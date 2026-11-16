"""Capa de servicios: exporta la tabla de pólizas a un Excel."""

from __future__ import annotations

import io

import pandas as pd
from openpyxl.styles import Font, PatternFill

# Colores del encabezado (los mismos de la app).
ROJO = "AE1800"
BLANCO = "FFFFFF"

# Diccionario: nombre de la columna en el Excel -> nombre del campo en el diccionario.
COLUMNAS = {
    "Póliza": "numero",
    "Asegurado": "nombre",
    "Cédula": "cedula",
    "Correo": "correo",
    "Aseguradora": "aseguradora",
    "Ramo": "ramo",
    "Vence": "hasta",
    "Días para vencer": "dias_para_vencer",
    "Prima anual (CRC)": "prima",
    "Estado": "estado",
    "Forma de pago": "pago",
    "Asesor": "asesor",
}


def _fecha_texto(fecha) -> str:
    """Devuelve la fecha como dd/mm/aaaa, o vacío si no hay."""
    if fecha is None:
        return ""
    return fecha.strftime("%d/%m/%Y")


def exportar_excel(resultados: list[dict]) -> bytes:
    """Arma un Excel con la tabla de pólizas y lo devuelve en bytes."""
    # Lista de diccionarios: una fila por póliza.
    filas: list[dict] = []

    # Bucle: convertimos cada póliza en una fila con nombres de columna en español.
    for poliza in resultados:
        fila = {}

        for encabezado, campo in COLUMNAS.items():
            valor = poliza.get(campo)

            # Condicional: la fecha se muestra como texto dd/mm/aaaa.
            if campo == "hasta":
                valor = _fecha_texto(valor)
            # Condicional: los vacíos se dejan en blanco en el Excel.
            elif valor is None:
                valor = ""

            fila[encabezado] = valor

        filas.append(fila)

    # DataFrame con el orden de columnas que definimos arriba.
    tabla = pd.DataFrame(filas, columns=list(COLUMNAS.keys()))

    # Buffer en memoria: el archivo no se guarda en disco.
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as escritor:
        tabla.to_excel(escritor, index=False, sheet_name="Polizas")

        hoja = escritor.sheets["Polizas"]

        # Encabezado con fondo rojo y letra blanca.
        for celda in hoja[1]:
            celda.font = Font(bold=True, color=BLANCO)
            celda.fill = PatternFill("solid", fgColor=ROJO)

        # Ancho de cada columna, calculado con el texto más largo.
        for indice, encabezado in enumerate(tabla.columns, start=1):
            letra = hoja.cell(row=1, column=indice).column_letter
            contenido = [str(valor) for valor in tabla[encabezado].tolist()]
            largo = max([len(encabezado)] + [len(texto) for texto in contenido])
            hoja.column_dimensions[letra].width = min(largo + 2, 40)

        # Fila de encabezado fija al hacer scroll.
        hoja.freeze_panes = "A2"

    return buffer.getvalue()
