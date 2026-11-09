# Sistema HCE - Hospital Universitario UDONE

Prototipo **educativo** de Sistema de Información Hospitalaria e Historia Clínica Electrónica
(Python · Streamlit · SQLite · ReportLab · HL7 FHIR R4 simplificado). Todos los datos son ficticios.

## Ejecución
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
La base `data/hce_udone.db` se crea sola la primera vez, con usuarios y 2 pacientes de prueba.

## Usuarios de demostración
| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador / Informática | admin | Admin#2026 |
| Médico | medico | Medico#2026 |
| Enfermera(o) | enfermera | Enfermera#2026 |
| Estudiante / Invitado | estudiante | Estudiante#2026 |

## Estructura
```
hce_udone/
├── app.py            # Entrada: login, sidebar, navegación por rol
├── auth.py           # Roles, permisos y sesión
├── database.py       # SQLite, PBKDF2, CRUD y datos semilla
├── catalogos.py      # CIE-10 simulado y listas
├── fhir.py           # Patient, Observation, Encounter, Condition, MedicationRequest/ServiceRequest, Bundle
├── pdf_report.py     # PDF con logotipo (ReportLab)
├── styles.py         # CSS azul / blanco / gris
├── assets/logo.png
├── data/             # SQLite (ignorado por git)
└── modules/          # admision, triage, historia, ordenes, fhir_viewer, reportes, admin
```

## Permisos por rol
- **Administrador**: todo, incluido gestión de usuarios, auditoría y vista técnica FHIR.
- **Médico**: admisión, evoluciones, diagnósticos CIE-10, órdenes y cierre de historia.
- **Enfermera(o)**: signos vitales, lectura de notas y administración de indicaciones.
- **Estudiante / Invitado**: solo lectura + registro de signos vitales en modo práctica (marcado «práctica»).

## Notas
- Los estudios (laboratorio/imagen) se exportan como `ServiceRequest`, porque `MedicationRequest` solo cubre medicamentos en FHIR R4.
- Es un prototipo docente: sin cifrado en reposo, sin HTTPS ni gestión de sesiones de producción.
