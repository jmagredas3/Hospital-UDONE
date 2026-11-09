"""Capa de datos (SQLite) y datos semilla del Sistema HCE - Hospital Universitario UDONE."""
import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "hce_udone.db")


def now(delta_hours=0):
    return (datetime.now() + timedelta(hours=delta_hours)).strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- seguridad
def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 120_000)
    return f"{salt}${dk.hex()}"


def verify_password(password, stored):
    salt, _ = stored.split("$")
    return hmac.compare_digest(hash_password(password, salt), stored)


# ---------------------------------------------------------------- conexión
@contextmanager
def conn_ctx():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def query(sql, params=()):
    with conn_ctx() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def execute(sql, params=()):
    with conn_ctx() as c:
        return c.execute(sql, params).lastrowid


SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios(
  id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL,
  rol TEXT NOT NULL, password_hash TEXT NOT NULL, creado TEXT);
CREATE TABLE IF NOT EXISTS auditoria(
  id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, usuario TEXT, rol TEXT, accion TEXT, detalle TEXT);
CREATE TABLE IF NOT EXISTS pacientes(
  id INTEGER PRIMARY KEY AUTOINCREMENT, historia_no TEXT DEFAULT '', cedula TEXT UNIQUE NOT NULL,
  nombres TEXT NOT NULL, apellidos TEXT NOT NULL, fecha_nac TEXT NOT NULL, sexo TEXT,
  grupo_sanguineo TEXT, telefono TEXT, direccion TEXT, contacto_emergencia TEXT,
  antecedentes TEXT, alergias TEXT, creado TEXT);
CREATE TABLE IF NOT EXISTS signos_vitales(
  id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
  fecha TEXT, pas INTEGER, pad INTEGER, temp REAL, fc INTEGER, fr INTEGER, sat INTEGER,
  peso REAL, talla REAL, nota TEXT, registrado_por TEXT);
CREATE TABLE IF NOT EXISTS encuentros(
  id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
  fecha TEXT, motivo TEXT, enfermedad_actual TEXT, examen_fisico TEXT, plan TEXT,
  medico TEXT, estado TEXT DEFAULT 'Abierta', cerrado_en TEXT);
CREATE TABLE IF NOT EXISTS diagnosticos(
  id INTEGER PRIMARY KEY AUTOINCREMENT, encuentro_id INTEGER NOT NULL REFERENCES encuentros(id),
  paciente_id INTEGER NOT NULL, codigo TEXT, descripcion TEXT, tipo TEXT);
CREATE TABLE IF NOT EXISTS ordenes(
  id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
  fecha TEXT, tipo TEXT, descripcion TEXT, dosis TEXT, via TEXT, frecuencia TEXT, duracion TEXT,
  indicaciones TEXT, estado TEXT DEFAULT 'Activa', medico TEXT, administrada_por TEXT, administrada_en TEXT);
"""


def init_db():
    with conn_ctx() as c:
        c.executescript(SCHEMA)
        vacio = c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0
    if vacio:
        seed()


# ---------------------------------------------------------------- usuarios / auditoría
def get_user(usuario):
    r = query("SELECT * FROM usuarios WHERE usuario=?", (usuario,))
    return r[0] if r else None


def list_users():
    return query("SELECT id, usuario, nombre, rol, creado FROM usuarios ORDER BY id")


def create_user(usuario, nombre, rol, password):
    return execute(
        "INSERT INTO usuarios(usuario,nombre,rol,password_hash,creado) VALUES (?,?,?,?,?)",
        (usuario, nombre, rol, hash_password(password), now()),
    )


def delete_user(user_id):
    execute("DELETE FROM usuarios WHERE id=?", (user_id,))


def log_audit(usuario, rol, accion, detalle=""):
    execute("INSERT INTO auditoria(fecha,usuario,rol,accion,detalle) VALUES (?,?,?,?,?)",
            (now(), usuario, rol, accion, detalle))


def list_audit(limit=500):
    return query("SELECT fecha, usuario, rol, accion, detalle FROM auditoria ORDER BY id DESC LIMIT ?", (limit,))


# ---------------------------------------------------------------- pacientes
PAC_COLS = ["cedula", "nombres", "apellidos", "fecha_nac", "sexo", "grupo_sanguineo", "telefono",
            "direccion", "contacto_emergencia", "antecedentes", "alergias"]


def add_patient(d):
    with conn_ctx() as c:
        cur = c.execute(
            f"INSERT INTO pacientes ({','.join(PAC_COLS)}, creado) VALUES ({','.join('?' * len(PAC_COLS))},?)",
            [d.get(k, "") for k in PAC_COLS] + [now()])
        pid = cur.lastrowid
        c.execute("UPDATE pacientes SET historia_no=? WHERE id=?", (f"HC-{pid:06d}", pid))
    return pid


def list_patients(search=""):
    like = f"%{search.strip()}%"
    return query("SELECT * FROM pacientes WHERE nombres LIKE ? OR apellidos LIKE ? OR cedula LIKE ? "
                 "OR historia_no LIKE ? ORDER BY apellidos, nombres", (like, like, like, like))


def get_patient(pid):
    r = query("SELECT * FROM pacientes WHERE id=?", (pid,))
    return r[0] if r else None


def update_background(pid, antecedentes, alergias):
    execute("UPDATE pacientes SET antecedentes=?, alergias=? WHERE id=?", (antecedentes, alergias, pid))


# ---------------------------------------------------------------- signos vitales
def add_vitals(d):
    return execute(
        "INSERT INTO signos_vitales(paciente_id,fecha,pas,pad,temp,fc,fr,sat,peso,talla,nota,registrado_por) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (d["paciente_id"], d.get("fecha") or now(), d["pas"], d["pad"], d["temp"], d["fc"], d["fr"],
         d["sat"], d.get("peso"), d.get("talla"), d.get("nota", ""), d["registrado_por"]))


def list_vitals(pid):
    return query("SELECT * FROM signos_vitales WHERE paciente_id=? ORDER BY fecha DESC, id DESC", (pid,))


# ---------------------------------------------------------------- encuentros / diagnósticos
def add_encounter(d, dxs):
    with conn_ctx() as c:
        cur = c.execute(
            "INSERT INTO encuentros(paciente_id,fecha,motivo,enfermedad_actual,examen_fisico,plan,medico,estado) "
            "VALUES (?,?,?,?,?,?,?, 'Abierta')",
            (d["paciente_id"], d.get("fecha") or now(), d["motivo"], d.get("enfermedad_actual", ""),
             d.get("examen_fisico", ""), d.get("plan", ""), d["medico"]))
        eid = cur.lastrowid
        for cod, desc, tipo in dxs:
            c.execute("INSERT INTO diagnosticos(encuentro_id,paciente_id,codigo,descripcion,tipo) VALUES (?,?,?,?,?)",
                      (eid, d["paciente_id"], cod, desc, tipo))
    return eid


def add_diagnosis(eid, pid, cod, desc, tipo):
    execute("INSERT INTO diagnosticos(encuentro_id,paciente_id,codigo,descripcion,tipo) VALUES (?,?,?,?,?)",
            (eid, pid, cod, desc, tipo))


def list_encounters(pid):
    return query("SELECT * FROM encuentros WHERE paciente_id=? ORDER BY fecha DESC, id DESC", (pid,))


def list_diagnoses(pid):
    return query("SELECT * FROM diagnosticos WHERE paciente_id=? ORDER BY id", (pid,))


def close_encounter(eid):
    execute("UPDATE encuentros SET estado='Cerrada', cerrado_en=? WHERE id=? AND estado='Abierta'", (now(), eid))


# ---------------------------------------------------------------- órdenes
def add_order(d):
    return execute(
        "INSERT INTO ordenes(paciente_id,fecha,tipo,descripcion,dosis,via,frecuencia,duracion,indicaciones,estado,medico) "
        "VALUES (?,?,?,?,?,?,?,?,?, 'Activa', ?)",
        (d["paciente_id"], now(), d["tipo"], d["descripcion"], d.get("dosis", ""), d.get("via", ""),
         d.get("frecuencia", ""), d.get("duracion", ""), d.get("indicaciones", ""), d["medico"]))


def list_orders(pid):
    return query("SELECT * FROM ordenes WHERE paciente_id=? ORDER BY fecha DESC, id DESC", (pid,))


def set_order_status(oid, estado, usuario=None):
    if estado == "Administrada":
        execute("UPDATE ordenes SET estado=?, administrada_por=?, administrada_en=? WHERE id=?",
                (estado, usuario, now(), oid))
    else:
        execute("UPDATE ordenes SET estado=? WHERE id=?", (estado, oid))


# ---------------------------------------------------------------- datos semilla
def seed():
    """Usuarios por rol y 2 pacientes ficticios. TODOS LOS DATOS SON FICTICIOS."""
    for u, n, r, p in [
        ("admin", "Ing. Carlos Rivas (Informática)", "Administrador", "Admin#2026"),
        ("medico", "Dra. Andrea Pérez", "Médico", "Medico#2026"),
        ("enfermera", "Lic. Luis García", "Enfermera(o)", "Enfermera#2026"),
        ("estudiante", "Estudiante de Medicina (Práctica)", "Estudiante / Invitado", "Estudiante#2026"),
    ]:
        create_user(u, n, r, p)

    p1 = add_patient(dict(
        cedula="V-18456321", nombres="María Fernanda", apellidos="Rodríguez Salazar", fecha_nac="1985-03-14",
        sexo="Femenino", grupo_sanguineo="O+", telefono="0414-5550101", direccion="Av. Perimetral, Cumaná, Sucre",
        contacto_emergencia="Pedro Rodríguez (hermano) 0412-5550102",
        antecedentes="Hipertensión arterial desde 2019. Madre con diabetes mellitus tipo 2. Apendicectomía en 2008.",
        alergias="Penicilina (rash cutáneo)"))
    p2 = add_patient(dict(
        cedula="V-7123456", nombres="José Luis", apellidos="Martínez Brito", fecha_nac="1962-09-02",
        sexo="Masculino", grupo_sanguineo="A+", telefono="0416-5550202", direccion="Calle Sucre, Cumanacoa, Sucre",
        contacto_emergencia="Rosa Brito (esposa) 0416-5550203",
        antecedentes="Diabetes mellitus tipo 2 desde 2012. Dislipidemia. Extabaquismo (20 paq/año).",
        alergias="Ninguna conocida"))

    add_vitals(dict(paciente_id=p1, fecha=now(-30), pas=148, pad=94, temp=36.7, fc=88, fr=18, sat=97,
                    peso=68.0, talla=164, nota="Cefalea occipital leve.", registrado_por="Lic. Luis García"))
    add_vitals(dict(paciente_id=p1, fecha=now(-2), pas=142, pad=90, temp=36.6, fc=84, fr=17, sat=98,
                    peso=68.0, talla=164, nota="Control posterior a evaluación.", registrado_por="Lic. Luis García"))
    add_vitals(dict(paciente_id=p2, fecha=now(-26), pas=132, pad=82, temp=37.0, fc=78, fr=16, sat=96,
                    peso=84.5, talla=172, nota="Glicemia capilar 240 mg/dL.", registrado_por="Lic. Luis García"))

    e1 = add_encounter(dict(
        paciente_id=p1, fecha=now(-29), medico="Dra. Andrea Pérez",
        motivo="Cefalea y cifras tensionales elevadas",
        enfermedad_actual="Paciente femenina de 41 años, hipertensa, con cefalea occipital de 3 días de evolución, "
                          "sin déficit neurológico. Refiere omisión del tratamiento antihipertensivo.",
        examen_fisico="TA 148/94 mmHg, FC 88 lpm. Alerta, orientada. Ruidos cardíacos rítmicos, sin soplos. "
                      "Fondo de ojo sin alteraciones. Sin focalización neurológica.",
        plan="Reiniciar antihipertensivo, dieta hiposódica, control de TA en 1 semana, educación sobre adherencia."),
        [("I10", "Hipertensión esencial (primaria)", "Definitivo"), ("R51", "Cefalea", "Presuntivo")])
    e2 = add_encounter(dict(
        paciente_id=p2, fecha=now(-25), medico="Dra. Andrea Pérez",
        motivo="Poliuria y polidipsia", 
        enfermedad_actual="Paciente masculino de 64 años, diabético tipo 2, con poliuria y polidipsia de 1 semana. "
                          "Reconoce transgresiones dietéticas.",
        examen_fisico="TA 132/82 mmHg, FC 78 lpm, IMC 28,6. Mucosas ligeramente secas. Pulsos pedios presentes. "
                      "Sensibilidad en pies conservada.",
        plan="Ajuste de hipoglucemiantes, solicitar HbA1c y perfil lipídico, nutrición, control en 2 semanas."),
        [("E11.65", "Diabetes mellitus tipo 2 con hiperglucemia", "Definitivo")])
    close_encounter(e2)

    add_order(dict(paciente_id=p1, tipo="Medicamento", descripcion="Losartán 50 mg tabletas", dosis="50 mg",
                   via="Oral", frecuencia="Cada 24 h", duracion="30 días",
                   indicaciones="Tomar en la mañana. Controlar TA en casa.", medico="Dra. Andrea Pérez"))
    add_order(dict(paciente_id=p1, tipo="Estudio", descripcion="Electrocardiograma de 12 derivaciones",
                   indicaciones="Realizar hoy.", medico="Dra. Andrea Pérez"))
    add_order(dict(paciente_id=p2, tipo="Medicamento", descripcion="Metformina 850 mg tabletas", dosis="850 mg",
                   via="Oral", frecuencia="Cada 12 h", duracion="30 días",
                   indicaciones="Administrar con las comidas.", medico="Dra. Andrea Pérez"))
    add_order(dict(paciente_id=p2, tipo="Estudio", descripcion="Hemoglobina glucosilada (HbA1c) y perfil lipídico",
                   indicaciones="Ayuno de 8 horas.", medico="Dra. Andrea Pérez"))
    log_audit("sistema", "Sistema", "Inicialización", "Base de datos creada con datos semilla ficticios")
