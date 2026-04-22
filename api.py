from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from models import (
    db, Vacuna, Diagnostico, Receta, Prevencion,
    Examen, Consulta, Usuario, Mascota
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import os
import json
from datetime import datetime

api = Blueprint('api', __name__)
CORS(api)

UPLOAD_FOLDER = "uploads/documentos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================
# UTILIDADES
# ============================================================

def save_file(file):
    if not file:
        return None
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filename


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except:
        return None


def append_document(existing, new_file):
    """
    Manejo profesional de documentos:
    - Si no hay archivo nuevo → devolver existing
    - Si existing es None → devolver string
    - Si existing es string → convertir a lista y agregar
    - Si existing es lista → agregar al final
    """
    if not new_file:
        return existing

    if not existing:
        return new_file

    try:
        parsed = json.loads(existing)
        if isinstance(parsed, list):
            parsed.append(new_file)
            return json.dumps(parsed)
        else:
            return json.dumps([parsed, new_file])
    except:
        return json.dumps([existing, new_file])


def load_docs(value):
    """
    Convierte campo documento (string o JSON) en lista de nombres de archivo.
    """
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except:
        return [value]


# ============================================================
# REGISTRO
# ============================================================

@api.route('/register', methods=['POST'])
def api_register():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "No se envió JSON"}), 400

    nombre = data.get("nombre")
    apellido = data.get("apellido", "")
    email = data.get("email")
    password = data.get("password")

    if not nombre or not email or not password:
        return jsonify({"success": False, "message": "Faltan campos obligatorios"}), 400

    if Usuario.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "El correo ya está registrado"}), 400

    nuevo = Usuario(
        nombre=nombre,
        apellido=apellido,
        email=email,
        password=generate_password_hash(password),
        foto=""
    )

    db.session.add(nuevo)
    db.session.commit()

    return jsonify({"success": True, "message": "Registro exitoso"}), 201


# ============================================================
# LOGIN
# ============================================================

@api.route('/login', methods=['POST'])
def api_login():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "No se envió JSON"}), 400

    email = data.get("email")
    password = data.get("password")

    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario or not check_password_hash(usuario.password, password):
        return jsonify({"success": False, "message": "Credenciales incorrectas"}), 401

    return jsonify({
        "success": True,
        "user_id": usuario.id,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "foto": usuario.foto
    }), 200


# ============================================================
# OBTENER USUARIO
# ============================================================

@api.route('/usuario/<int:user_id>', methods=['GET'])
def obtener_usuario(user_id):
    usuario = Usuario.query.get(user_id)

    if not usuario:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404

    return jsonify({
        "success": True,
        "user_id": usuario.id,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "foto": usuario.foto
    }), 200


# ============================================================
# MASCOTAS
# ============================================================

@api.route('/mascotas', methods=['GET'])
def obtener_mascotas():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"success": False, "message": "Falta user_id"}), 400

    mascotas = Mascota.query.filter_by(user_id=user_id).all()

    return jsonify({
        "success": True,
        "mascotas": [m.to_dict() for m in mascotas]
    }), 200


@api.route('/mascotas', methods=['POST'])
def crear_mascota():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "No se envió JSON"}), 400

    nueva = Mascota(
        nombre=data.get("nombre"),
        especie=data.get("especie"),
        raza=data.get("raza"),
        fecha_nacimiento=parse_date(data.get("fecha_nacimiento")),
        peso=data.get("peso"),
        microchip=data.get("microchip"),
        castrado=data.get("castrado", False),
        foto=data.get("foto"),
        user_id=data.get("user_id")
    )

    db.session.add(nueva)
    db.session.commit()

    return jsonify({"success": True, "id": nueva.id}), 201


@api.route('/mascotas/<int:mascota_id>', methods=['PUT'])
def actualizar_mascota(mascota_id):
    data = request.get_json()

    mascota = Mascota.query.get(mascota_id)
    if not mascota:
        return jsonify({"success": False, "message": "Mascota no encontrada"}), 404

    mascota.nombre = data.get("nombre", mascota.nombre)
    mascota.especie = data.get("especie", mascota.especie)
    mascota.raza = data.get("raza", mascota.raza)
    mascota.fecha_nacimiento = parse_date(data.get("fecha_nacimiento")) or mascota.fecha_nacimiento
    mascota.peso = data.get("peso", mascota.peso)
    mascota.microchip = data.get("microchip", mascota.microchip)
    mascota.castrado = data.get("castrado", mascota.castrado)
    mascota.foto = data.get("foto", mascota.foto)

    db.session.commit()

    return jsonify({"success": True, "message": "Mascota actualizada correctamente"}), 200


# ============================================================
# VACUNAS
# ============================================================

@api.route('/vacunas/<int:mascota_id>', methods=['GET'])
def obtener_vacunas(mascota_id):
    vacunas = Vacuna.query.filter_by(mascota_id=mascota_id).all()
    return jsonify([v.to_dict() for v in vacunas]), 200


@api.route('/vacunas', methods=['POST'])
def crear_vacuna():
    try:
        nombre = request.form.get("nombre")
        marca = request.form.get("marca")
        tarjeta_profesional = request.form.get("tarjeta_profesional")
        cantidad_dosis = request.form.get("cantidad_dosis")
        numero_identificacion = request.form.get("numero_identificacion")
        fecha_fabricacion = parse_date(request.form.get("fecha_fabricacion"))
        fecha_vencimiento = parse_date(request.form.get("fecha_vencimiento"))
        fecha_aplicacion = parse_date(request.form.get("fecha_aplicacion"))
        fecha_refuerzo = parse_date(request.form.get("fecha_refuerzo"))
        mascota_id = request.form.get("mascota_id")

        documento = save_file(request.files.get("documento"))

        nueva = Vacuna(
            nombre=nombre,
            marca=marca,
            tarjeta_profesional=tarjeta_profesional,
            cantidad_dosis=cantidad_dosis,
            numero_identificacion=numero_identificacion,
            fecha_fabricacion=fecha_fabricacion,
            fecha_vencimiento=fecha_vencimiento,
            fecha_aplicacion=fecha_aplicacion,
            fecha_refuerzo=fecha_refuerzo,
            documento=json.dumps([documento]) if documento else None,
            mascota_id=mascota_id
        )

        db.session.add(nueva)
        db.session.commit()

        return jsonify({"success": True, "message": "Vacuna registrada correctamente"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route('/vacunas/<int:vacuna_id>', methods=['PUT'])
def actualizar_vacuna(vacuna_id):
    try:
        vacuna = Vacuna.query.get(vacuna_id)
        if not vacuna:
            return jsonify({"success": False, "message": "Vacuna no encontrada"}), 404

        vacuna.nombre = request.form.get("nombre", vacuna.nombre)
        vacuna.marca = request.form.get("marca", vacuna.marca)
        vacuna.tarjeta_profesional = request.form.get("tarjeta_profesional", vacuna.tarjeta_profesional)
        vacuna.cantidad_dosis = request.form.get("cantidad_dosis", vacuna.cantidad_dosis)
        vacuna.numero_identificacion = request.form.get("numero_identificacion", vacuna.numero_identificacion)
        vacuna.fecha_aplicacion = parse_date(request.form.get("fecha_aplicacion")) or vacuna.fecha_aplicacion
        vacuna.fecha_refuerzo = parse_date(request.form.get("fecha_refuerzo")) or vacuna.fecha_refuerzo

        new_doc = save_file(request.files.get("documento"))

        docs = []
        if vacuna.documento:
            try:
                docs = json.loads(vacuna.documento)
            except:
                docs = [vacuna.documento]

        if new_doc:
            if len(docs) < 5:
                docs.append(new_doc)

        vacuna.documento = json.dumps(docs)

        db.session.commit()

        return jsonify({"success": True, "message": "Vacuna actualizada correctamente"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route('/vacunas/<int:vacuna_id>/documento/<string:filename>', methods=['DELETE'])
def eliminar_documento_vacuna(vacuna_id, filename):
    vacuna = Vacuna.query.get(vacuna_id)
    if not vacuna:
        return jsonify({"success": False, "message": "Vacuna no encontrada"}), 404

    docs = load_docs(vacuna.documento)

    if filename not in docs:
        return jsonify({"success": False, "message": "Documento no encontrado"}), 404

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    docs.remove(filename)
    vacuna.documento = json.dumps(docs) if docs else None

    db.session.commit()

    return jsonify({"success": True, "message": "Documento eliminado"}), 200


@api.route('/vacunas/<int:vacuna_id>', methods=['DELETE'])
def eliminar_vacuna(vacuna_id):
    vacuna = Vacuna.query.get(vacuna_id)
    if not vacuna:
        return jsonify({"success": False, "message": "Vacuna no encontrada"}), 404

    if vacuna.documento:
        docs = load_docs(vacuna.documento)
        for f in docs:
            filepath = os.path.join(UPLOAD_FOLDER, f)
            if os.path.exists(filepath):
                os.remove(filepath)

    db.session.delete(vacuna)
    db.session.commit()

    return jsonify({"success": True, "message": "Vacuna eliminada correctamente"}), 200


# ============================================================
# DIAGNÓSTICOS
# ============================================================

@api.route('/diagnosticos/<int:mascota_id>', methods=['GET'])
def obtener_diagnosticos(mascota_id):
    diagnosticos = Diagnostico.query.filter_by(mascota_id=mascota_id).all()
    return jsonify([d.to_dict() for d in diagnosticos]), 200


@api.route('/diagnosticos', methods=['POST'])
def crear_diagnostico():
    try:
        titulo = request.form.get("titulo")
        descripcion = request.form.get("descripcion")
        fecha = parse_date(request.form.get("fecha"))
        diagnostico_confirmado = request.form.get("diagnostico_confirmado") == "1"
        sospecha = request.form.get("sospecha")
        mascota_id = request.form.get("mascota_id")
        documento = save_file(request.files.get("documento"))

        nuevo = Diagnostico(
            titulo=titulo,
            descripcion=descripcion,
            fecha=fecha,
            diagnostico_confirmado=diagnostico_confirmado,
            sospecha=sospecha,
            documento=documento,
            mascota_id=mascota_id
        )

        db.session.add(nuevo)
        db.session.commit()

        return jsonify({"success": True, "message": "Diagnóstico registrado correctamente"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route('/diagnosticos/<int:diag_id>', methods=['PUT'])
def actualizar_diagnostico(diag_id):
    try:
        diag = Diagnostico.query.get(diag_id)
        if not diag:
            return jsonify({"success": False, "message": "Diagnóstico no encontrado"}), 404

        diag.titulo = request.form.get("titulo", diag.titulo)
        diag.descripcion = request.form.get("descripcion", diag.descripcion)
        diag.fecha = parse_date(request.form.get("fecha")) or diag.fecha
        diag.diagnostico_confirmado = request.form.get("diagnostico_confirmado", str(diag.diagnostico_confirmado)) == "1"
        diag.sospecha = request.form.get("sospecha", diag.sospecha)

        new_doc = save_file(request.files.get("documento"))
        diag.documento = append_document(diag.documento, new_doc)

        db.session.commit()

        return jsonify({"success": True, "message": "Diagnóstico actualizado correctamente"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route('/diagnosticos/<int:diag_id>/documento/<string:filename>', methods=['DELETE'])
def eliminar_documento_diagnostico(diag_id, filename):
    diag = Diagnostico.query.get(diag_id)
    if not diag:
        return jsonify({"success": False, "message": "Diagnóstico no encontrado"}), 404

    docs = load_docs(diag.documento)

    if filename not in docs:
        return jsonify({"success": False, "message": "Documento no encontrado"}), 404

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    docs.remove(filename)
    diag.documento = json.dumps(docs) if docs else None

    db.session.commit()

    return jsonify({"success": True, "message": "Documento eliminado"}), 200


@api.route('/diagnosticos/<int:diag_id>', methods=['DELETE'])
def eliminar_diagnostico(diag_id):
    diag = Diagnostico.query.get(diag_id)
    if not diag:
        return jsonify({"success": False, "message": "Diagnóstico no encontrado"}), 404

    if diag.documento:
        docs = load_docs(diag.documento)
        for f in docs:
            filepath = os.path.join(UPLOAD_FOLDER, f)
            if os.path.exists(filepath):
                os.remove(filepath)

    db.session.delete(diag)
    db.session.commit()

    return jsonify({"success": True, "message": "Diagnóstico eliminado correctamente"}), 200


# ============================================================
# RECETAS
# ============================================================

@api.route('/recetas/<int:mascota_id>', methods=['GET'])
def obtener_recetas(mascota_id):
    recetas = Receta.query.filter_by(mascota_id=mascota_id).all()
    return jsonify([r.to_dict() for r in recetas]), 200


@api.route('/recetas', methods=['POST'])
def crear_receta():
    try:
        medicamento_veterinario = request.form.get("medicamento_veterinario") == "true"
        medicamento = request.form.get("medicamento")
        cantidad = request.form.get("cantidad")
        via_administracion = request.form.get("via_administracion")
        instrucciones = request.form.get("instrucciones")
        observaciones = request.form.get("observaciones")
        fecha = parse_date(request.form.get("fecha"))
        mascota_id = request.form.get("mascota_id")
        documento = save_file(request.files.get("documento"))

        nueva = Receta(
            medicamento_veterinario=medicamento_veterinario,
            medicamento=medicamento,
            cantidad=cantidad,
            via_administracion=via_administracion,
            instrucciones=instrucciones,
            observaciones=observaciones,
            fecha=fecha,
            documento=documento,
            mascota_id=mascota_id
        )

        db.session.add(nueva)
        db.session.commit()

        return jsonify({"success": True, "message": "Receta registrada correctamente"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route('/recetas/<int:receta_id>', methods=['PUT'])
def actualizar_receta(receta_id):
    try:
        receta = Receta.query.get(receta_id)
        if not receta:
            return jsonify({"success": False, "message": "Receta no encontrada"}), 404

        receta.medicamento_veterinario = request.form.get("medicamento_veterinario", str(receta.medicamento_veterinario)) == "1"
        receta.medicamento = request.form.get("medicamento", receta.medicamento)
        receta.cantidad = request.form.get("cantidad", receta.cantidad)
        receta.via_administracion = request.form.get("via_administracion", receta.via_administracion)
        receta.instrucciones = request.form.get("instrucciones", receta.instrucciones)
        receta.observaciones = request.form.get("observaciones", receta.observaciones)
        receta.fecha = parse_date(request.form.get("fecha")) or receta.fecha

        new_doc = save_file(request.files.get("documento"))
        receta.documento = append_document(receta.documento, new_doc)

        db.session.commit()

        return jsonify({"success": True, "message": "Receta actualizada correctamente"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route('/recetas/<int:receta_id>/documento/<string:filename>', methods=['DELETE'])
def eliminar_documento_receta(receta_id, filename):
    receta = Receta.query.get(receta_id)
    if not receta:
        return jsonify({"success": False, "message": "Receta no encontrada"}), 404

    docs = load_docs(receta.documento)

    if filename not in docs:
        return jsonify({"success": False, "message": "Documento no encontrado"}), 404

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    docs.remove(filename)
    receta.documento = json.dumps(docs) if docs else None

    db.session.commit()

    return jsonify({"success": True, "message": "Documento eliminado"}), 200


@api.route('/recetas/<int:receta_id>', methods=['DELETE'])
def eliminar_receta(receta_id):
    receta = Receta.query.get(receta_id)
    if not receta:
        return jsonify({"success": False, "message": "Receta no encontrada"}), 404

    if receta.documento:
        docs = load_docs(receta.documento)
        for f in docs:
            filepath = os.path.join(UPLOAD_FOLDER, f)
            if os.path.exists(filepath):
                os.remove(filepath)

    db.session.delete(receta)
    db.session.commit()

    return jsonify({"success": True, "message": "Receta eliminada correctamente"}), 200


# ============================================================
# PREVENCIONES
# ============================================================

@api.route('/prevenciones/<int:mascota_id>', methods=['GET'])
def obtener_prevenciones(mascota_id):
    prev = Prevencion.query.filter_by(mascota_id=mascota_id).all()
    return jsonify({
        "success": True,
        "prevenciones": [p.to_dict() for p in prev]
    }), 200


@api.route('/prevenciones', methods=['POST'])
def crear_prevencion():
    try:
        tipo = request.form.get("tipo")
        descripcion = request.form.get("descripcion")
        fecha = parse_date(request.form.get("fecha"))
        mascota_id = request.form.get("mascota_id")
        documento = save_file(request.files.get("documento"))

        nueva = Prevencion(
            tipo=tipo,
            descripcion=descripcion,
            fecha=fecha,
            documento=documento,
            mascota_id=mascota_id
        )

        db.session.add(nueva)
        db.session.commit()

        return jsonify({"success": True, "message": "Prevención registrada correctamente"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route('/prevenciones/<int:prev_id>', methods=['PUT'])
def actualizar_prevencion(prev_id):
    try:
        prev = Prevencion.query.get(prev_id)
        if not prev:
            return jsonify({"success": False, "message": "Prevención no encontrada"}), 404

        prev.tipo = request.form.get("tipo", prev.tipo)
        prev.descripcion = request.form.get("descripcion", prev.descripcion)
        prev.fecha = parse_date(request.form.get("fecha")) or prev.fecha
        prev.mascota_id = request.form.get("mascota_id", prev.mascota_id)

        new_doc = save_file(request.files.get("documento"))
        prev.documento = append_document(prev.documento, new_doc)

        db.session.commit()

        return jsonify({"success": True, "message": "Prevención actualizada correctamente"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route('/prevenciones/<int:prev_id>/documento/<string:filename>', methods=['DELETE'])
def eliminar_documento_prevencion(prev_id, filename):
    prev = Prevencion.query.get(prev_id)
    if not prev:
        return jsonify({"success": False, "message": "Prevención no encontrada"}), 404

    docs = load_docs(prev.documento)

    if filename not in docs:
        return jsonify({"success": False, "message": "Documento no encontrado"}), 404

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    docs.remove(filename)
    prev.documento = json.dumps(docs) if docs else None

    db.session.commit()

    return jsonify({"success": True, "message": "Documento eliminado"}), 200


@api.route('/prevenciones/<int:prev_id>', methods=['DELETE'])
def eliminar_prevencion(prev_id):
    prev = Prevencion.query.get(prev_id)
    if not prev:
        return jsonify({"success": False, "message": "Prevención no encontrada"}), 404

    if prev.documento:
        docs = load_docs(prev.documento)
        for f in docs:
            filepath = os.path.join(UPLOAD_FOLDER, f)
            if os.path.exists(filepath):
                os.remove(filepath)

    db.session.delete(prev)
    db.session.commit()

    return jsonify({"success": True, "message": "Prevención eliminada correctamente"}), 200


# ============================================================
# EXÁMENES
# ============================================================

@api.route('/examenes/<int:mascota_id>', methods=['GET'])
def obtener_examenes(mascota_id):
    examenes = Examen.query.filter_by(mascota_id=mascota_id).all()
    return jsonify([e.to_dict() for e in examenes]), 200


@api.route('/examenes', methods=['POST'])
def crear_examen():
    try:
        tipo_examen = request.form.get("tipo_examen")
        fecha = parse_date(request.form.get("fecha"))
        detalles = request.form.get("detalles")
        mascota_id = request.form.get("mascota_id")
        documento = save_file(request.files.get("documento"))

        nuevo = Examen(
            tipo_examen=tipo_examen,
            fecha=fecha,
            detalles=detalles,
            documento=documento,
            mascota_id=mascota_id
        )

        db.session.add(nuevo)
        db.session.commit()

        return jsonify({"success": True, "id": nuevo.id, "message": "Examen registrado correctamente"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route('/examenes/<int:examen_id>', methods=['PUT'])
def actualizar_examen(examen_id):
    try:
        examen = Examen.query.get(examen_id)
        if not examen:
            return jsonify({"success": False, "message": "Examen no encontrado"}), 404

        examen.tipo_examen = request.form.get("tipo_examen", examen.tipo_examen)
        examen.detalles = request.form.get("detalles", examen.detalles)
        examen.fecha = parse_date(request.form.get("fecha")) or examen.fecha

        new_doc = save_file(request.files.get("documento"))
        examen.documento = append_document(examen.documento, new_doc)

        db.session.commit()

        return jsonify({"success": True, "message": "Examen actualizado correctamente"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route('/examenes/<int:examen_id>/documento/<string:filename>', methods=['DELETE'])
def eliminar_documento_examen(examen_id, filename):
    examen = Examen.query.get(examen_id)
    if not examen:
        return jsonify({"success": False, "message": "Examen no encontrado"}), 404

    docs = load_docs(examen.documento)

    if filename not in docs:
        return jsonify({"success": False, "message": "Documento no encontrado"}), 404

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    docs.remove(filename)
    examen.documento = json.dumps(docs) if docs else None

    db.session.commit()

    return jsonify({"success": True, "message": "Documento eliminado"}), 200


@api.route('/examenes/<int:examen_id>', methods=['DELETE'])
def eliminar_examen(examen_id):
    examen = Examen.query.get(examen_id)
    if not examen:
        return jsonify({"success": False, "message": "Examen no encontrado"}), 404

    if examen.documento:
        docs = load_docs(examen.documento)
        for f in docs:
            filepath = os.path.join(UPLOAD_FOLDER, f)
            if os.path.exists(filepath):
                os.remove(filepath)

    db.session.delete(examen)
    db.session.commit()

    return jsonify({"success": True, "message": "Examen eliminado correctamente"}), 200


# ============================================================
# CONSULTAS
# ============================================================

@api.route('/consultas/<int:mascota_id>', methods=['GET'])
def obtener_consultas(mascota_id):
    consultas = Consulta.query.filter_by(mascota_id=mascota_id).all()
    return jsonify([c.to_dict() for c in consultas]), 200


@api.route('/consultas', methods=['POST'])
def crear_consulta():
    try:
        veterinario = request.form.get("veterinario")
        tarjeta_profesional = request.form.get("tarjeta_profesional")
        nombre_veterinaria = request.form.get("nombre_veterinaria")
        direccion = request.form.get("direccion")
        telefono = request.form.get("telefono")
        fecha = parse_date(request.form.get("fecha"))
        mascota_id = request.form.get("mascota_id")
        documento = save_file(request.files.get("documento"))

        nueva = Consulta(
            veterinario=veterinario,
            tarjeta_profesional=tarjeta_profesional,
            nombre_veterinaria=nombre_veterinaria,
            direccion=direccion,
            telefono=telefono,
            fecha=fecha,
            documento=documento,
            mascota_id=mascota_id
        )

        db.session.add(nueva)
        db.session.commit()

        return jsonify({"success": True, "message": "Consulta registrada correctamente"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route('/consultas/<int:consulta_id>', methods=['PUT'])
def actualizar_consulta(consulta_id):
    try:
        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return jsonify({"success": False, "message": "Consulta no encontrada"}), 404

        consulta.veterinario = request.form.get("veterinario", consulta.veterinario)
        consulta.tarjeta_profesional = request.form.get("tarjeta_profesional", consulta.tarjeta_profesional)
        consulta.nombre_veterinaria = request.form.get("nombre_veterinaria", consulta.nombre_veterinaria)
        consulta.direccion = request.form.get("direccion", consulta.direccion)
        consulta.telefono = request.form.get("telefono", consulta.telefono)
        consulta.fecha = parse_date(request.form.get("fecha")) or consulta.fecha

        new_doc = save_file(request.files.get("documento"))
        consulta.documento = append_document(consulta.documento, new_doc)

        db.session.commit()

        return jsonify({"success": True, "message": "Consulta actualizada correctamente"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route('/consultas/<int:consulta_id>/documento/<string:filename>', methods=['DELETE'])
def eliminar_documento_consulta(consulta_id, filename):
    consulta = Consulta.query.get(consulta_id)
    if not consulta:
        return jsonify({"success": False, "message": "Consulta no encontrada"}), 404

    docs = load_docs(consulta.documento)

    if filename not in docs:
        return jsonify({"success": False, "message": "Documento no encontrado"}), 404

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    docs.remove(filename)
    consulta.documento = json.dumps(docs) if docs else None

    db.session.commit()

    return jsonify({"success": True, "message": "Documento eliminado"}), 200


@api.route('/consultas/<int:consulta_id>', methods=['DELETE'])
def eliminar_consulta(consulta_id):
    consulta = Consulta.query.get(consulta_id)
    if not consulta:
        return jsonify({"success": False, "message": "Consulta no encontrada"}), 404

    if consulta.documento:
        docs = load_docs(consulta.documento)
        for f in docs:
            filepath = os.path.join(UPLOAD_FOLDER, f)
            if os.path.exists(filepath):
                os.remove(filepath)

    db.session.delete(consulta)
    db.session.commit()

    return jsonify({"success": True, "message": "Consulta eliminada correctamente"}), 200
