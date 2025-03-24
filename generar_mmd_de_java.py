import os
import re
import sys
from collections import OrderedDict
from icecream import ic as icdebug

# Expresiones regulares mejoradas
CLASS_REGEX = r"class (\w+)"
INTERFACE_REGEX = r"interface (\w+)"
ENUM_REGEX = r"enum\s+(\w+)\s*\{(.*?)\}"
ENUM_VALUES_REGEX = r"([A-Z_][\w]*)(?:\([^)]*\))?"
HERENCIA_REGEX = r"class (\w+) extends (\w+)"
IMPLEMENTACION_REGEX = r"class (\w+) implements ([\w, ]+)"
ATRIBUTO_REGEX = r"(private|public|protected)?\s*(static)?\s*(final)?\s*([\w<>\[\], ]+)\s+(\w+)\s*(?:=\s*[^;]+)?\s*;"
METODO_REGEX = r"(?:@\w+(?:\([^)]*\))?\s*)*(public|protected|private)?\s*(static)?\s*(?:abstract\s+)?([\w<>\[\], ]+)\s+(\w+)\s*\(([^)]*)\)\s*(?:;|\{)"
CONSTRUCTOR_REGEX = r"(?:@\w+(?:\([^)]*\))?\s*)*(public|protected|private)?\s*(\w+)\s*\(([^)]*)\)\s*\{"
DEPENDENCIA_REGEX = r"new (\w+)\s*\("
PARAMETRO_REGEX = r"([\w<>\[\], ]+)\s+(\w+)"

TIPOS_ESPECIALES = {"LocalDateTime", "Date", "Optional", "List", "Set", "Map"}
PALABRAS_CLAVE_EXCLUIDAS = {"if", "else", "for", "while", "switch", "case", "super", "return", "break", "continue", "try", "catch", "finally"}

def es_palabra_clave_excluida(nombre):
    return nombre.lower() in PALABRAS_CLAVE_EXCLUIDAS

def limpiar_tipo(tipo):
    return re.sub(r"<.*?>", "", tipo).strip()

def es_tipo_valido(tipo, clases_definidas):
    tipo_limpio = limpiar_tipo(tipo)
    return tipo_limpio in clases_definidas or tipo_limpio in TIPOS_ESPECIALES

def determinar_relacion(clase_origen, clase_destino, visibilidad):
    if visibilidad == "private":
        return "Composición"
    return "Agregación"

def leer_archivos_java(directorio):
    archivos_java = {}
    for archivo in os.listdir(directorio):
        if archivo.endswith(".java"):
            with open(os.path.join(directorio, archivo), "r", encoding="utf-8") as f:
                archivos_java[archivo] = f.read()
    return archivos_java

def extraer_clases_y_relaciones(archivos_java):
    clases = {}
    relaciones_dict = {}
    clases_definidas = set()

    for nombre_archivo, contenido in archivos_java.items():
        clases_en_archivo = re.findall(CLASS_REGEX, contenido)
        clases_definidas.update(clases_en_archivo)

        for clase in clases_en_archivo:
            if clase not in clases:
                clases[clase] = {
                    "atributos": set(),
                    "metodos": OrderedDict(),  # Usamos OrderedDict para métodos
                    "enums": {}
                }

        for enum_match in re.finditer(ENUM_REGEX, contenido, re.DOTALL):
            enum_nombre = enum_match.group(1)
            enum_contenido = enum_match.group(2)
            
            clase_contenedora = None
            for clase in clases_en_archivo:
                clase_start = contenido.find(f"class {clase}")
                if clase_start == -1:
                    continue
                
                clase_end = contenido.find('}', clase_start)
                enum_pos = enum_match.start()
                
                if clase_start < enum_pos < clase_end:
                    clase_contenedora = clase
                    break

            valores_enum = re.findall(ENUM_VALUES_REGEX, enum_contenido)
            
            if clase_contenedora:
                clases[clase_contenedora]["enums"][enum_nombre] = valores_enum
            else:
                clases[enum_nombre] = {
                    "atributos": set(),
                    "metodos": OrderedDict(),
                    "enums": {},
                    "es_enum": True
                }

        herencias = re.findall(HERENCIA_REGEX, contenido)
        implementaciones = re.findall(IMPLEMENTACION_REGEX, contenido)

        for clase, padre in herencias:
            relaciones_dict[f"{padre} <|-- {clase}"] = "Herencia"

        for clase, interfaces in implementaciones:
            for interfaz in interfaces.split(","):
                relaciones_dict[f"{interfaz.strip()} <|.. {clase}"] = "Implementación"

    return clases, relaciones_dict, clases_definidas

def extraer_atributos_metodos_dependencias(archivos_java, clases, clases_definidas, relaciones_dict):
    for contenido in archivos_java.values():
        for clase, detalles in clases.items():
            if detalles.get("es_enum"):
                continue
                
            match = re.search(rf"(class|enum) {clase}.*?\{{([\s\S]*?)\}}", contenido)
            if match:
                cuerpo_clase = match.group(2)

                # Procesar atributos
                for atr in re.findall(ATRIBUTO_REGEX, cuerpo_clase):
                    visibilidad = atr[0] if atr[0] else "package-private"
                    tipo = atr[3]
                    nombre = atr[4]

                    if not es_palabra_clave_excluida(nombre):
                        detalles["atributos"].add(f"{visibilidad} {tipo} {nombre}")

                        tipo_principal = limpiar_tipo(tipo)
                        if es_tipo_valido(tipo, clases_definidas):
                            relacion = determinar_relacion(clase, tipo_principal, visibilidad)
                            
                            key_dependencia = f"{clase} ..> {tipo_principal}"
                            if key_dependencia in relaciones_dict:
                                relaciones_dict.pop(key_dependencia)
                            
                            key_relacion = f"{clase} --{'*' if relacion == 'Composición' else 'o'} {tipo_principal}"
                            relaciones_dict[key_relacion] = relacion

                # Procesar métodos (evitando duplicados)
                for met in re.findall(METODO_REGEX, contenido, re.MULTILINE):
                    visibilidad = met[0] if met[0] else "package-private"
                    tipo_retorno = met[2]
                    nombre = met[3]
                    parametros = met[4]

                    if not es_palabra_clave_excluida(nombre):
                        # Crear firma única sin parámetros para visualización
                        firma_visual = f"{visibilidad} {tipo_retorno} {nombre}()"
                        firma_visual = f"{visibilidad} {nombre}()"  # Mejor esta firma para evitar duplicados!!
                        # Guardar información completa para análisis
                        detalles["metodos"][firma_visual] = {
                            "tipo_retorno": tipo_retorno,
                            "parametros": parametros
                        }

                        tipo_principal = limpiar_tipo(tipo_retorno)
                        if (es_tipo_valido(tipo_principal, clases_definidas) and 
                            not any(f"{clase} --{x} {tipo_principal}" in relaciones_dict for x in ["*", "o"])):
                            relaciones_dict[f"{clase} ..> {tipo_principal}"] = "Dependencia"

                        for param in re.findall(PARAMETRO_REGEX, parametros):
                            tipo_param = limpiar_tipo(param[0])
                            if (es_tipo_valido(tipo_param, clases_definidas) and 
                                not any(f"{clase} --{x} {tipo_param}" in relaciones_dict for x in ["*", "o"])):
                                relaciones_dict[f"{clase} ..> {tipo_param}"] = "Dependencia"

                # Procesar constructores (evitando duplicados)
                for constr in re.findall(CONSTRUCTOR_REGEX, contenido, re.MULTILINE):
                    visibilidad = constr[0] if constr[0] else "package-private"
                    nombre = constr[1]
                    parametros = constr[2]

                    if not es_palabra_clave_excluida(nombre):
                        firma_visual = f"{visibilidad} {nombre}()"
                        detalles["metodos"][firma_visual] = {
                            "parametros": parametros,
                            "es_constructor": True
                        }

                # Procesar dependencias
                for dependencia in re.findall(DEPENDENCIA_REGEX, cuerpo_clase):
                    if (es_tipo_valido(dependencia, clases_definidas) and 
                        not any(f"{clase} --{x} {dependencia}" in relaciones_dict for x in ["*", "o"])):
                        relaciones_dict[f"{clase} ..> {dependencia}"] = "Dependencia"

def generar_mermaid(clases, relaciones_dict, bQuitarRelDependencia=False):
    mermaid = "classDiagram\n"
    
    for clase, detalles in clases.items():
        mermaid += f"    class {clase} {{\n"
        
        # Mostrar enums
        for enum_nombre, valores in detalles.get("enums", {}).items():
            mermaid += f"        <<enum>> {enum_nombre}\n"
            for valor in valores:
                mermaid += f"        {valor}\n"
        
        # Atributos
        for atributo in sorted(detalles["atributos"]):
            mermaid += f"        {atributo}\n"
        
        # Métodos (usando las firmas visuales sin duplicados)
        for metodo in detalles["metodos"]:
            mermaid += f"        {metodo}\n"
        
        mermaid += "    }\n"
    
    # Relaciones
    relaciones_mostradas = set()
    for relacion, tipo in relaciones_dict.items():
        if not bQuitarRelDependencia or tipo != 'Dependencia':
            partes = relacion.split()
            clave_relacion = (partes[0], partes[-1])
            if clave_relacion not in relaciones_mostradas:
                mermaid += f"    {relacion} : {tipo}\n"
                relaciones_mostradas.add(clave_relacion)
    
    # Leyenda mejorada
    mermaid += """
    %% === Leyenda ===
    class Leyenda {
        "A <|-- B : Herencia"
        "A <|.. B : Implementación"
        "A --* B : Composición (todo-parte, vida dependiente)"
        "A --o B : Agregación (todo-parte, vida independiente)"
        "A ..> B : Dependencia (uso temporal)"
        "<<enum>> : Enumeración"
    }
    """
    
    return mermaid

def validar_directorio(directorio):
    if not os.path.exists(directorio):
        print(f"❌ Error: El directorio '{directorio}' no existe.")
        sys.exit(1)
    if not os.path.isdir(directorio):
        print(f"❌ Error: '{directorio}' no es un directorio.")
        sys.exit(1)

def validar_nombre_archivo(nombre_archivo):
    if not nombre_archivo:
        print("❌ Error: El nombre de archivo no puede estar vacío.")
        sys.exit(1)
    if '.' not in nombre_archivo:
        nombre_archivo += '.mmd'
    return nombre_archivo

if __name__ == "__main__":
    icdebug.configureOutput(includeContext=True)
    inputPath = "./miaparcamiento"
    outputPath = "diagrama.mmd"

    if len(sys.argv) == 3:
        inputPath = sys.argv[1]
        outputPath = sys.argv[2]

    validar_directorio(inputPath)
    outputPath = validar_nombre_archivo(outputPath)

    archivos_java = leer_archivos_java(inputPath)
    clases, relaciones_dict, clases_definidas = extraer_clases_y_relaciones(archivos_java)
    extraer_atributos_metodos_dependencias(archivos_java, clases, clases_definidas, relaciones_dict)
    # icdebug(clases_definidas)
    # icdebug(clases['Vehiculo'])
    mermaid_script = generar_mermaid(clases, relaciones_dict)

    with open(outputPath, "w", encoding="utf-8") as f:
        f.write(mermaid_script)

    print(f"✅ Diagrama generado en {outputPath}")