"""Capa de controladores: rutas de Flask para las pólizas."""

from __future__ import annotations

import io
import zipfile

from flask import Blueprint, abort, render_template, request, send_file

from models.polizas import (
    FECHA_CORTE,
    buscar_inconsistencias,
    buscar_por_numero,
    calcular_resultados,
    contar_por_estado,
    primas_por_aseguradora,
)
from services.generador_aviso import crear_aviso_pdf

# Blueprint: agrupa las rutas de este controlador.
bp = Blueprint("polizas", __name__)


@bp.route("/")
def inicio():
    """Muestra el tablero con los resultados de las pólizas."""
    # El controlador no calcula: pide los datos al modelo.
    resultados = calcular_resultados()
    conteo = contar_por_estado(resultados)
    primas = primas_por_aseguradora(resultados)
    inconsistencias = buscar_inconsistencias(resultados)

    # Enviamos todo a la plantilla.
    return render_template(
        "inicio.html",
        resultados=resultados,
        conteo=conteo,
        primas=primas,
        inconsistencias=inconsistencias,
        fecha_corte=FECHA_CORTE,
    )


@bp.route("/aviso/")
def ver_aviso():
    """Devuelve el PDF del aviso de una póliza."""
    # El número viene en la URL: /aviso/?numero=AIS-2026-0001
    numero = (request.args.get("numero") or "").strip()
    if not numero:
        abort(404)

    # Buscamos la póliza en el modelo.
    poliza = buscar_por_numero(numero)

    # Si no existe o todavía está vigente, no se genera aviso.
    if poliza is None or poliza["estado"] == "Vigente":
        abort(404)

    # El servicio crea el PDF y lo devolvemos para verlo en el navegador.
    datos_pdf = crear_aviso_pdf(poliza)
    return send_file(
        io.BytesIO(datos_pdf),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"aviso_{poliza['numero']}.pdf",
    )


@bp.route("/descargar-avisos")
def descargar_avisos():
    """Devuelve un .zip con los avisos de las pólizas por vencer y vencidas."""
    resultados = calcular_resultados()

    # Filtramos las pólizas que sí necesitan aviso.
    seleccionadas = [
        poliza
        for poliza in resultados
        if poliza["estado"] in ("Por vencer", "Vencida")
    ]

    # Creamos el .zip en memoria.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archivo_zip:
        # Bucle: agregamos el PDF de cada póliza seleccionada.
        for poliza in seleccionadas:
            datos_pdf = crear_aviso_pdf(poliza)
            archivo_zip.writestr(
                f"aviso_{poliza['numero']}.pdf",
                datos_pdf,
            )

    # Volvemos al inicio del archivo para enviarlo completo.
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="avisos.zip",
    )
