"""Utilidades compartidas por los módulos."""
from datetime import date, datetime
from html import escape

import streamlit as st

import database as db


def header(titulo, subtitulo=""):
    st.markdown(f'<div class="hce-header"><h2>{escape(titulo)}</h2><p>{escape(subtitulo)}</p></div>',
                unsafe_allow_html=True)


def flash(msg, kind="success"):
    st.session_state["_flash"] = (kind, msg)


def show_flash():
    f = st.session_state.pop("_flash", None)
    if f:
        getattr(st, f[0])(f[1])


def edad(fecha_nac):
    b = datetime.strptime(fecha_nac, "%Y-%m-%d").date()
    t = date.today()
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


def banner(p):
    e = escape
    st.markdown(
        f'<div class="pac-banner"><b>{e(p["apellidos"])}, {e(p["nombres"])}</b> · {e(p["historia_no"])} · '
        f'C.I. {e(p["cedula"])} · {edad(p["fecha_nac"])} años · {e(p["sexo"] or "")} · '
        f'Grupo {e(p["grupo_sanguineo"] or "—")}<br><b>Alergias:</b> {e(p["alergias"] or "—")}</div>',
        unsafe_allow_html=True)


def patient_selector(key, user=None):
    pacientes = db.list_patients()
    if not pacientes:
        st.info("No hay pacientes registrados. Use el módulo de Admisión.")
        return None
    opciones = {f"{p['historia_no']} — {p['apellidos']}, {p['nombres']}": p for p in pacientes}
    sel = st.selectbox("Paciente", list(opciones), key=key)
    p = opciones[sel]
    banner(p)
    if user:
        mark = f"_visto_{p['id']}"
        if st.session_state.get("_ultimo_visto") != p["id"]:
            db.log_audit(user["usuario"], user["rol"], "Consulta de paciente", p["historia_no"])
            st.session_state["_ultimo_visto"] = p["id"]
    return p
