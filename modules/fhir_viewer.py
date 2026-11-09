"""Interoperabilidad académica: visor de recursos HL7 FHIR R4 en JSON."""
import json

import pandas as pd
import streamlit as st

import auth
import database as db
import fhir
from modules.common import header, patient_selector


def _datos(p):
    return p, db.list_vitals(p["id"]), db.list_encounters(p["id"]), db.list_diagnoses(p["id"]), db.list_orders(p["id"])


def render(user):
    header("Interoperabilidad Académica · Visor HL7/FHIR", "Esquema JSON estándar de los datos del paciente (FHIR R4 simplificado)")
    p = patient_selector("fhir_pac", user)
    if not p:
        return
    recursos = fhir.resources_for(*_datos(p))
    tecnico = auth.can(user["rol"], "fhir:tecnico")
    tabs = st.tabs(["Recursos", "Bundle completo"] + (["Vista técnica (Informática)"] if tecnico else []))

    with tabs[0]:
        tipo = st.selectbox("Tipo de recurso", list(recursos))
        data = recursos[tipo]
        st.caption(f"{len(data) if isinstance(data, list) else 1} recurso(s)")
        st.json(data, expanded=2)
        st.download_button("Descargar JSON", json.dumps(data, ensure_ascii=False, indent=2),
                           file_name=f"{tipo.split()[0]}_{p['historia_no']}.json", mime="application/json")

    with tabs[1]:
        b = fhir.bundle(*_datos(p))
        st.caption(f"Bundle tipo «collection» con {len(b['entry'])} entradas")
        st.json(b, expanded=1)
        st.download_button("Descargar Bundle", json.dumps(b, ensure_ascii=False, indent=2),
                           file_name=f"Bundle_{p['historia_no']}.json", mime="application/json")

    if tecnico:
        with tabs[2]:
            st.markdown("**Mapeo simulado de endpoints REST FHIR** (el prototipo no expone un servidor real).")
            st.dataframe(pd.DataFrame([
                ("GET", f"/Patient/{p['id']}", "Patient", "pacientes"),
                ("GET", f"/Observation?patient={p['id']}&category=vital-signs", "Observation", "signos_vitales"),
                ("GET", f"/Encounter?patient={p['id']}", "Encounter", "encuentros"),
                ("GET", f"/Condition?patient={p['id']}", "Condition", "diagnosticos"),
                ("GET", f"/MedicationRequest?patient={p['id']}", "MedicationRequest / ServiceRequest", "ordenes"),
            ], columns=["Método", "Endpoint", "Recurso", "Tabla local"]), hide_index=True, use_container_width=True)
            st.markdown("**CapabilityStatement (resumen simulado)**")
            st.json({"resourceType": "CapabilityStatement", "status": "draft", "fhirVersion": "4.0.1",
                     "format": ["json"], "kind": "instance",
                     "software": {"name": "Sistema HCE - Hospital Universitario UDONE", "version": "1.0-edu"},
                     "rest": [{"mode": "server", "resource": [
                         {"type": t, "interaction": [{"code": "read"}, {"code": "search-type"}]}
                         for t in ["Patient", "Observation", "Encounter", "Condition", "MedicationRequest", "ServiceRequest"]]}]})
            st.markdown("**Terminologías usadas:** LOINC (signos vitales), UCUM (unidades), CIE-10 / ICD-10 (diagnósticos).")
