"""Capa de datos: es el único lugar que abre archivos."""

from __future__ import annotations

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


def cargar_clientes() -> pd.DataFrame:
    """Lee la hoja 'Clientes' y devuelve un DataFrame con la cédula como texto."""
    # dtype={"Cedula": str}: obliga a pandas a leer la cédula como texto,
    # no como número.
    clientes = pd.read_excel(
        RUTA_CLIENTES,
        sheet_name="Clientes",
        dtype={"Cedula": str},
    )

    # .astype(str): convierte la columna completa a texto.
    # .str.strip(): quita espacios al inicio y al final de cada cédula.
    clientes["Cedula"] = clientes["Cedula"].astype(str).str.strip()

    return clientes


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
    """Recorre data/polizas en orden alfabético y devuelve una lista de diccionarios."""
    # sorted() ordena las rutas alfabéticamente.
    rutas = sorted(CARPETA_POLIZAS.glob("*.pdf"))

    # Lista por comprensión: lee cada PDF y guarda su diccionario.
    return [leer_poliza(ruta) for ruta in rutas]
