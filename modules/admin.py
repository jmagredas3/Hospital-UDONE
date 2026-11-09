"""Administración de usuarios y auditoría de accesos."""
import sqlite3

import pandas as pd
import streamlit as st

import auth
import database as db
from modules.common import flash, header, show_flash


def render(user):
    header("Administración y Auditoría", "Gestión de cuentas y trazabilidad de accesos")
    show_flash()
    tabs = st.tabs(["Usuarios", "Auditoría de accesos"])

    with tabs[0]:
        usuarios = db.list_users()
        st.dataframe(pd.DataFrame(usuarios).rename(columns={"id": "ID", "usuario": "Usuario", "nombre": "Nombre",
                                                           "rol": "Rol", "creado": "Creado"}),
                     use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Crear usuario")
            with st.form("form_user", clear_on_submit=True):
                u = st.text_input("Usuario *")
                n = st.text_input("Nombre completo *")
                r = st.selectbox("Rol", auth.ROLES)
                pw = st.text_input("Contraseña * (mín. 8 caracteres)", type="password")
                ok = st.form_submit_button("Crear")
            if ok:
                if not (u.strip() and n.strip()) or len(pw) < 8:
                    st.error("Complete todos los campos; la contraseña requiere al menos 8 caracteres.")
                else:
                    try:
                        db.create_user(u.strip(), n.strip(), r, pw)
                        db.log_audit(user["usuario"], user["rol"], "Usuario creado", f"{u.strip()} ({r})")
                        flash("Usuario creado.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Ese nombre de usuario ya existe.")
        with c2:
            st.subheader("Eliminar usuario")
            opts = {f"{x['usuario']} — {x['rol']}": x for x in usuarios}
            sel = opts[st.selectbox("Usuario", list(opts))]
            admins = [x for x in usuarios if x["rol"] == "Administrador"]
            if sel["id"] == user["id"]:
                st.info("No puede eliminar su propia cuenta.")
            elif sel["rol"] == "Administrador" and len(admins) <= 1:
                st.info("Debe existir al menos un administrador.")
            elif st.button("Eliminar usuario"):
                db.delete_user(sel["id"])
                db.log_audit(user["usuario"], user["rol"], "Usuario eliminado", sel["usuario"])
                flash("Usuario eliminado.")
                st.rerun()

    with tabs[1]:
        df = pd.DataFrame(db.list_audit())
        if df.empty:
            st.info("Sin registros.")
            return
        f = st.text_input("Filtrar (usuario, acción o detalle)")
        if f:
            mask = df.apply(lambda c: c.astype(str).str.contains(f, case=False, na=False)).any(axis=1)
            df = df[mask]
        df.columns = ["Fecha", "Usuario", "Rol", "Acción", "Detalle"]
        st.dataframe(df, use_container_width=True, hide_index=True)
