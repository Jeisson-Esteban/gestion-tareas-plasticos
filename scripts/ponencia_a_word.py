"""Convierte docs/ponencia-final.md en docs/ponencia-final.docx con formato APA 7.

Uso:  python scripts/ponencia_a_word.py [entrada.md] [salida.docx]

Se usa python-docx en lugar de pandoc para controlar el formato APA
(sangrías, títulos por nivel, figuras) sin depender de una plantilla externa.
Solo soporta el subconjunto de markdown que usa la ponencia.
"""

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
FUENTE, MONO = "Times New Roman", "Consolas"
SANGRIA = Cm(1.27)
ANCHO_FIGURA = Cm(16)

FIGURA = re.compile(r"^\[Insertar Figura \d+:\s*(.+?)\]$")
LISTA = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
# Orden importa: enlaces y código antes que énfasis, ** antes que *
EN_LINEA = re.compile(r"\[([^\]]+)\]\(([^)]+)\)|`([^`]+)`|\*\*(.+?)\*\*|\*(.+?)\*")


def configurar(doc):
    for s in doc.sections:
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Cm(2.54)
    normal = doc.styles["Normal"]
    normal.font.name = FUENTE
    normal.font.size = Pt(12)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    pf.space_before = pf.space_after = Pt(0)


def hipervinculo(parrafo, texto, url):
    rel = parrafo.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), rel)
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    for etiqueta, val in (("w:color", "0563C1"), ("w:u", "single")):
        e = OxmlElement(etiqueta)
        e.set(qn("w:val"), val)
        rpr.append(e)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.text = texto
    t.set(qn("xml:space"), "preserve")
    r.append(t)
    h.append(r)
    parrafo._p.append(h)


def agregar_texto(parrafo, texto, negrita=False, cursiva=False):
    pos = 0
    for m in EN_LINEA.finditer(texto):
        if m.start() > pos:
            run = parrafo.add_run(texto[pos:m.start()])
            run.bold, run.italic = negrita or None, cursiva or None
        enlace, url, codigo, neg, cur = m.groups()
        if enlace:
            hipervinculo(parrafo, enlace, url)
        elif codigo:
            run = parrafo.add_run(codigo)
            run.font.name = MONO
            run.font.size = Pt(10)
        elif neg:
            agregar_texto(parrafo, neg, True, cursiva)
        else:
            agregar_texto(parrafo, cur, negrita, True)
        pos = m.end()
    if pos < len(texto):
        run = parrafo.add_run(texto[pos:])
        run.bold, run.italic = negrita or None, cursiva or None


def titulo(doc, nivel, texto):
    p = doc.add_paragraph()
    run = p.add_run(texto)
    run.bold = True
    # APA 7: nivel 1 centrado; nivel 3 además en cursiva
    if nivel == 1:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if nivel >= 3:
        run.italic = True
    p.paragraph_format.keep_with_next = True
    return p


def sencillo(p):
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE


def bloque_codigo(doc, lineas):
    p = doc.add_paragraph()
    sencillo(p)
    p.paragraph_format.space_after = Pt(6)
    sombra = OxmlElement("w:shd")
    sombra.set(qn("w:val"), "clear")
    sombra.set(qn("w:fill"), "F2F2F2")
    p._p.get_or_add_pPr().append(sombra)
    for i, linea in enumerate(lineas):
        run = p.add_run(linea)
        run.font.name = MONO
        run.font.size = Pt(9)
        if i < len(lineas) - 1:
            run.add_break()


def tabla(doc, filas):
    celdas = [[c.strip() for c in f.strip().strip("|").split("|")] for f in filas]
    celdas = [f for f in celdas if not all(re.fullmatch(r":?-+:?", c) for c in f)]
    t = doc.add_table(rows=len(celdas), cols=len(celdas[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, fila in enumerate(celdas):
        for j, texto in enumerate(fila[: len(celdas[0])]):
            p = t.cell(i, j).paragraphs[0]
            sencillo(p)
            agregar_texto(p, texto, negrita=(i == 0))
            for run in p.runs:
                run.font.size = Pt(10)
    doc.add_paragraph()  # aire después de la tabla


def figura(doc, ruta):
    imagen = (RAIZ / ruta).resolve()
    p = doc.add_paragraph()
    sencillo(p)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(18)
    if imagen.exists():
        p.add_run().add_picture(str(imagen), width=ANCHO_FIGURA)
    else:
        run = p.add_run(f"FALTA IMAGEN: {ruta}")
        run.bold = True
        run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)


def convertir(md, salida):
    doc = Document()
    configurar(doc)
    lineas = md.splitlines()
    en_referencias = False
    i = 0
    while i < len(lineas):
        linea = lineas[i].rstrip()
        if re.match(r"^#{1,2}\s+Notas para publicar", linea):
            break  # esa sección es para el autor, no para el foro
        if not linea.strip() or linea.strip() == "---":
            i += 1
            continue
        if linea.startswith("```"):
            fin = i + 1
            while fin < len(lineas) and not lineas[fin].startswith("```"):
                fin += 1
            bloque_codigo(doc, lineas[i + 1:fin])
            i = fin + 1
            continue
        if linea.lstrip().startswith("|"):
            fin = i
            while fin < len(lineas) and lineas[fin].lstrip().startswith("|"):
                fin += 1
            tabla(doc, lineas[i:fin])
            i = fin
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", linea)
        if m:
            texto = m.group(2).strip()
            en_referencias = texto.lower() == "referencias"
            p = titulo(doc, len(m.group(1)), texto)
            p.paragraph_format.page_break_before = en_referencias  # APA: referencias en página nueva
            i += 1
            continue
        m = FIGURA.match(linea.strip())
        if m:
            figura(doc, m.group(1).strip())
            i += 1
            continue
        m = LISTA.match(linea)
        if m:
            estilo = "List Number" if m.group(2)[0].isdigit() else "List Bullet"
            p = doc.add_paragraph(style=estilo)
            agregar_texto(p, m.group(3))
            i += 1
            continue
        # párrafo: une líneas consecutivas hasta una línea en blanco o un bloque
        partes = [linea.strip()]
        i += 1
        while i < len(lineas) and lineas[i].strip() and not re.match(r"^(#|```|\||\[Insertar Figura|\s*([-*]|\d+\.)\s)", lineas[i]):
            partes.append(lineas[i].strip())
            i += 1
        texto = " ".join(partes)
        p = doc.add_paragraph()
        agregar_texto(p, texto)
        pf = p.paragraph_format
        if en_referencias:
            pf.left_indent, pf.first_line_indent = SANGRIA, -SANGRIA  # sangría francesa
        elif re.fullmatch(r"\*\*Figura \d+\*\*|\*[^*].*\*", texto):
            pf.keep_with_next = True  # número y título de figura no se separan de la imagen
        else:
            pf.first_line_indent = SANGRIA
    doc.save(salida)


if __name__ == "__main__":
    entrada = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "docs" / "ponencia-final.md"
    salida = Path(sys.argv[2]) if len(sys.argv) > 2 else RAIZ / "docs" / "ponencia-final.docx"
    convertir(entrada.read_text(encoding="utf-8"), salida)
    print(f"Generado {salida}")
