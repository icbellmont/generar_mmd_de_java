import os
import re
import sys

# Expresiones regulares
CLASS_REGEX = r"class (\w+)"
INTERFACE_REGEX = r"interface (\w+)"
HERENCIA_REGEX = r"class (\w+) extends (\w+)"
IMPLEMENTACION_REGEX = r"class (\w+) implements ([\w, ]+)"
ATRIBUTO_REGEX = r"(private|public|protected)?\s*(static)?\s*(final)?\s*(?:List<(\w+)>|(\w+))\s+(\w+)\s*;"
METODO_REGEX = r"(private|public|protected)?\s*(static)?\s*(\w+)\s+(\w+)\s*\(([^)]*)\)\s*\{"
DEPENDENCIA_REGEX = r"new (\w+)\s*\("
PARAMETRO_REGEX = r"(\w+)\s+(\w+)"

def leer_archivos_java(directorio):
    archivos_java = {}
    for archivo in os.listdir(directorio):
        if archivo.endswith(".java"):
            with open(os.path.join(directorio, archivo), "r", encoding="utf-8") as f:
                archivos_java[archivo] = f.read()
    return archivos_java


def extraer_clases_y_relaciones(archivos_java):
    clases = {}
    relaciones_dict = {}  # Diccionario para filtrar relaciones redundantes
    clases_definidas = set()

    for contenido in archivos_java.values():
        clases_en_archivo = re.findall(CLASS_REGEX, contenido)
        interfaces_en_archivo = re.findall(INTERFACE_REGEX, contenido)

        clases_definidas.update(clases_en_archivo + interfaces_en_archivo)

        herencias = re.findall(HERENCIA_REGEX, contenido)
        implementaciones = re.findall(IMPLEMENTACION_REGEX, contenido)

        for clase in clases_en_archivo:
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
            match = re.search(rf"class {clase}.*?\{{([\s\S]*?)\}}", contenido)
            if match:
                cuerpo_clase = match.group(1)

                atributos = re.findall(ATRIBUTO_REGEX, cuerpo_clase)
                metodos = re.findall(METODO_REGEX, cuerpo_clase)
                dependencias = re.findall(DEPENDENCIA_REGEX, cuerpo_clase)

                for atr in atributos:
                    visibilidad = atr[0] if atr[0] else "package-private"
                    tipo = atr[3] if atr[3] else atr[4]  # `List<Tipo>` o `Tipo`
                    nombre = atr[5]

                    if nombre.lower() != "return":
                        clases[clase]["atributos"].add(f"{visibilidad} {tipo} {nombre}")

                        if tipo in clases_definidas:
                            key_composicion = f"{clase} --* {tipo}"
                            key_agregacion = f"{clase} --o {tipo}"

                            # Si ya existe una relación de agregación, se reemplaza por composición
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
                    tipo_retorno = met[2]
                    nombre = met[3]
                    parametros = met[4]
                    clases[clase]["metodos"].add(f"{visibilidad} {tipo_retorno} {nombre}()")

                    if tipo_retorno in clases_definidas:
                        relaciones_dict[f"{clase} ..> {tipo_retorno}"] = "Dependencia"

                    for param in re.findall(PARAMETRO_REGEX, parametros):
                        tipo_param = param[0]
                        if tipo_param in clases_definidas:
                            relaciones_dict[f"{clase} ..> {tipo_param}"] = "Dependencia"

                for dependencia in dependencias:
                    if dependencia in clases_definidas:
                        relaciones_dict[f"{clase} ..> {dependencia}"] = "Dependencia"
                        

def generar_mermaid(clases, relaciones_dict, bQuitarRelDependencia = False):
    """
    Genera el código Mermaid para representar el diagrama de clases.
    https://mermaid.js.org/syntax/classDiagram.html
    """
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
            if tipo not in ('Dependencia'):
                mermaid += f"    {relacion} : {tipo}\n"
        else:
            mermaid += f"    {relacion} : {tipo}\n"
        
    # Leyenda con explicaciones ampliadas
    mermaid += """
    %% === Leyenda ===
    class Leyenda {
        "A <|-- B : Herencia (Una clase hereda atributos y métodos de otra)"
        "A <|.. B : Implementación (Una clase implementa una interfaz)"
        "A --o B : Agregación (Una clase contiene instancias de otra, pero no es dueña)"
        "A --* B : Composición (Una clase contiene otra y es dueña de ella)"
        "A ..> B : Dependencia (Una clase usa otra como parámetro o retorno)"
    }
    """

    return mermaid


def validar_directorio(directorio):
    """
    Valida si el directorio proporcionado existe y es un directorio válido.
    """
    if not os.path.exists(directorio):
        print(f"❌ Error: El directorio '{directorio}' no existe.")
        sys.exit(1)  # Salir con código de error 1

    if not os.path.isdir(directorio):
        print(f"❌ Error: '{directorio}' no es un directorio.")
        sys.exit(1)
        
        
def validar_nombre_archivo(nombre_archivo):
    """
    Valida si el nombre de archivo proporcionado es válido.
    """
    if not nombre_archivo:
        print("❌ Error: El nombre de archivo no puede estar vacío.")
        sys.exit(1)
        
    # Verifica si el nombre de archivo tiene una extensión
    if '.' not in nombre_archivo:
        nombre_archivo += '.mmd'  # Agrega la extensión .mmd

    # Verifica si el nombre de archivo contiene caracteres no permitidos
    caracteres_no_permitidos = r'[<>:"/\\|?*]'
    if any(c in caracteres_no_permitidos for c in nombre_archivo):
        print("❌ Error: El nombre de archivo contiene caracteres no permitidos.")
        sys.exit(1)

    # Verifica si el nombre de archivo es demasiado largo
    if len(nombre_archivo) > 255: # Máximo común en muchos sistemas
        print("❌ Error: El nombre de archivo es demasiado largo.")
        sys.exit(1)
        
    return nombre_archivo  # Devuelve el nombre de archivo modificado
        

# 📌 Carpeta donde están los archivos .java
directorio = "./gestionacademia"
inputPath = "input_directory"
outputPath = "output_filename.mmd"
if(len(sys.argv) != 3):
    print("❌ Not sufficient amount of arguments. ℹ️  Uso: python script.py <directorio> <nombre_archivo>")
    # sys.exit(1)
else:
    inputPath = sys.argv[1]
    outputPath = sys.argv[2]

directorio = inputPath
validar_directorio(directorio)
outputPath = validar_nombre_archivo(sys.argv[2])

archivos_java = leer_archivos_java(directorio)

clases, relaciones_dict, clases_definidas = extraer_clases_y_relaciones(archivos_java)

extraer_atributos_metodos_dependencias(archivos_java, clases, clases_definidas, relaciones_dict)

# mermaid_script = generar_mermaid(clases, relaciones_dict)
mermaid_script = generar_mermaid(clases, relaciones_dict, bQuitarRelDependencia=True)

# with open("diagrama.mmd", "w", encoding="utf-8") as f:
with open(outputPath, "w", encoding="utf-8") as f:
    f.write(mermaid_script)

print(f"✅ Diagrama generado en {outputPath}. ¡Ábrelo en Mermaid Live Editor o VS Code!")
