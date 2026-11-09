"""Capa de servicios: crea el aviso de renovación en PDF."""

from __future__ import annotations

from fpdf import FPDF

# Colores del diseño.
ROJO = (174, 24, 0)
NEGRO = (32, 30, 29)
GRIS_CLARO = (243, 242, 242)
GRIS_TEXTO = (120, 120, 120)
GRIS_BORDE = (200, 200, 200)
BLANCO = (255, 255, 255)


def _latin1(texto: object) -> str:
    """Convierte un texto a latin-1 para que Helvetica no falle con tildes."""
    return str(texto).encode("latin-1", errors="replace").decode("latin-1")


def _fecha_texto(fecha) -> str:
    """Devuelve una fecha como dd/mm/aaaa o un texto de respaldo."""
    if fecha is None:
        return "No registrada"
    return fecha.strftime("%d/%m/%Y")


def _texto_o_respaldo(valor: object, respaldo: str = "No registrada") -> str:
    """Devuelve el valor como texto o el respaldo si está vacío."""
    if valor is None or str(valor).strip() == "":
        return respaldo
    return str(valor).strip()


def _parrafo(poliza: dict) -> str:
    """Arma el párrafo según el estado de la póliza."""
    estado = poliza.get("estado")
    hasta = _fecha_texto(poliza.get("hasta"))
    dias = poliza.get("dias_para_vencer")

    # Condicional: póliza ya vencida.
    if estado == "Vencida":
        return (
            f"Le informamos que su póliza venció el {hasta}. "
            "Para continuar protegido, por favor comuníquese con su asesor."
        )

    # Condicional: póliza cerca de vencer.
    if estado == "Por vencer":
        if dias is None:
            return (
                f"Le informamos que su póliza vence el {hasta}. "
                "Su asesor se comunicará con usted."
            )
        return (
            f"Le informamos que su póliza vence el {hasta}, "
            f"dentro de {dias} días. Su asesor se comunicará con usted."
        )

    # Condicional: póliza todavía vigente.
    if estado == "Vigente":
        return f"Le informamos que su póliza se encuentra vigente hasta el {hasta}."

    # Respaldo: no se pudo leer la fecha.
    return (
        "No se pudo leer la fecha de vencimiento de su póliza. "
        "Por favor comuníquese con su asesor."
    )


def _fila_tabla(pdf: FPDF, etiqueta: str, valor: str) -> None:
    """Dibuja una fila de la tabla: etiqueta a la izquierda y valor a la derecha."""
    # Celda de la etiqueta, con fondo gris claro.
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(*GRIS_CLARO)
    pdf.cell(50, 8, _latin1(etiqueta), border=1, fill=True)

    # Celda del valor.
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(130, 8, _latin1(valor), border=1)

    # Salto de línea para la siguiente fila.
    pdf.ln(8)


def crear_aviso_pdf(poliza: dict) -> bytes:
    """Crea el aviso de renovación en A4 vertical y lo devuelve en bytes."""
    # Creamos el PDF en A4 vertical (P = portrait), con medidas en milímetros.
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Banda superior roja.
    pdf.set_fill_color(*ROJO)
    pdf.rect(0, 0, 210, 38, style="F")

    # Textos blancos dentro de la banda.
    pdf.set_text_color(*BLANCO)
    pdf.set_xy(15, 10)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 8, _latin1("Corredora de Seguros Horizonte"))

    pdf.set_xy(15, 21)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 7, _latin1("Aviso de renovación de póliza"))

    # Saludo.
    pdf.set_text_color(*NEGRO)
    pdf.set_y(48)
    pdf.set_font("Helvetica", "B", 12)
    nombre = _texto_o_respaldo(poliza.get("nombre"), "cliente")
    pdf.cell(0, 6, _latin1(f"Estimado(a) {nombre}:"))
    pdf.ln(10)

    # Párrafo según el estado de la póliza.
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, _latin1(_parrafo(poliza)))
    pdf.ln(6)

    # Texto de la vigencia.
    desde = poliza.get("desde")
    hasta = poliza.get("hasta")

    if desde is not None and hasta is not None:
        vigencia = f"{_fecha_texto(desde)} al {_fecha_texto(hasta)}"
    elif desde is not None:
        vigencia = f"Desde {_fecha_texto(desde)}"
    elif hasta is not None:
        vigencia = f"Hasta {_fecha_texto(hasta)}"
    else:
        vigencia = "No registrada"

    # Prima anual: si no hay dato, mostramos "No registrada".
    prima = poliza.get("prima")
    prima_texto = "No registrada" if prima is None else f"CRC {prima:,.2f}"

    # Lista de filas de la tabla.
    filas = [
        ("Número de póliza", _texto_o_respaldo(poliza.get("numero"))),
        ("Aseguradora", _texto_o_respaldo(poliza.get("aseguradora"))),
        ("Ramo", _texto_o_respaldo(poliza.get("ramo"))),
        ("Cédula", _texto_o_respaldo(poliza.get("cedula"))),
        ("Vigencia", vigencia),
        ("Prima anual", prima_texto),
        ("Forma de pago", _texto_o_respaldo(poliza.get("pago"))),
    ]

    # Bucle: dibujamos cada fila de la tabla.
    for etiqueta, valor in filas:
        _fila_tabla(pdf, etiqueta, valor)

    # Pie de página gris.
    # Desactivamos el salto automático para que el pie no se vaya a otra página.
    pdf.set_auto_page_break(auto=False)
    pdf.set_y(-20)
    pdf.set_draw_color(*GRIS_BORDE)
    pdf.line(15, pdf.get_y() - 3, 195, pdf.get_y() - 3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.cell(
        0,
        5,
        _latin1(
            "Documento ficticio para fines académicos. "
            "Universidad Fundepos - Técnico en IA Empresarial."
        ),
        align="C",
    )

    # Devolvemos el PDF como bytes.
    return bytes(pdf.output())
