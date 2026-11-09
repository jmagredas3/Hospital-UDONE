"""Construcción de recursos HL7 FHIR R4 (simplificados) a partir de las tablas locales."""
LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"


def _ts(s):
    return (s or "").replace(" ", "T")


def _ref(rtype, rid):
    return {"reference": f"{rtype}/{rid}"}


def patient(p):
    r = {
        "resourceType": "Patient", "id": str(p["id"]), "active": True,
        "identifier": [
            {"system": "urn:udone:hce:historia-clinica", "value": p["historia_no"]},
            {"system": "urn:udone:cedula", "value": p["cedula"]},
        ],
        "name": [{"use": "official", "family": p["apellidos"], "given": p["nombres"].split()}],
        "gender": {"Masculino": "male", "Femenino": "female"}.get(p.get("sexo"), "other"),
        "birthDate": p["fecha_nac"],
    }
    if p.get("telefono"):
        r["telecom"] = [{"system": "phone", "value": p["telefono"]}]
    if p.get("direccion"):
        r["address"] = [{"use": "home", "text": p["direccion"]}]
    if p.get("contacto_emergencia"):
        r["contact"] = [{"name": {"text": p["contacto_emergencia"]}}]
    return r


def _obs(oid, pid, fecha, code, display, value, unit, ucum, cat="vital-signs"):
    return {
        "resourceType": "Observation", "id": oid, "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                  "code": cat}]}],
        "code": {"coding": [{"system": LOINC, "code": code, "display": display}], "text": display},
        "subject": _ref("Patient", pid), "effectiveDateTime": _ts(fecha),
        "valueQuantity": {"value": value, "unit": unit, "system": UCUM, "code": ucum},
    }


def observations(v):
    pid, base, f = v["paciente_id"], f"vs-{v['id']}", v["fecha"]
    out = []
    if v.get("pas") is not None:
        bp = {
            "resourceType": "Observation", "id": f"{base}-bp", "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                      "code": "vital-signs"}]}],
            "code": {"coding": [{"system": LOINC, "code": "85354-9", "display": "Blood pressure panel"}],
                     "text": "Presión arterial"},
            "subject": _ref("Patient", pid), "effectiveDateTime": _ts(f),
            "component": [
                {"code": {"coding": [{"system": LOINC, "code": "8480-6", "display": "Systolic blood pressure"}]},
                 "valueQuantity": {"value": v["pas"], "unit": "mmHg", "system": UCUM, "code": "mm[Hg]"}},
                {"code": {"coding": [{"system": LOINC, "code": "8462-4", "display": "Diastolic blood pressure"}]},
                 "valueQuantity": {"value": v["pad"], "unit": "mmHg", "system": UCUM, "code": "mm[Hg]"}},
            ],
        }
        out.append(bp)
    items = [
        ("temp", "8310-5", "Body temperature", "°C", "Cel"),
        ("fc", "8867-4", "Heart rate", "lpm", "/min"),
        ("fr", "9279-1", "Respiratory rate", "rpm", "/min"),
        ("sat", "2708-6", "Oxygen saturation in Arterial blood", "%", "%"),
        ("peso", "29463-7", "Body weight", "kg", "kg"),
        ("talla", "8302-2", "Body height", "cm", "cm"),
    ]
    for key, code, disp, unit, ucum in items:
        if v.get(key):
            out.append(_obs(f"{base}-{key}", pid, f, code, disp, v[key], unit, ucum))
    return out


def encounter(e):
    return {
        "resourceType": "Encounter", "id": str(e["id"]),
        "status": "finished" if e["estado"] == "Cerrada" else "in-progress",
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatory"},
        "subject": _ref("Patient", e["paciente_id"]),
        "participant": [{"individual": {"display": e["medico"]}}],
        "period": {"start": _ts(e["fecha"]), **({"end": _ts(e["cerrado_en"])} if e.get("cerrado_en") else {})},
        "reasonCode": [{"text": e["motivo"]}],
    }


def condition(d, enc_fecha=None):
    return {
        "resourceType": "Condition", "id": str(d["id"]),
        "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                       "code": "active"}]},
        "verificationStatus": {"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
            "code": "confirmed" if d["tipo"] == "Definitivo" else "provisional"}]},
        "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": d["codigo"],
                             "display": d["descripcion"]}], "text": d["descripcion"]},
        "subject": _ref("Patient", d["paciente_id"]),
        "encounter": _ref("Encounter", d["encuentro_id"]),
    }


def order(o):
    """Medicamento -> MedicationRequest; Estudio -> ServiceRequest (el estándar no admite estudios en MedicationRequest)."""
    estado = {"Activa": "active", "Administrada": "completed", "Suspendida": "revoked"}.get(o["estado"], "unknown")
    base = {"id": str(o["id"]), "status": estado, "intent": "order", "subject": _ref("Patient", o["paciente_id"]),
            "authoredOn": _ts(o["fecha"]), "requester": {"display": o["medico"]}}
    if o["tipo"] == "Medicamento":
        di = {"text": f"{o.get('dosis', '')} {o.get('via', '')} {o.get('frecuencia', '')}".strip(),
              "route": {"text": o.get("via", "")}}
        if o.get("indicaciones"):
            di["patientInstruction"] = o["indicaciones"]
        return {"resourceType": "MedicationRequest", **base,
                "medicationCodeableConcept": {"text": o["descripcion"]}, "dosageInstruction": [di]}
    r = {"resourceType": "ServiceRequest", **base, "code": {"text": o["descripcion"]}}
    if o.get("indicaciones"):
        r["patientInstruction"] = o["indicaciones"]
    return r


def resources_for(p, vitals, encounters, dxs, orders):
    return {
        "Patient": patient(p),
        "Observation": [x for v in vitals for x in observations(v)],
        "Encounter": [encounter(e) for e in encounters],
        "Condition": [condition(d) for d in dxs],
        "MedicationRequest / ServiceRequest": [order(o) for o in orders],
    }


def bundle(p, vitals, encounters, dxs, orders):
    entries = [patient(p)]
    entries += [x for v in vitals for x in observations(v)]
    entries += [encounter(e) for e in encounters] + [condition(d) for d in dxs] + [order(o) for o in orders]
    return {"resourceType": "Bundle", "type": "collection",
            "entry": [{"fullUrl": f"urn:udone:{r['resourceType']}/{r['id']}", "resource": r} for r in entries]}
