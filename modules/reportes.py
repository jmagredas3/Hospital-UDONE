"""Reportes y exportación a PDF."""
import streamlit as st

import database as db
from modules.common import header, patient_selector
from pdf_report import build_pdf


def render(user):
    header("Reportes y Exportación a PDF", "Resumen formal de la Historia Clínica Electrónica")
    p = patient_selector("rep_pac", user)
    if not p:
        return
    st.markdown("**Secciones a incluir**")
    c = st.columns(3)
    sec = set()
    if c[0].checkbox("Signos vitales", True):
        sec.add("vitales")
    if c[1].checkbox("Evoluciones y diagnósticos", True):
        sec.add("evoluciones")
    if c[2].checkbox("Órdenes y prescripciones", True):
        sec.add("ordenes")
    if st.button("Generar PDF"):
        pdf = build_pdf(p, db.list_vitals(p["id"]), db.list_encounters(p["id"]), db.list_diagnoses(p["id"]),
                        db.list_orders(p["id"]), user["nombre"], sec)
        db.log_audit(user["usuario"], user["rol"], "Exportación PDF", p["historia_no"])
        st.session_state["_pdf"] = (p["historia_no"], pdf)
    if "_pdf" in st.session_state:
        hn, pdf = st.session_state["_pdf"]
        st.success(f"PDF generado para {hn}.")
        st.download_button("Descargar PDF", pdf, file_name=f"HCE_{hn}.pdf", mime="application/pdf")
