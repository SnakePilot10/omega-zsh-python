#!/usr/bin/env python3
import os
import subprocess
import sys
import glob
import shutil  # <-- Nueva librería para detectar ejecutables correctamente

# Configuración
TEXTO_MUESTRA = "Termux Ninja"

def verificar_dependencia():
    """
    Verifica si figlet está instalado usando shutil.which.
    Esto es más seguro y compatible que llamar a 'which' vía subprocess.
    """
    if shutil.which("figlet") is None:
        print("❌ Error crítico: 'figlet' no está instalado o no se encuentra en el PATH.")
        sys.exit(1)

def obtener_fuentes(directorio_fuentes):
    """
    Busca archivos .flf en el directorio especificado.
    Retorna una lista ordenada de nombres de fuentes (sin extensión).
    """
    if not os.path.exists(directorio_fuentes):
        print(f"⚠️  Advertencia: No se encontró el directorio {directorio_fuentes}")
        return []
    
    patron = os.path.join(directorio_fuentes, "*.flf")
    archivos = glob.glob(patron)
    
    # Extraemos solo el nombre del archivo sin la extensión .flf
    fuentes = [os.path.splitext(os.path.basename(f))[0] for f in archivos]
    return sorted(fuentes)

def renderizar_texto(texto, fuente):
    """Ejecuta figlet con la fuente específica y retorna el resultado."""
    try:
        # Ejecutamos figlet directamente
        resultado = subprocess.run(
            ["figlet", "-f", fuente, texto],
            capture_output=True,
            text=True,
            check=True
        )
        return resultado.stdout
    except subprocess.CalledProcessError:
        return "Error al renderizar fuente."
    except FileNotFoundError:
        return "Error: Ejecutable figlet no encontrado al intentar renderizar."

def main():
    # 1. Verificación del entorno
    verificar_dependencia()
    
    # Detectar prefijo de Termux dinámicamente
    prefix = os.environ.get("PREFIX", "/usr")
    dir_fuentes = os.path.join(prefix, "share", "figlet")
    
    print(f"🔍 Buscando fuentes en: {dir_fuentes}")
    fuentes_disponibles = obtener_fuentes(dir_fuentes)
    
    if not fuentes_disponibles:
        print("❌ No se encontraron fuentes .flf instaladas.")
        return

    print(f"✅ Se encontraron {len(fuentes_disponibles)} fuentes.")
    print("=" * 50)

    # 2. Bucle principal de renderizado
    for fuente in fuentes_disponibles:
        print(f"\n🏷️  ESTILO: {fuente.upper()}")
        print("-" * 30)
        banner = renderizar_texto(TEXTO_MUESTRA, fuente)
        print(banner)

if __name__ == "__main__":
    main()

