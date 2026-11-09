"""Autenticación, roles y permisos (simulación educativa persistida en SQLite)."""
import streamlit as st
import database as db

ROLES = ["Administrador", "Médico", "Enfermera(o)", "Estudiante / Invitado"]

# Módulos de la barra lateral: clave -> etiqueta
MODULOS = {
    "admision": "Admisión de Pacientes",
    "triage": "Triage / Signos Vitales",
    "historia": "Historia Clínica Electrónica",
    "ordenes": "Órdenes y Prescripciones",
    "fhir": "Interoperabilidad HL7/FHIR",
    "reportes": "Reportes y Exportación PDF",
    "admin": "Administración y Auditoría",
}

PERMISOS = {
    "Administrador": {
        "admision:ver", "admision:escribir", "triage:ver", "triage:escribir", "historia:ver", "historia:escribir",
        "ordenes:ver", "ordenes:escribir", "ordenes:administrar", "fhir:ver", "fhir:tecnico", "reportes:ver",
        "admin:usuarios", "admin:auditoria",
    },
    "Médico": {
        "admision:ver", "admision:escribir", "triage:ver", "historia:ver", "historia:escribir",
        "ordenes:ver", "ordenes:escribir", "fhir:ver", "reportes:ver",
    },
    "Enfermera(o)": {
        "admision:ver", "triage:ver", "triage:escribir", "historia:ver", "ordenes:ver",
        "ordenes:administrar", "fhir:ver", "reportes:ver",
    },
    "Estudiante / Invitado": {
        "admision:ver", "triage:ver", "triage:practica", "historia:ver", "ordenes:ver", "fhir:ver", "reportes:ver",
    },
}


def can(rol, permiso):
    return permiso in PERMISOS.get(rol, set())


def modulos_visibles(rol):
    return [k for k in MODULOS if any(p.startswith(k + ":") for p in PERMISOS.get(rol, set()))]


def login(usuario, password):
    u = db.get_user(usuario.strip())
    if u and db.verify_password(password, u["password_hash"]):
        st.session_state["user"] = {"id": u["id"], "usuario": u["usuario"], "nombre": u["nombre"], "rol": u["rol"]}
        db.log_audit(u["usuario"], u["rol"], "Inicio de sesión", "Acceso exitoso")
        return True
    db.log_audit(usuario.strip() or "(vacío)", "—", "Acceso fallido", "Credenciales incorrectas")
    return False


def logout():
    u = st.session_state.get("user")
    if u:
        db.log_audit(u["usuario"], u["rol"], "Cierre de sesión", "")
    for k in list(st.session_state.keys()):
        del st.session_state[k]


def current_user():
    return st.session_state.get("user")
