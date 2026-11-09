"""Historia Clínica Electrónica - recursos FHIR Encounter / Condition."""
import streamlit as st

import auth
import database as db
from catalogos import CIE10, CIE10_OPCIONES, TIPOS_DX
from modules.common import flash, header, patient_selector, show_flash


def _dx_tuple(opcion, tipo):
    cod = opcion.split(" — ")[0]
    desc = dict(CIE10)[cod]
    return cod, desc, tipo


def render(user):
    header("Historia Clínica Electrónica", "Evolución, antecedentes y diagnósticos · FHIR: Encounter / Condition")
    show_flash()
    rol = user["rol"]
    escribir = auth.can(rol, "historia:escribir")
    p = patient_selector("hce_pac", user)
    if not p:
        return

    nombres = ["Antecedentes", "Evoluciones"] + (["Nueva evolución", "Diagnósticos y cierre"] if escribir else [])
    tabs = st.tabs(nombres)

    # --- Antecedentes
    with tabs[0]:
        if escribir:
            with st.form("form_ant"):
                ant = st.text_area("Antecedentes personales y familiares", p["antecedentes"] or "", height=130)
                ale = st.text_area("Alergias", p["alergias"] or "", height=70)
                if st.form_submit_button("Guardar antecedentes"):
                    db.update_background(p["id"], ant, ale)
                    db.log_audit(user["usuario"], rol, "Actualización de antecedentes", p["historia_no"])
                    flash("Antecedentes actualizados.")
                    st.rerun()
        else:
            st.markdown(f"**Antecedentes:** {p['antecedentes'] or '—'}")
            st.markdown(f"**Alergias:** {p['alergias'] or '—'}")

    encs = db.list_encounters(p["id"])
    dxs = db.list_diagnoses(p["id"])

    # --- Evoluciones
    with tabs[1]:
        if not encs:
            st.info("Sin evoluciones registradas.")
        for e in encs:
            badge = "badge-gray" if e["estado"] == "Cerrada" else "badge-ok"
            with st.expander(f"{e['fecha'][:16]} · {e['motivo']} · {e['estado']}", expanded=e is encs[0]):
                st.markdown(f'<span class="badge {badge}">{e["estado"]}</span> &nbsp; **Médico:** {e["medico"]}',
                            unsafe_allow_html=True)
                st.markdown(f"**Enfermedad actual:** {e['enfermedad_actual'] or '—'}")
                st.markdown(f"**Examen físico:** {e['examen_fisico'] or '—'}")
                st.markdown(f"**Plan:** {e['plan'] or '—'}")
                for d in [d for d in dxs if d["encuentro_id"] == e["id"]]:
                    st.markdown(f"- `{d['codigo']}` {d['descripcion']} _({d['tipo']})_")
                if e["cerrado_en"]:
                    st.caption(f"Historia cerrada el {e['cerrado_en']}")

    if not escribir:
        return

    # --- Nueva evolución
    with tabs[2]:
        with st.form("form_evo", clear_on_submit=True):
            motivo = st.text_input("Motivo de consulta *")
            ea = st.text_area("Enfermedad actual")
            ef = st.text_area("Examen físico")
            plan = st.text_area("Plan / conducta")
            dx_sel = st.multiselect("Diagnósticos CIE-10 (simulado) *", CIE10_OPCIONES)
            tipo = st.radio("Tipo de diagnóstico", TIPOS_DX, horizontal=True)
            ok = st.form_submit_button("Guardar evolución")
        if ok:
            if not motivo.strip() or not dx_sel:
                st.error("El motivo de consulta y al menos un diagnóstico son obligatorios.")
            else:
                db.add_encounter(dict(paciente_id=p["id"], motivo=motivo.strip(), enfermedad_actual=ea,
                                      examen_fisico=ef, plan=plan, medico=user["nombre"]),
                                 [_dx_tuple(o, tipo) for o in dx_sel])
                db.log_audit(user["usuario"], rol, "Nueva evolución clínica", p["historia_no"])
                flash("Evolución registrada.")
                st.rerun()

    # --- Diagnósticos y cierre
    with tabs[3]:
        abiertas = {f"{e['fecha'][:16]} · {e['motivo']}": e for e in encs if e["estado"] == "Abierta"}
        if not abiertas:
            st.info("No hay evoluciones abiertas. Las historias cerradas no pueden modificarse.")
        else:
            sel = st.selectbox("Evolución abierta", list(abiertas))
            e = abiertas[sel]
            with st.form("form_dx"):
                op = st.selectbox("Agregar diagnóstico", CIE10_OPCIONES)
                tp = st.radio("Tipo", TIPOS_DX, horizontal=True)
                if st.form_submit_button("Agregar diagnóstico"):
                    db.add_diagnosis(e["id"], p["id"], *_dx_tuple(op, tp))
                    db.log_audit(user["usuario"], rol, "Diagnóstico agregado", p["historia_no"])
                    flash("Diagnóstico agregado.")
                    st.rerun()
            st.divider()
            st.warning("El cierre es definitivo: la evolución quedará de solo lectura.")
            conf = st.checkbox("Confirmo que la información es correcta y deseo cerrar esta evolución")
            if st.button("Cerrar historia clínica de esta evolución", disabled=not conf):
                db.close_encounter(e["id"])
                db.log_audit(user["usuario"], rol, "Cierre de historia clínica", f"{p['historia_no']} · enc {e['id']}")
                flash("Evolución cerrada.")
                st.rerun()
