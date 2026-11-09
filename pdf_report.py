"""Generación del resumen de Historia Clínica Electrónica en PDF (ReportLab)."""
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from styles import LOGO_PATH
import os

AZUL = colors.HexColor("#0B3C7A")
AZUL_CLARO = colors.HexColor("#E8EFF8")
GRIS = colors.HexColor("#5F6B7A")
GRIS_CLARO = colors.HexColor("#F3F5F8")
BORDE = colors.HexColor("#D9DFE7")

_ss = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=_ss["Normal"], fontSize=9, leading=12)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8, textColor=GRIS)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8, leading=10)
H1 = ParagraphStyle("h1", parent=_ss["Title"], fontSize=15, textColor=AZUL, alignment=0, spaceAfter=0)
H2 = ParagraphStyle("h2", parent=_ss["Heading2"], fontSize=11, textColor=AZUL, spaceBefore=10, spaceAfter=4)


def P(text, style=BODY):
    t = escape(str(text)) if text not in (None, "") else "—"
    return Paragraph(t.replace("\n", "<br/>"), style)


def _tabla(data, widths, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, BORDE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), AZUL), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO])]
    t.setStyle(TableStyle(st))
    return t


def _hdr(text):
    return Paragraph(f'<font color="white"><b>{escape(text)}</b></font>', CELL)


def _edad(fecha_nac):
    b = datetime.strptime(fecha_nac, "%Y-%m-%d").date()
    t = datetime.now().date()
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


def build_pdf(patient, vitals, encounters, dxs, orders, usuario, secciones=None):
    secciones = secciones or {"vitales", "evoluciones", "ordenes"}
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.6 * cm, bottomMargin=1.8 * cm,
                            title=f"HCE {patient['historia_no']}", author="Sistema HCE - Hospital Universitario UDONE")
    W = letter[0] - 4 * cm
    s = []

    # Encabezado con logotipo
    logo = Image(LOGO_PATH, 2.3 * cm, 2.3 * cm) if os.path.exists(LOGO_PATH) else P("")
    titulo = [Paragraph("HOSPITAL UNIVERSITARIO UDONE", H1),
              Paragraph("Resumen de Historia Clínica Electrónica", ParagraphStyle("st", parent=BODY, fontSize=11, textColor=GRIS)),
              Paragraph(f"Emitido: {datetime.now():%d/%m/%Y %H:%M} · Usuario: {escape(usuario)}", SMALL)]
    h = Table([[logo, titulo]], colWidths=[2.8 * cm, W - 2.8 * cm])
    h.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    s += [h, HRFlowable(width="100%", thickness=2, color=AZUL, spaceBefore=4, spaceAfter=6)]

    # Datos del paciente
    p = patient
    s.append(Paragraph("1. Datos del paciente", H2))
    datos = [
        [P("Historia N°", SMALL), P(p["historia_no"]), P("Cédula", SMALL), P(p["cedula"])],
        [P("Paciente", SMALL), P(f"{p['apellidos']}, {p['nombres']}"), P("Edad / Sexo", SMALL),
         P(f"{_edad(p['fecha_nac'])} años · {p['sexo']}")],
        [P("Fecha de nacimiento", SMALL), P(p["fecha_nac"]), P("Grupo sanguíneo", SMALL), P(p["grupo_sanguineo"])],
        [P("Teléfono", SMALL), P(p["telefono"]), P("Contacto de emergencia", SMALL), P(p["contacto_emergencia"])],
        [P("Dirección", SMALL), P(p["direccion"]), P("Alergias", SMALL), P(p["alergias"])],
    ]
    t = _tabla(datos, [3.2 * cm, W / 2 - 3.2 * cm, 3.6 * cm, W / 2 - 3.6 * cm], header=False)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), AZUL_CLARO), ("BACKGROUND", (2, 0), (2, -1), AZUL_CLARO)]))
    s += [t, Spacer(1, 4), Paragraph("<b>Antecedentes:</b> " + escape(p["antecedentes"] or "—").replace("\n", "<br/>"), BODY)]

    n = 2
    if "vitales" in secciones:
        s.append(Paragraph(f"{n}. Signos vitales (últimos 10 registros)", H2)); n += 1
        if vitals:
            rows = [[_hdr(x) for x in ["Fecha", "PA mmHg", "Temp °C", "FC lpm", "FR rpm", "SatO₂ %", "Peso/Talla", "Registró"]]]
            for v in vitals[:10]:
                rows.append([P(v["fecha"][:16], CELL), P(f"{v['pas']}/{v['pad']}", CELL), P(v["temp"], CELL),
                             P(v["fc"], CELL), P(v["fr"], CELL), P(v["sat"], CELL),
                             P(f"{v['peso'] or '—'} kg / {v['talla'] or '—'} cm", CELL), P(v["registrado_por"], CELL)])
            s.append(_tabla(rows, [2.6 * cm, 1.8 * cm, 1.5 * cm, 1.4 * cm, 1.4 * cm, 1.5 * cm, 3.0 * cm, W - 13.2 * cm]))
        else:
            s.append(P("Sin registros."))

    if "evoluciones" in secciones:
        s.append(Paragraph(f"{n}. Evolución clínica y diagnósticos (CIE-10)", H2)); n += 1
        if not encounters:
            s.append(P("Sin evoluciones registradas."))
        for e in encounters:
            ed = [d for d in dxs if d["encuentro_id"] == e["id"]]
            cab = Paragraph(f"<b>{escape(e['fecha'][:16])}</b> — {escape(e['motivo'])} "
                            f"<font color='#5F6B7A'>[{e['estado']}] · {escape(e['medico'])}</font>", BODY)
            filas = [[cab, ""],
                     [P("Enfermedad actual", SMALL), P(e["enfermedad_actual"])],
                     [P("Examen físico", SMALL), P(e["examen_fisico"])],
                     [P("Plan", SMALL), P(e["plan"])],
                     [P("Diagnósticos", SMALL), P("\n".join(f"{d['codigo']} — {d['descripcion']} ({d['tipo']})" for d in ed))]]
            t = _tabla(filas, [3.0 * cm, W - 3.0 * cm], header=False)
            t.setStyle(TableStyle([("SPAN", (0, 0), (1, 0)), ("BACKGROUND", (0, 0), (-1, 0), AZUL_CLARO)]))
            s += [t, Spacer(1, 6)]

    if "ordenes" in secciones:
        s.append(Paragraph(f"{n}. Órdenes médicas y prescripciones", H2)); n += 1
        if orders:
            rows = [[_hdr(x) for x in ["Fecha", "Tipo", "Descripción / Indicación", "Posología", "Estado"]]]
            for o in orders:
                pos = " · ".join(x for x in [o["dosis"], o["via"], o["frecuencia"], o["duracion"]] if x)
                desc = o["descripcion"] + (f"\n{o['indicaciones']}" if o["indicaciones"] else "")
                rows.append([P(o["fecha"][:16], CELL), P(o["tipo"], CELL), P(desc, CELL), P(pos, CELL), P(o["estado"], CELL)])
            s.append(_tabla(rows, [2.6 * cm, 2.0 * cm, W - 10.4 * cm, 4.0 * cm, 1.8 * cm]))
        else:
            s.append(P("Sin órdenes registradas."))

    def footer(canvas, d):
        canvas.saveState()
        canvas.setStrokeColor(AZUL); canvas.setLineWidth(0.8)
        canvas.line(2 * cm, 1.4 * cm, letter[0] - 2 * cm, 1.4 * cm)
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawString(2 * cm, 1.0 * cm, "Sistema HCE - Hospital Universitario UDONE · Documento con fines educativos; datos ficticios, sin validez clínica ni legal.")
        canvas.drawRightString(letter[0] - 2 * cm, 1.0 * cm, f"Página {d.page}")
        canvas.restoreState()

    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
