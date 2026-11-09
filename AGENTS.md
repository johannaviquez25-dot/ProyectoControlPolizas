# AGENTS.md

## Idioma

- Responde siempre en español, aunque el código, los archivos o las instrucciones estén en otro idioma.

## Qué es este espacio

- No es un repositorio de código: es un conjunto de **datos y documentos académicos ficticios** (Universidad Fundepos, Técnico en IA Empresarial). No hay build, tests, lint, package manifest ni CI.
- La ruta raíz termina en un espacio (`.../Proyecto control polizas `): **cita siempre las rutas**.
- Todo el contenido es ficticio; no lo trates como datos reales de clientes.

## Estructura y fuente de verdad

- `Insumos_Control_Polizas/Maestro_Clientes.xlsx` → hoja `Clientes`, 20 registros. Columnas: `Cedula`, `Nombre_Completo`, `Correo`, `Telefono`, `Asesor`. La cédula es la clave.
- `Insumos_Control_Polizas/polizas/` → 20 PDFs de una página generados con ReportLab.
- No existe otro registro de pólizas: el estado se deriva de los PDFs + el maestro.

## Convención de pólizas

- Nombre: `Poliza_<CODIGO>-<AÑO>-<NNNN>.pdf`. El número interno y el pie de página (`Pagina 1 de 1 - ...`) deben coincidir con el nombre del archivo.
- Códigos de aseguradora: `AIS` = Aseguradora del Istmo S.A.; `PCS` = Proteccion Caribe S.A.; `SPC` = Seguros Pacifico Central S.A.
- Campos del PDF: Número, Ramo, Tomador/Asegurado, Cédula, Vigencia desde/hasta (`DD/MM/YYYY`), Prima anual (`CRC 228,000.00`), Forma de pago, Suma asegurada, Intermediario, Asesor, Coberturas.
- Ramos usados: Automovil, Salud, Vida, Hogar, Responsabilidad Civil.

## Codificación y extracción (gotchas)

- Los datos están **sin tildes** (`Umana`, `Zuniga`, `Bolanos`, `Proteccion`, `Pacifico`). No "corrijas" tildes: compara literalmente.
- No hay `pdftotext`, `openpyxl` ni `pandas` instalados. El texto de los PDFs está en un stream ASCII85+Flate; con stdlib:

```python
import re, zlib, base64
d = open(pdf, "rb").read()
s = re.search(rb"stream\r?\n(.*?)endstream", d, re.S).group(1).strip()
text = zlib.decompress(base64.a85decode(s, adobe=True)).decode("latin-1")
```

- El XLSX usa inline strings (no hay `sharedStrings.xml`); se puede leer con `zipfile` + XML sin dependencias.

## Inconsistencias conocidas (verificadas 2026-11-09)

- `Poliza_PCS-2026-0009.pdf` es de **Roberto Fantasma Perez** (`9-0000-0001`), que no existe en el maestro.
- **Javier Espinoza Leon** (`1-0321-0654`) está en el maestro pero no tiene póliza.
- `AIS-2026-0002` tiene `Prima anual` vacía (solo `Forma de pago: Semestral`).
- Probablemente son casos de prueba intencionales: repórtalos; no los "arregles" en silencio.

## Reglas de trabajo

- No edites binarios a mano ni regeneres PDFs/XLSX sin pedirlo; conserva nombres, numeración y formato.
- Al agregar pólizas, sigue la convención anterior y actualiza el maestro cuando corresponda.
- `.DS_Store` es ruido; ignóralo.
