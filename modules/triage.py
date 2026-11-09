"""Triage / signos vitales - recurso FHIR Observation."""
import pandas as pd
import streamlit as st

import auth
import database as db
from modules.common import flash, header, patient_selector, show_flash


def evaluar(v):
    """Alertas educativas simples (no sustituyen un sistema de triage validado)."""
    a = []
    if v["pas"] >= 180 or v["pad"] >= 120:
        a.append(("error", "Presión arterial en rango de crisis hipertensiva"))
    elif v["pas"] >= 140 or v["pad"] >= 90:
        a.append(("warning", "Presión arterial elevada"))
    elif v["pas"] < 90:
        a.append(("warning", "Posible hipotensión"))
    if v["temp"] >= 38:
        a.append(("warning", "Fiebre"))
    elif v["temp"] < 35.5:
        a.append(("warning", "Hipotermia"))
    if v["fc"] > 100:
        a.append(("warning", "Taquicardia"))
    elif v["fc"] < 60:
        a.append(("warning", "Bradicardia"))
    if v["fr"] > 20:
        a.append(("warning", "Taquipnea"))
    elif v["fr"] < 12:
        a.append(("warning", "Bradipnea"))
    if v["sat"] < 90:
        a.append(("error", "Hipoxemia severa"))
    elif v["sat"] < 94:
        a.append(("warning", "Saturación de oxígeno baja"))
    return a


def render(user):
    header("Triage / Signos Vitales", "Enfermería · Recurso FHIR: Observation")
    show_flash()
    rol = user["rol"]
    escribir = auth.can(rol, "triage:escribir")
    practica = auth.can(rol, "triage:practica")
    p = patient_selector("tri_pac", user)
    if not p:
        return

    if escribir or practica:
        if practica and not escribir:
            st.info("Modo práctica: los registros quedan marcados como «práctica» en el historial.")
        with st.form("form_vitales", clear_on_submit=False):
            c = st.columns(3)
            pas = c[0].number_input("PA sistólica (mmHg)", 40, 300, 120)
            pad = c[1].number_input("PA diastólica (mmHg)", 20, 200, 80)
            temp = c[2].number_input("Temperatura (°C)", 30.0, 43.0, 36.6, step=0.1)
            c = st.columns(3)
            fc = c[0].number_input("Frecuencia cardíaca (lpm)", 20, 250, 75)
            fr = c[1].number_input("Frecuencia respiratoria (rpm)", 5, 60, 16)
            sat = c[2].number_input("Saturación O₂ (%)", 50, 100, 98)
            c = st.columns(2)
            peso = c[0].number_input("Peso (kg)", 0.0, 400.0, 0.0, step=0.5)
            talla = c[1].number_input("Talla (cm)", 0.0, 250.0, 0.0, step=1.0)
            nota = st.text_input("Observaciones")
            ok = st.form_submit_button("Registrar signos vitales")
        if ok:
            reg = user["nombre"] + ("" if escribir else " (práctica)")
            v = dict(paciente_id=p["id"], pas=pas, pad=pad, temp=temp, fc=fc, fr=fr, sat=sat,
                     peso=peso or None, talla=talla or None, nota=nota, registrado_por=reg)
            db.add_vitals(v)
            db.log_audit(user["usuario"], rol, "Registro de signos vitales", p["historia_no"])
            for kind, msg in evaluar(v):
                st.session_state.setdefault("_alertas", []).append((kind, msg))
            flash("Signos vitales registrados.")
            st.rerun()

    for kind, msg in st.session_state.pop("_alertas", []):
        getattr(st, kind)(msg)

    st.subheader("Historial de signos vitales")
    vit = db.list_vitals(p["id"])
    if not vit:
        st.info("Sin registros para este paciente.")
        return
    df = pd.DataFrame(vit)
    ver = df[["fecha", "pas", "pad", "temp", "fc", "fr", "sat", "peso", "talla", "nota", "registrado_por"]].copy()
    ver.columns = ["Fecha", "PAS", "PAD", "Temp °C", "FC", "FR", "SatO₂ %", "Peso kg", "Talla cm", "Observaciones", "Registró"]
    st.dataframe(ver, use_container_width=True, hide_index=True)
    if len(df) > 1:
        g = df.sort_values("fecha").set_index("fecha")[["pas", "pad", "fc"]]
        g.columns = ["PA sistólica", "PA diastólica", "Frec. cardíaca"]
        st.line_chart(g, color=["#0B3C7A", "#1F5FA8", "#8A97A8"])
