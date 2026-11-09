"""Órdenes y prescripciones - FHIR MedicationRequest (medicamentos) / ServiceRequest (estudios)."""
import pandas as pd
import streamlit as st

import auth
import database as db
from catalogos import FRECUENCIAS, VIAS
from modules.common import flash, header, patient_selector, show_flash


def render(user):
    header("Órdenes y Prescripciones Médicas", "Indicaciones de medicamentos y estudios · FHIR: MedicationRequest")
    show_flash()
    rol = user["rol"]
    prescribe = auth.can(rol, "ordenes:escribir")
    administra = auth.can(rol, "ordenes:administrar")
    p = patient_selector("ord_pac", user)
    if not p:
        return

    nombres = ["Órdenes del paciente"]
    if prescribe:
        nombres.append("Nueva orden")
    if administra:
        nombres.append("Administración de enfermería")
    tabs = st.tabs(nombres)
    ordenes = db.list_orders(p["id"])

    with tabs[0]:
        if not ordenes:
            st.info("Sin órdenes.")
        else:
            df = pd.DataFrame(ordenes)[["fecha", "tipo", "descripcion", "dosis", "via", "frecuencia", "duracion",
                                        "estado", "medico", "administrada_por"]]
            df.columns = ["Fecha", "Tipo", "Descripción", "Dosis", "Vía", "Frecuencia", "Duración", "Estado",
                          "Médico", "Administró"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        if prescribe:
            for o in [o for o in ordenes if o["estado"] == "Activa"]:
                c = st.columns([5, 1])
                c[0].write(f"#{o['id']} · {o['descripcion']}")
                if c[1].button("Suspender", key=f"susp_{o['id']}"):
                    db.set_order_status(o["id"], "Suspendida")
                    db.log_audit(user["usuario"], rol, "Orden suspendida", f"{p['historia_no']} · orden {o['id']}")
                    st.rerun()

    idx = 1
    if prescribe:
        with tabs[idx]:
            tipo = st.radio("Tipo de orden", ["Medicamento", "Estudio"], horizontal=True)
            with st.form("form_orden", clear_on_submit=True):
                desc = st.text_input("Medicamento (nombre y concentración) *" if tipo == "Medicamento"
                                     else "Estudio solicitado *")
                dosis = via = frec = dur = ""
                if tipo == "Medicamento":
                    c = st.columns(4)
                    dosis = c[0].text_input("Dosis")
                    via = c[1].selectbox("Vía", VIAS)
                    frec = c[2].selectbox("Frecuencia", FRECUENCIAS)
                    dur = c[3].text_input("Duración", "7 días")
                ind = st.text_area("Indicaciones adicionales")
                ok = st.form_submit_button("Emitir orden")
            if ok:
                if not desc.strip():
                    st.error("La descripción es obligatoria.")
                else:
                    db.add_order(dict(paciente_id=p["id"], tipo=tipo, descripcion=desc.strip(), dosis=dosis, via=via,
                                      frecuencia=frec, duracion=dur, indicaciones=ind, medico=user["nombre"]))
                    db.log_audit(user["usuario"], rol, "Orden emitida", f"{p['historia_no']} · {tipo}")
                    flash("Orden emitida.")
                    st.rerun()
        idx += 1

    if administra:
        with tabs[idx]:
            pend = [o for o in ordenes if o["estado"] == "Activa"]
            if not pend:
                st.info("No hay indicaciones pendientes.")
            for o in pend:
                c = st.columns([5, 1.4])
                pos = " · ".join(x for x in [o["dosis"], o["via"], o["frecuencia"]] if x)
                c[0].markdown(f"**{o['descripcion']}** ({o['tipo']})  \n{pos}  \n_{o['indicaciones'] or ''}_")
                if c[1].button("Registrar administración" if o["tipo"] == "Medicamento" else "Registrar realizado",
                               key=f"adm_{o['id']}"):
                    db.set_order_status(o["id"], "Administrada", user["nombre"])
                    db.log_audit(user["usuario"], rol, "Indicación administrada", f"{p['historia_no']} · orden {o['id']}")
                    flash("Administración registrada.")
                    st.rerun()
