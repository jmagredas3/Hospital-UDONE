"""Catálogos simulados con fines educativos (CIE-10 reducido y listas de apoyo)."""

CIE10 = [
    ("A09", "Gastroenteritis y colitis de origen infeccioso"),
    ("A90", "Dengue clásico"),
    ("B34.9", "Infección viral, no especificada"),
    ("B50.9", "Paludismo por Plasmodium falciparum"),
    ("D64.9", "Anemia, no especificada"),
    ("E11.65", "Diabetes mellitus tipo 2 con hiperglucemia"),
    ("E11.9", "Diabetes mellitus tipo 2 sin complicaciones"),
    ("E66.9", "Obesidad, no especificada"),
    ("E78.5", "Hiperlipidemia, no especificada"),
    ("F41.9", "Trastorno de ansiedad, no especificado"),
    ("I10", "Hipertensión esencial (primaria)"),
    ("I20.9", "Angina de pecho, no especificada"),
    ("I50.9", "Insuficiencia cardíaca, no especificada"),
    ("I63.9", "Infarto cerebral, no especificado"),
    ("J06.9", "Infección aguda de las vías respiratorias superiores"),
    ("J18.9", "Neumonía, no especificada"),
    ("J44.9", "Enfermedad pulmonar obstructiva crónica"),
    ("J45.9", "Asma, no especificada"),
    ("K29.7", "Gastritis, no especificada"),
    ("K35.8", "Apendicitis aguda, otra y no especificada"),
    ("L03.9", "Celulitis, no especificada"),
    ("M54.5", "Lumbago no especificado"),
    ("N39.0", "Infección de vías urinarias, sitio no especificado"),
    ("O80", "Parto único espontáneo"),
    ("R07.4", "Dolor torácico, no especificado"),
    ("R10.4", "Otros dolores abdominales y los no especificados"),
    ("R50.9", "Fiebre, no especificada"),
    ("R51", "Cefalea"),
    ("S06.0", "Conmoción cerebral"),
    ("Z00.0", "Examen médico general"),
]
CIE10_OPCIONES = [f"{c} — {d}" for c, d in CIE10]

VIAS = ["Oral", "Intravenosa", "Intramuscular", "Subcutánea", "Sublingual", "Inhalatoria", "Tópica", "Rectal"]
FRECUENCIAS = ["Dosis única", "Cada 4 h", "Cada 6 h", "Cada 8 h", "Cada 12 h", "Cada 24 h", "Si es necesario (PRN)"]
GRUPOS_SANGUINEOS = ["Desconocido", "O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
TIPOS_DX = ["Presuntivo", "Definitivo"]
