from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
from models import db, Usuario, Mascota, Vacuna, Diagnostico, Receta, Prevencion

api = Blueprint('api', __name__)

# ============================================================
# TEST
# ============================================================
@api.route('/ping')
def ping():
    return jsonify({"success": True, "message": "API funcionando"}), 200


# ============================================================
# OBTENER USUARIO
# ============================================================
@api.route('/usuario/<int:id>', methods=['GET'])
def obtener_usuario(id):
    usuario = Usuario.query.get(id)

    if not usuario:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404

    return jsonify({
        "success": True,
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "email": usuario.email,
            "foto": usuario.foto if hasattr(usuario, "foto") else ""
        }
    }), 200


# ============================================================
# ACTUALIZAR USUARIO COMPLETO (NUEVO)
# ============================================================
@api.route('/usuario/<int:id>', methods=['PUT'])
def actualizar_usuario(id):
    usuario = Usuario.query.get(id)

    if not usuario:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404

    data = request.get_json() or {}

    usuario.nombre = data.get("nombre", usuario.nombre)
    usuario.apellido = data.get("apellido", usuario.apellido)
    usuario.email = data.get("email", usuario.email)

    # Foto opcional
    if "foto" in data:
        usuario.foto = data.get("foto")

    db.session.commit()

    return jsonify({"success": True, "message": "Usuario actualizado"}), 200


# ============================================================
# ACTUALIZAR FOTO DE USUARIO
# ============================================================
@api.route('/usuario/<int:user_id>/foto', methods=['PUT'])
def actualizar_foto_usuario(user_id):
    usuario = Usuario.query.get(user_id)

    if not usuario:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404

    data = request.get_json() or {}
    foto_base64 = data.get("foto")

    if not foto_base64:
        return jsonify({"success": False, "message": "No se envió ninguna foto"}), 400

    usuario.foto = foto_base64
    db.session.commit()

    return jsonify({"success": True, "message": "Foto actualizada"}), 200


# ============================================================
# LOGIN
# ============================================================
@api.route('/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "Email y contraseña son obligatorios"}), 400

    user = Usuario.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"success": False, "message": "Credenciales incorrectas"}), 401

    return jsonify({
        "success": True,
        "message": "Login exitoso",
        "user_id": user.id,
        "nombre": user.nombre,
        "apellido": user.apellido,
        "email": user.email,
        "foto": user.foto if hasattr(user, "foto") else ""
    }), 200


# ============================================================
# REGISTER
# ============================================================
@api.route('/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}

    nombre = data.get("nombre")
    apellido = data.get("apellido") or ""
    email = data.get("email")
    password = data.get("password")

    if not nombre or not email or not password:
        return jsonify({"success": False, "message": "Nombre, email y contraseña son obligatorios"}), 400

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

    return jsonify({
        "success": True,
        "message": "Usuario registrado",
        "user_id": nuevo.id,
        "nombre": nuevo.nombre,
        "apellido": nuevo.apellido,
        "email": nuevo.email,
        "foto": nuevo.foto
    }), 201


# ============================================================
# MASCOTAS
# ============================================================
@api.route('/mascotas', methods=['GET'])
def obtener_mascotas():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"success": False, "message": "Falta user_id"}), 400

    mascotas = Mascota.query.filter_by(user_id=user_id).all()

    return jsonify({
        "success": True,
        "mascotas": [m.to_dict() for m in mascotas]
    }), 200


@api.route('/mascotas', methods=['POST'])
def agregar_mascota():
    data = request.get_json() or {}

    if not data.get("nombre") or not data.get("especie") or not data.get("raza"):
        return jsonify({"success": False, "message": "Faltan datos obligatorios"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Falta user_id"}), 400

    nueva = Mascota(
        nombre=data.get("nombre"),
        especie=data.get("especie"),
        raza=data.get("raza"),
        fecha_nacimiento=None,
        peso=data.get("peso") or 0.0,
        microchip=data.get("microchip"),
        castrado=data.get("castrado", False),
        foto=data.get("foto") or "",
        user_id=user_id
    )

    db.session.add(nueva)
    db.session.commit()

    return jsonify({"success": True, "message": "Mascota agregada", "id": nueva.id}), 201


@api.route('/mascotas/<int:id>', methods=['PUT'])
def editar_mascota(id):
    mascota = Mascota.query.get(id)

    if not mascota:
        return jsonify({"success": False, "message": "Mascota no encontrada"}), 404

    data = request.get_json() or {}

    mascota.nombre = data.get("nombre", mascota.nombre)
    mascota.especie = data.get("especie", mascota.especie)
    mascota.raza = data.get("raza", mascota.raza)
    mascota.peso = data.get("peso", mascota.peso)
    mascota.microchip = data.get("microchip", mascota.microchip)
    mascota.castrado = data.get("castrado", mascota.castrado)
    mascota.foto = data.get("foto", mascota.foto)

    db.session.commit()

    return jsonify({"success": True, "message": "Mascota actualizada"}), 200


@api.route('/mascotas/<int:id>', methods=['DELETE'])
def eliminar_mascota(id):
    mascota = Mascota.query.get(id)

    if not mascota:
        return jsonify({"success": False, "message": "Mascota no encontrada"}), 404

    db.session.delete(mascota)
    db.session.commit()

    return jsonify({"success": True, "message": "Mascota eliminada"}), 200


# ============================================================
# VACUNAS
# ============================================================
@api.route('/mascotas/<int:mascota_id>/vacunas', methods=['GET'])
def obtener_vacunas(mascota_id):
    vacunas = Vacuna.query.filter_by(mascota_id=mascota_id).all()

    return jsonify({
        "success": True,
        "vacunas": [
            {
                "id": v.id,
                "nombre": v.nombre,
                "fecha_aplicacion": v.fecha_aplicacion.isoformat()
            }
            for v in vacunas
        ]
    }), 200


@api.route('/vacunas', methods=['POST'])
def agregar_vacuna():
    data = request.get_json() or {}

    if not data.get("nombre") or not data.get("fecha_aplicacion") or not data.get("mascota_id"):
        return jsonify({"success": False, "message": "Faltan datos"}), 400

    nueva = Vacuna(
        nombre=data.get("nombre"),
        fecha_aplicacion=date.fromisoformat(data.get("fecha_aplicacion")),
        mascota_id=data.get("mascota_id")
    )

    db.session.add(nueva)
    db.session.commit()

    return jsonify({"success": True, "message": "Vacuna agregada", "id": nueva.id}), 201


# ============================================================
# DIAGNÓSTICOS
# ============================================================
@api.route('/mascotas/<int:mascota_id>/diagnosticos', methods=['GET'])
def obtener_diagnosticos(mascota_id):
    diagnosticos = Diagnostico.query.filter_by(mascota_id=mascota_id).all()

    return jsonify({
        "success": True,
        "diagnosticos": [
            {
                "id": d.id,
                "titulo": d.titulo,
                "fecha": d.fecha.isoformat(),
                "descripcion": d.descripcion
            }
            for d in diagnosticos
        ]
    }), 200


@api.route('/diagnosticos', methods=['POST'])
def agregar_diagnostico():
    data = request.get_json() or {}

    if not data.get("titulo") or not data.get("fecha") or not data.get("mascota_id"):
        return jsonify({"success": False, "message": "Faltan datos"}), 400

    nuevo = Diagnostico(
        titulo=data.get("titulo"),
        fecha=date.fromisoformat(data.get("fecha")),
        descripcion=data.get("descripcion"),
        mascota_id=data.get("mascota_id")
    )

    db.session.add(nuevo)
    db.session.commit()

    return jsonify({"success": True, "message": "Diagnóstico agregado", "id": nuevo.id}), 201


# ============================================================
# RECETAS
# ============================================================
@api.route('/mascotas/<int:mascota_id>/recetas', methods=['GET'])
def obtener_recetas(mascota_id):
    recetas = Receta.query.filter_by(mascota_id=mascota_id).all()

    return jsonify({
        "success": True,
        "recetas": [
            {
                "id": r.id,
                "medicamento": r.medicamento,
                "dosis": r.dosis,
                "fecha": r.fecha.isoformat(),
                "instrucciones": r.instrucciones
            }
            for r in recetas
        ]
    }), 200


@api.route('/recetas', methods=['POST'])
def agregar_receta():
    data = request.get_json() or {}

    if not data.get("medicamento") or not data.get("dosis") or not data.get("fecha") or not data.get("mascota_id"):
        return jsonify({"success": False, "message": "Faltan datos"}), 400

    nueva = Receta(
        medicamento=data.get("medicamento"),
        dosis=data.get("dosis"),
        fecha=date.fromisoformat(data.get("fecha")),
        instrucciones=data.get("instrucciones"),
        mascota_id=data.get("mascota_id")
    )

    db.session.add(nueva)
    db.session.commit()

    return jsonify({"success": True, "message": "Receta agregada", "id": nueva.id}), 201


# ============================================================
# PREVENCIONES
# ============================================================
@api.route('/mascotas/<int:mascota_id>/prevenciones', methods=['GET'])
def obtener_prevenciones(mascota_id):
    prevenciones = Prevencion.query.filter_by(mascota_id=mascota_id).all()

    return jsonify({
        "success": True,
        "prevenciones": [
            {
                "id": p.id,
                "tipo": p.tipo,
                "fecha": p.fecha.isoformat(),
                "descripcion": p.descripcion
            }
            for p in prevenciones
        ]
    }), 200


@api.route('/prevenciones', methods=['POST'])
def agregar_prevencion():
    data = request.get_json() or {}

    if not data.get("tipo") or not data.get("fecha") or not data.get("mascota_id"):
        return jsonify({"success": False, "message": "Faltan datos"}), 400

    nueva = Prevencion(
        tipo=data.get("tipo"),
        fecha=date.fromisoformat(data.get("fecha")),
        descripcion=data.get("descripcion"),
        mascota_id=data.get("mascota_id")
    )

    db.session.add(nueva)
    db.session.commit()

    return jsonify({"success": True, "message": "Prevención agregada", "id": nueva.id}), 201
