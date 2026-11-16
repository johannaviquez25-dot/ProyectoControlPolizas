"""Capa de datos: es el único lugar que abre archivos."""

from __future__ import annotations

import io
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pdfplumber

# ---------------------------------------------------------------------------
# Rutas base
# ---------------------------------------------------------------------------
# Path(__file__) apunta a models/datos.py.
# .parent es models/ y .parent.parent es la raíz del proyecto.
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
CARPETA_DATA = RAIZ_PROYECTO / "data"
RUTA_CLIENTES = CARPETA_DATA / "Maestro_Clientes.xlsx"
CARPETA_POLIZAS = CARPETA_DATA / "polizas"

# ---------------------------------------------------------------------------
# Carpeta de archivos importados por el usuario
# ---------------------------------------------------------------------------
# data/ es la bodega original y NO se toca. Lo que se importa desde la página
# se guarda aquí, en una carpeta aparte que sí se puede escribir.
CARPETA_USUARIO = RAIZ_PROYECTO / "datos_usuario"
RUTA_CLIENTES_USUARIO = CARPETA_USUARIO / "Maestro_Clientes.xlsx"
CARPETA_POLIZAS_USUARIO = CARPETA_USUARIO / "polizas"

# Lista de columnas que debe tener el Excel de clientes.
COLUMNAS_CLIENTES = ["Cedula", "Nombre_Completo", "Correo", "Telefono", "Asesor"]

# Diccionario: etiqueta que aparece en el PDF -> nombre del campo en el diccionario.
CAMPOS = {
    "Numero de poliza": "numero",
    "Ramo": "ramo",
    "Tomador / Asegurado": "nombre",
    "Cedula": "cedula",
    "Vigencia desde": "desde",
    "Vigencia hasta": "hasta",
    "Prima anual": "prima",
    "Forma de pago": "pago",
    "Suma asegurada": "suma",
    "Asesor": "asesor",
}

# Conjuntos para saber qué campos hay que convertir.
CAMPOS_FECHA = {"desde", "hasta"}
CAMPOS_MONTO = {"prima", "suma"}


def _convertir_fecha(texto: str) -> date | None:
    """Convierte un texto dd/mm/aaaa a date. Si está vacío o mal, devuelve None."""
    texto = texto.strip()

    # Condicional: si no hay texto, no hay fecha.
    if not texto:
        return None

    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        # Si la fecha está incompleta o mal escrita, devolvemos None.
        return None


def _convertir_monto(texto: str) -> float | None:
    """Convierte 'CRC 228,000.00' a 228000.0. Si está vacío, devuelve None."""
    # Quitamos la moneda, las comas y los espacios.
    texto = texto.replace("CRC", "").replace(",", "").strip()

    # Condicional: si no hay texto, no hay monto.
    if not texto:
        return None

    try:
        return float(texto)
    except ValueError:
        return None


def _leer_clientes(ruta: Path) -> pd.DataFrame:
    """Lee una hoja 'Clientes' desde un Excel y deja la cédula como texto limpio."""
    # dtype={"Cedula": str}: obliga a pandas a leer la cédula como texto,
    # no como número.
    clientes = pd.read_excel(
        ruta,
        sheet_name="Clientes",
        dtype={"Cedula": str},
    )

    # .astype(str): convierte la columna completa a texto.
    # .str.strip(): quita espacios al inicio y al final de cada cédula.
    clientes["Cedula"] = clientes["Cedula"].astype(str).str.strip()

    return clientes


def cargar_clientes() -> pd.DataFrame:
    """Devuelve los clientes. Si el usuario importó un maestro, ese manda."""
    # Condicional: si existe el Excel importado, lo usamos; si no, el original.
    if RUTA_CLIENTES_USUARIO.exists():
        return _leer_clientes(RUTA_CLIENTES_USUARIO)

    return _leer_clientes(RUTA_CLIENTES)


def leer_poliza(ruta_pdf: str | Path) -> dict:
    """Lee un PDF y devuelve un diccionario con sus datos."""
    ruta_pdf = Path(ruta_pdf)

    # Diccionario con todas las claves vacías.
    # Así todas las pólizas devuelven exactamente las mismas claves.
    poliza = {
        "archivo": ruta_pdf.name,
        "aseguradora": None,
        "numero": None,
        "ramo": None,
        "nombre": None,
        "cedula": None,
        "desde": None,
        "hasta": None,
        "prima": None,
        "pago": None,
        "suma": None,
        "asesor": None,
    }

    with pdfplumber.open(ruta_pdf) as pdf:
        # Texto de la primera página. Si no hay texto, usamos una cadena vacía.
        texto = pdf.pages[0].extract_text() or ""

    # Lista de líneas del PDF.
    lineas = texto.splitlines()

    # La primera línea es el nombre de la aseguradora.
    if lineas:
        poliza["aseguradora"] = lineas[0].strip()

    # Bucle: recorremos las líneas después de la primera.
    for linea in lineas[1:]:
        # Condicional: solo nos interesan las líneas con "Etiqueta: valor".
        if ":" not in linea:
            continue

        # split(":", 1) corta solo en el primer ":".
        etiqueta, valor = linea.split(":", 1)
        etiqueta = etiqueta.strip()
        valor = valor.strip()

        # Si la etiqueta no está en el diccionario CAMPOS, se ignora.
        if etiqueta not in CAMPOS:
            continue

        # Nombre del campo que usaremos en el diccionario.
        campo = CAMPOS[etiqueta]

        # Conversión según el tipo de dato.
        if campo in CAMPOS_FECHA:
            poliza[campo] = _convertir_fecha(valor)
        elif campo in CAMPOS_MONTO:
            poliza[campo] = _convertir_monto(valor)
        else:
            poliza[campo] = valor

    return poliza


def cargar_polizas() -> list[dict]:
    """Devuelve todas las pólizas: las del repositorio más las importadas."""
    # Base: los PDFs que vienen en data/polizas, en orden alfabético.
    polizas = [leer_poliza(ruta) for ruta in sorted(CARPETA_POLIZAS.glob("*.pdf"))]

    # Condicional: si el usuario importó PDFs, también se leen.
    if CARPETA_POLIZAS_USUARIO.exists():
        subidas = [
            leer_poliza(ruta)
            for ruta in sorted(CARPETA_POLIZAS_USUARIO.glob("*.pdf"))
        ]

        # Diccionario: número de póliza -> póliza.
        # Si una póliza subida tiene el mismo número que una del repositorio,
        # la subida reemplaza a la original (queda la última que se guarda).
        por_numero: dict[str, dict] = {}
        sin_numero: list[dict] = []

        for poliza in polizas + subidas:
            if poliza["numero"]:
                por_numero[poliza["numero"]] = poliza
            else:
                sin_numero.append(poliza)

        polizas = list(por_numero.values()) + sin_numero

        # Orden final por número (las que no tienen número van al final).
        polizas.sort(key=lambda p: (p["numero"] is None, p["numero"] or ""))

    return polizas


def guardar_clientes(contenido: bytes) -> dict:
    """Valida un Excel de clientes y lo guarda. Devuelve un resumen."""
    # Condicional: intentamos leer la hoja "Clientes" del archivo subido.
    try:
        datos = pd.read_excel(
            io.BytesIO(contenido),
            sheet_name="Clientes",
            dtype={"Cedula": str},
        )
    except ValueError:
        # pandas lanza ValueError cuando la hoja no existe.
        return {
            "ok": False,
            "mensaje": "El Excel no tiene una hoja llamada 'Clientes'.",
        }
    except Exception:
        return {
            "ok": False,
            "mensaje": "No se pudo leer el Excel. Revisá que sea un .xlsx válido.",
        }

    # Lista de columnas que faltan.
    faltantes = [columna for columna in COLUMNAS_CLIENTES if columna not in datos.columns]

    if faltantes:
        return {
            "ok": False,
            "mensaje": "Faltan columnas en el Excel: " + ", ".join(faltantes) + ".",
        }

    # Condicional: el Excel tiene que traer al menos un cliente.
    if len(datos) == 0:
        return {"ok": False, "mensaje": "El Excel no tiene filas de clientes."}

    # Columna de cédulas como texto, conservando los vacíos.
    cedulas = datos["Cedula"].astype("string").str.strip()

    if cedulas.isna().any() or (cedulas == "").any():
        return {
            "ok": False,
            "mensaje": "Hay clientes sin cédula. Completá esa columna.",
        }

    if cedulas.duplicated().any():
        return {
            "ok": False,
            "mensaje": "Hay cédulas repetidas en el Excel. Cada cliente debe tener la suya.",
        }

    # Creamos la carpeta y guardamos el archivo tal cual lo subió el usuario.
    CARPETA_USUARIO.mkdir(parents=True, exist_ok=True)
    RUTA_CLIENTES_USUARIO.write_bytes(contenido)

    return {
        "ok": True,
        "mensaje": f"Maestro importado: {len(datos)} clientes.",
    }


def guardar_polizas(archivos: list[tuple[str, bytes]]) -> dict:
    """Valida y guarda los PDFs subidos. Devuelve un resumen."""
    # Listas para separar lo que sirve de lo que no.
    guardadas: list[str] = []
    rechazadas: list[str] = []

    # Creamos la carpeta de pólizas importadas.
    CARPETA_POLIZAS_USUARIO.mkdir(parents=True, exist_ok=True)

    # Bucle: recorremos cada archivo recibido como (nombre, contenido).
    for nombre, contenido in archivos:
        # Path(nombre).name quita cualquier ruta que venga en el nombre.
        nombre_limpio = Path(nombre).name

        # Condicional: solo aceptamos PDFs.
        if not nombre_limpio.lower().endswith(".pdf"):
            rechazadas.append(f"{nombre_limpio}: no es un PDF.")
            continue

        destino = CARPETA_POLIZAS_USUARIO / nombre_limpio
        destino.write_bytes(contenido)

        # Condicional: comprobamos que el PDF se pueda leer.
        try:
            poliza = leer_poliza(destino)
        except Exception:
            destino.unlink(missing_ok=True)
            rechazadas.append(f"{nombre_limpio}: está dañado o no se pudo leer.")
            continue

        # Condicional: debe tener número de póliza para servir.
        if not poliza["numero"]:
            destino.unlink(missing_ok=True)
            rechazadas.append(f"{nombre_limpio}: no tiene 'Numero de poliza'.")
            continue

        guardadas.append(poliza["numero"])

    # Armamos el mensaje según lo que pasó.
    partes: list[str] = []

    if guardadas:
        partes.append(f"Pólizas importadas: {len(guardadas)}.")

    if rechazadas:
        partes.append("Rechazadas: " + " ".join(rechazadas))

    if not partes:
        return {"ok": False, "mensaje": "No se recibió ningún PDF."}

    return {"ok": bool(guardadas), "mensaje": " ".join(partes)}
