"""Capa de modelos: reglas del negocio de las pólizas."""

from __future__ import annotations

from datetime import date

from models.datos import cargar_clientes, cargar_polizas

# Fecha con la que comparamos las vigencias.
FECHA_CORTE = date(2026, 11, 9)

# Días de aviso antes del vencimiento.
DIAS_AVISO = 30


def estado_poliza(hasta: date | None, fecha_corte: date = FECHA_CORTE) -> str:
    """Devuelve el estado de una póliza según su fecha de vencimiento."""
    # Condicional: si no hay fecha, no podemos saber el estado.
    if hasta is None:
        return "Sin fecha"

    # Días que faltan para vencer. Pueden ser negativos si ya venció.
    dias = (hasta - fecha_corte).days

    if dias < 0:
        return "Vencida"
    elif dias <= DIAS_AVISO:
        return "Por vencer"
    else:
        return "Vigente"


def calcular_resultados(fecha_corte: date = FECHA_CORTE) -> list[dict]:
    """Cruza pólizas con clientes y devuelve una lista ordenada por urgencia."""
    # DataFrame de clientes.
    clientes = cargar_clientes()

    # Diccionario: cédula -> fila del cliente.
    clientes_por_cedula = {
        fila["Cedula"]: fila
        for _, fila in clientes.iterrows()
    }

    # Lista donde guardaremos cada póliza con sus datos calculados.
    resultados: list[dict] = []

    # Bucle: recorremos todas las pólizas.
    for poliza in cargar_polizas():
        # Copiamos el diccionario para no modificar el original.
        resultado = dict(poliza)

        cedula = resultado["cedula"]
        cliente = clientes_por_cedula.get(cedula)

        # Datos del cruce con el maestro.
        resultado["en_maestro"] = cliente is not None
        resultado["correo"] = (
            str(cliente["Correo"]).strip() if cliente is not None else None
        )

        # Días hasta vencer.
        hasta = resultado["hasta"]
        resultado["dias_para_vencer"] = (
            (hasta - fecha_corte).days if hasta is not None else None
        )

        # Estado usando la función anterior.
        resultado["estado"] = estado_poliza(hasta, fecha_corte)

        resultados.append(resultado)

    # Orden: menos días primero, para que lo urgente aparezca arriba.
    # Las pólizas sin fecha van al final.
    resultados.sort(
        key=lambda p: (
            p["dias_para_vencer"] is None,
            p["dias_para_vencer"] if p["dias_para_vencer"] is not None else 0,
        )
    )

    return resultados


def contar_por_estado(resultados: list[dict]) -> dict[str, int]:
    """Cuenta cuántas pólizas hay en cada estado."""
    # Diccionario con los estados posibles, todos empezando en cero.
    conteo = {
        "Vigente": 0,
        "Por vencer": 0,
        "Vencida": 0,
        "Sin fecha": 0,
    }

    # Bucle: sumamos uno al estado de cada póliza.
    for poliza in resultados:
        estado = poliza["estado"]
        conteo[estado] = conteo.get(estado, 0) + 1

    return conteo


def primas_por_aseguradora(resultados: list[dict]) -> dict[str, float]:
    """Suma las primas no vencidas por aseguradora, de mayor a menor."""
    # Diccionario: aseguradora -> suma de primas.
    sumas: dict[str, float] = {}

    # Bucle: sumamos solo las pólizas vigentes o por vencer.
    for poliza in resultados:
        if poliza["estado"] not in ("Vigente", "Por vencer"):
            continue

        # Si no hay prima, no se suma.
        if poliza["prima"] is None:
            continue

        aseguradora = poliza["aseguradora"] or "Sin aseguradora"
        sumas[aseguradora] = sumas.get(aseguradora, 0.0) + poliza["prima"]

    # sorted() ordena de mayor a menor por la suma.
    return dict(sorted(sumas.items(), key=lambda item: item[1], reverse=True))


def buscar_inconsistencias(resultados: list[dict]) -> list[str]:
    """Devuelve una lista de textos con los problemas encontrados."""
    clientes = cargar_clientes()

    # Lista de textos de inconsistencias.
    inconsistencias: list[str] = []

    # Cédulas que sí tienen al menos una póliza.
    cedulas_con_poliza = {
        poliza["cedula"] for poliza in resultados if poliza["cedula"]
    }

    # Problema 1: cliente del maestro sin ninguna póliza.
    for _, cliente in clientes.iterrows():
        cedula = cliente["Cedula"]
        if cedula not in cedulas_con_poliza:
            inconsistencias.append(
                f"Cliente sin póliza: {cliente['Nombre_Completo']} ({cedula})."
            )

    # Problema 2: póliza cuya cédula no está en el maestro.
    for poliza in resultados:
        if not poliza["en_maestro"]:
            inconsistencias.append(
                f"Póliza sin cliente en el maestro: {poliza['numero']} "
                f"(cédula {poliza['cedula']}, {poliza['nombre']})."
            )

    # Problema 3: póliza sin prima o con fecha ilegible.
    for poliza in resultados:
        if poliza["prima"] is None:
            inconsistencias.append(
                f"Póliza sin prima anual: {poliza['numero']}."
            )
        if poliza["desde"] is None or poliza["hasta"] is None:
            inconsistencias.append(
                f"Póliza con fecha ilegible: {poliza['numero']}."
            )

    return inconsistencias


def buscar_por_numero(numero: str) -> dict | None:
    """Busca una póliza por su número y devuelve el diccionario o None."""
    numero = (numero or "").strip().upper()

    # Bucle: recorremos los resultados ya calculados.
    for poliza in calcular_resultados():
        if (poliza["numero"] or "").upper() == numero:
            return poliza

    return None
