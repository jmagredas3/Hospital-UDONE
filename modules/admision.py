"""Admisión de pacientes - recurso FHIR Patient."""
import sqlite3
from datetime import date

import pandas as pd
import streamlit as st

import auth
import database as db
from catalogos import GRUPOS_SANGUINEOS
from modules.common import flash, header, show_flash


def render(user):
    header("Admisión de Pacientes", "Registro demográfico · Recurso FHIR: Patient")
    show_flash()
    escribir = auth.can(user["rol"], "admision:escribir")
    tabs = st.tabs(["Pacientes registrados", "Nuevo ingreso"] if escribir else ["Pacientes registrados"])

    with tabs[0]:
        q = st.text_input("Buscar por nombre, cédula o N° de historia", key="adm_q")
        pacs = db.list_patients(q)
        if pacs:
            df = pd.DataFrame(pacs)[["historia_no", "cedula", "apellidos", "nombres", "fecha_nac", "sexo",
                                     "grupo_sanguineo", "telefono"]]
            df.columns = ["Historia N°", "Cédula", "Apellidos", "Nombres", "Nacimiento", "Sexo", "Grupo", "Teléfono"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"{len(pacs)} paciente(s)")
        else:
            st.info("Sin resultados.")

    if escribir:
        with tabs[1]:
            with st.form("form_admision", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nombres = c1.text_input("Nombres *")
                apellidos = c2.text_input("Apellidos *")
                cedula = c1.text_input("Cédula de identidad * (ej. V-12345678)")
                fnac = c2.date_input("Fecha de nacimiento *", value=date(1990, 1, 1),
                                     min_value=date(1900, 1, 1), max_value=date.today())
                sexo = c1.selectbox("Sexo", ["Femenino", "Masculino", "Otro"])
                gs = c2.selectbox("Grupo sanguíneo", GRUPOS_SANGUINEOS)
                tel = c1.text_input("Teléfono")
                contacto = c2.text_input("Contacto de emergencia")
                direccion = st.text_input("Dirección")
                antecedentes = st.text_area("Antecedentes personales y familiares")
                alergias = st.text_area("Alergias", height=70)
                ok = st.form_submit_button("Registrar paciente")
            if ok:
                if not (nombres.strip() and apellidos.strip() and cedula.strip()):
                    st.error("Nombres, apellidos y cédula son obligatorios.")
                else:
                    try:
                        pid = db.add_patient(dict(
                            cedula=cedula.strip().upper(), nombres=nombres.strip(), apellidos=apellidos.strip(),
                            fecha_nac=fnac.isoformat(), sexo=sexo, grupo_sanguineo=gs, telefono=tel,
                            direccion=direccion, contacto_emergencia=contacto, antecedentes=antecedentes,
                            alergias=alergias or "Ninguna conocida"))
                        p = db.get_patient(pid)
                        db.log_audit(user["usuario"], user["rol"], "Admisión de paciente", p["historia_no"])
                        flash(f"Paciente registrado con historia {p['historia_no']}.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Ya existe un paciente con esa cédula.")
