"""Sistema HCE - Hospital Universitario UDONE (prototipo educativo).
Ejecutar:  streamlit run app.py
"""
import os

import streamlit as st

import auth
import database as db
import styles
from modules import admin, admision, fhir_viewer, historia, ordenes, reportes, triage

st.set_page_config(page_title="Sistema HCE - Hospital Universitario UDONE",
                   page_icon=styles.LOGO_PATH if os.path.exists(styles.LOGO_PATH) else None, layout="wide")


@st.cache_resource
def _init():
    db.init_db()
    return True


_init()
styles.inject_css()

RENDERERS = {"admision": admision.render, "triage": triage.render, "historia": historia.render,
             "ordenes": ordenes.render, "fhir": fhir_viewer.render, "reportes": reportes.render,
             "admin": admin.render}


def login_screen():
    _, c, _ = st.columns([1, 1.3, 1])
    with c:
        st.markdown(f'<div class="login-card">{styles.logo_html(130)}'
                    '<div class="login-title">Sistema HCE</div>'
                    '<div class="login-sub">Hospital Universitario UDONE · Historia Clínica Electrónica</div></div>',
                    unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            ok = st.form_submit_button("Iniciar sesión", use_container_width=True)
        if ok:
            if auth.login(u, p):
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
        with st.expander("Credenciales de demostración"):
            st.markdown("| Rol | Usuario | Contraseña |\n|---|---|---|\n"
                        "| Administrador | `admin` | `Admin#2026` |\n| Médico | `medico` | `Medico#2026` |\n"
                        "| Enfermera(o) | `enfermera` | `Enfermera#2026` |\n"
                        "| Estudiante / Invitado | `estudiante` | `Estudiante#2026` |")
        st.markdown('<div class="edu-note">Prototipo con fines educativos. Todos los datos son ficticios.</div>',
                    unsafe_allow_html=True)


def main_app(user):
    with st.sidebar:
        st.markdown(f'<div class="sb-brand">{styles.logo_html(110)}'
                    '<div class="t1">Sistema HCE</div><div class="t2">Hospital Universitario UDONE</div></div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="sb-user"><b>{user["nombre"]}</b><br>{user["rol"]}</div>', unsafe_allow_html=True)
        visibles = auth.modulos_visibles(user["rol"])
        clave = st.radio("Navegación", visibles, format_func=lambda k: auth.MODULOS[k], label_visibility="collapsed")
        st.divider()
        if st.button("Cerrar sesión", use_container_width=True):
            auth.logout()
            st.rerun()
        st.caption("Uso educativo · datos ficticios")

    if st.session_state.get("_modulo_log") != clave:
        db.log_audit(user["usuario"], user["rol"], "Acceso a módulo", auth.MODULOS[clave])
        st.session_state["_modulo_log"] = clave
    RENDERERS[clave](user)


usuario = auth.current_user()
if usuario is None:
    login_screen()
else:
    main_app(usuario)
