import os
import re
import sys

# Expresiones regulares mejoradas
CLASS_REGEX = r"class (\w+)"
INTERFACE_REGEX = r"interface (\w+)"
ENUM_REGEX = r"enum (\w+)"
HERENCIA_REGEX = r"class (\w+) extends (\w+)"
IMPLEMENTACION_REGEX = r"class (\w+) implements ([\w, ]+)"
ATRIBUTO_REGEX = r"(private|public|protected)?\s*(static)?\s*(final)?\s*([\w<>\[\], ]+)\s+(\w+)\s*(?:=\s*[^;]+)?\s*;"
METODO_REGEX = r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*(public|protected|private)?\s*(static)?\s*(?:abstract\s+)?([\w<>\[\], ]+)\s+(\w+)\s*\(([^)]*)\)\s*(?:;|\{)"
CONSTRUCTOR_REGEX = r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*(public|protected|private)?\s*(\w+)\s*\(([^)]*)\)\s*\{"
DEPENDENCIA_REGEX = r"new (\w+)\s*\("
PARAMETRO_REGEX = r"([\w<>\[\], ]+)\s+(\w+)"

# Tipos especiales y palabras clave a excluir
TIPOS_ESPECIALES = {"LocalDateTime", "Date", "Optional", "List", "Set", "Map"}
PALABRAS_CLAVE_EXCLUIDAS = {"if", "else", "for", "while", "switch", "case", "super", "return", "break", "continue", "try", "catch", "finally"}

def es_palabra_clave_excluida(nombre):
    """Verifica si el nombre del método o constructor está en la lista de palabras clave excluidas."""
    return nombre.lower() in PALABRAS_CLAVE_EXCLUIDAS

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

    for contenido in archivos_java.values():
        clases_en_archivo = re.findall(CLASS_REGEX, contenido)
        interfaces_en_archivo = re.findall(INTERFACE_REGEX, contenido)
        enums_en_archivo = re.findall(ENUM_REGEX, contenido)

        clases_definidas.update(clases_en_archivo + interfaces_en_archivo + enums_en_archivo)

        herencias = re.findall(HERENCIA_REGEX, contenido)
        implementaciones = re.findall(IMPLEMENTACION_REGEX, contenido)

        for clase in clases_en_archivo + enums_en_archivo:
            if clase not in clases:
                clases[clase] = {"atributos": set(), "metodos": set()}

        for interfaz in interfaces_en_archivo:
            if interfaz not in clases:
                clases[interfaz] = {"atributos": set(), "metodos": set()}

        for clase, padre in herencias:
            relaciones_dict[f"{padre} <|-- {clase}"] = "Herencia"

        for clase, interfaces in implementaciones:
            for interfaz in interfaces.split(","):
                relaciones_dict[f"{interfaz.strip()} <|.. {clase}"] = "Implementación"

    return clases, relaciones_dict, clases_definidas

def extraer_atributos_metodos_dependencias(archivos_java, clases, clases_definidas, relaciones_dict):
    for contenido in archivos_java.values():
        for clase in clases.keys():
            match = re.search(rf"(class|enum) {clase}.*?\{{([\s\S]*?)\}}", contenido)
            if match:
                cuerpo_clase = match.group(2)

                atributos = re.findall(ATRIBUTO_REGEX, cuerpo_clase)
                metodos = re.findall(METODO_REGEX, contenido, re.MULTILINE)  # Buscar métodos en todo el contenido
                constructores = re.findall(CONSTRUCTOR_REGEX, contenido, re.MULTILINE)
                dependencias = re.findall(DEPENDENCIA_REGEX, cuerpo_clase)

                for atr in atributos:
                    visibilidad = atr[0] if atr[0] else "package-private"
                    tipo = atr[3].strip()
                    nombre = atr[4]

                    if nombre.lower() != "return":
                        clases[clase]["atributos"].add(f"{visibilidad} {tipo} {nombre}")

                        tipo_principal = re.sub(r"<.*?>", "", tipo).strip()
                        if tipo_principal in clases_definidas or tipo_principal in TIPOS_ESPECIALES:
                            key_composicion = f"{clase} --* {tipo_principal}"
                            key_agregacion = f"{clase} --o {tipo_principal}"

                            if key_agregacion in relaciones_dict:
                                relaciones_dict.pop(key_agregacion)
                                relaciones_dict[key_composicion] = "Composición"
                            elif key_composicion not in relaciones_dict:
                                if visibilidad == "private":
                                    relaciones_dict[key_composicion] = "Composición"
                                else:
                                    relaciones_dict[key_agregacion] = "Agregación"

                for met in metodos:
                    visibilidad = met[0] if met[0] else "package-private"
                    tipo_retorno = met[2].strip()
                    nombre = met[3]
                    parametros = met[4]

                    # Filtro adicional: Excluir palabras clave
                    if not es_palabra_clave_excluida(nombre):
                        clases[clase]["metodos"].add(f"{visibilidad} {tipo_retorno} {nombre}()")

                        tipo_principal = re.sub(r"<.*?>", "", tipo_retorno).strip()
                        if tipo_principal in clases_definidas or tipo_principal in TIPOS_ESPECIALES:
                            relaciones_dict[f"{clase} ..> {tipo_principal}"] = "Dependencia"

                        for param in re.findall(PARAMETRO_REGEX, parametros):
                            tipo_param = re.sub(r"<.*?>", "", param[0]).strip()
                            if tipo_param in clases_definidas or tipo_param in TIPOS_ESPECIALES:
                                relaciones_dict[f"{clase} ..> {tipo_param}"] = "Dependencia"

                for constr in constructores:
                    visibilidad = constr[0] if constr[0] else "package-private"
                    nombre = constr[1]
                    parametros = constr[2]

                    # Filtro adicional: Excluir palabras clave
                    if not es_palabra_clave_excluida(nombre):
                        clases[clase]["metodos"].add(f"{visibilidad} {nombre}()")

                for dependencia in dependencias:
                    if dependencia in clases_definidas:
                        relaciones_dict[f"{clase} ..> {dependencia}"] = "Dependencia"

def generar_mermaid(clases, relaciones_dict, bQuitarRelDependencia=False):
    mermaid = "classDiagram\n"

    for clase, detalles in clases.items():
        mermaid += f"    class {clase} {{\n"

        for atributo in sorted(detalles["atributos"]):
            mermaid += f"        {atributo}\n"

        for metodo in sorted(detalles["metodos"]):
            mermaid += f"        {metodo}\n"

        mermaid += f"    }}\n"

    for relacion, tipo in relaciones_dict.items():
        if bQuitarRelDependencia:
            if tipo != 'Dependencia':
                mermaid += f"    {relacion} : {tipo}\n"
        else:
            mermaid += f"    {relacion} : {tipo}\n"

    mermaid += """
    %% === Leyenda ===
    class Leyenda {
        "A <|-- B : Herencia"
        "A <|.. B : Implementación"
        "A --o B : Agregación"
        "A --* B : Composición"
        "A ..> B : Dependencia"
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

inputPath = "./miaparcamiento"
outputPath = "diagrama"

if len(sys.argv) == 3:
    inputPath = sys.argv[1]
    outputPath = sys.argv[2]

directorio = inputPath
validar_directorio(directorio)
outputPath = validar_nombre_archivo(outputPath)

archivos_java = leer_archivos_java(directorio)
clases, relaciones_dict, clases_definidas = extraer_clases_y_relaciones(archivos_java)
extraer_atributos_metodos_dependencias(archivos_java, clases, clases_definidas, relaciones_dict)
mermaid_script = generar_mermaid(clases, relaciones_dict, bQuitarRelDependencia=False)

with open(outputPath, "w", encoding="utf-8") as f:
    f.write(mermaid_script)

print(f"✅ Diagrama generado en {outputPath}. ¡Ábrelo en Mermaid Live Editor o VS Code!")