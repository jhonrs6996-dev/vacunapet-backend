print("✅ models.py actualizado correctamente")

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json  # ← necesario para manejar listas de documentos

db = SQLAlchemy()

# ============================================================
# UTILIDAD PARA FECHAS
# ============================================================

def parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except:
        return None


# ============================================================
# USUARIO
# ============================================================

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellido = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    foto = db.Column(db.Text)

    mascotas = db.relationship('Mascota', backref='duenio', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


# ============================================================
# MASCOTA
# ============================================================

class Mascota(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especie = db.Column(db.String(100), nullable=False)
    raza = db.Column(db.String(100))
    fecha_nacimiento = db.Column(db.Date)
    peso = db.Column(db.Float)
    microchip = db.Column(db.String(100))
    castrado = db.Column(db.Boolean, default=False)
    foto = db.Column(db.String(200))

    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    vacunas = db.relationship('Vacuna', backref='mascota', cascade="all, delete-orphan")
    diagnosticos = db.relationship('Diagnostico', backref='mascota', cascade="all, delete-orphan")
    recetas = db.relationship('Receta', backref='mascota', cascade="all, delete-orphan")
    prevenciones = db.relationship('Prevencion', backref='mascota', cascade="all, delete-orphan")
    consultas = db.relationship('Consulta', backref='mascota', cascade="all, delete-orphan")
    examenes = db.relationship('Examen', backref='mascota', cascade="all, delete-orphan")

    def calcular_edad(self):
        if not self.fecha_nacimiento:
            return None
        hoy = date.today()
        años = hoy.year - self.fecha_nacimiento.year
        if (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
            años -= 1
        return años

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "especie": self.especie,
            "raza": self.raza,
            "fecha_nacimiento": self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            "peso": self.peso,
            "microchip": self.microchip,
            "castrado": self.castrado,
            "foto": self.foto,
            "user_id": self.user_id
        }


# ============================================================
# VACUNA
# ============================================================

class Vacuna(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

    marca = db.Column(db.String(100))
    tarjeta_profesional = db.Column(db.String(100))
    cantidad_dosis = db.Column(db.String(50))
    numero_identificacion = db.Column(db.String(100))

    fecha_fabricacion = db.Column(db.Date)
    fecha_vencimiento = db.Column(db.Date)

    fecha_aplicacion = db.Column(db.Date, nullable=False)
    fecha_refuerzo = db.Column(db.Date)

    # Puede ser string simple o JSON string con lista de nombres de archivos
    documento = db.Column(db.String(300))

    mascota_id = db.Column(db.Integer, db.ForeignKey('mascota.id'), nullable=False)

    def to_dict(self):
        # Convertir documento → lista (hasta 5 documentos)
        docs = []
        if self.documento:
            try:
                parsed = json.loads(self.documento)
                if isinstance(parsed, list):
                    docs = parsed
                else:
                    docs = [parsed]
            except:
                docs = [self.documento]

        # Limitar a máximo 5 por seguridad
        docs = docs[:5]

        return {
            "id": self.id,
            "nombre": self.nombre,
            "marca": self.marca,
            "tarjeta_profesional": self.tarjeta_profesional,
            "cantidad_dosis": self.cantidad_dosis,
            "numero_identificacion": self.numero_identificacion,
            "fecha_fabricacion": self.fecha_fabricacion.isoformat() if self.fecha_fabricacion else None,
            "fecha_vencimiento": self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
            "fecha_aplicacion": self.fecha_aplicacion.isoformat() if self.fecha_aplicacion else None,
            "fecha_refuerzo": self.fecha_refuerzo.isoformat() if self.fecha_refuerzo else None,
            "documentos": docs,  # ← ahora siempre lista
            "mascota_id": self.mascota_id
        }


# ============================================================
# DIAGNÓSTICO
# ============================================================

class Diagnostico(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    diagnostico_confirmado = db.Column(db.Boolean, default=False)
    sospecha = db.Column(db.String(300))

    titulo = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.Text)

    documento = db.Column(db.String(300))

    mascota_id = db.Column(db.Integer, db.ForeignKey('mascota.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "fecha": self.fecha.isoformat(),
            "descripcion": self.descripcion,
            "diagnostico_confirmado": self.diagnostico_confirmado,
            "sospecha": self.sospecha,
            "documento": self.documento,
            "mascota_id": self.mascota_id
        }


# ============================================================
# RECETA
# ============================================================

class Receta(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    medicamento_veterinario = db.Column(db.Boolean, default=True)
    medicamento = db.Column(db.String(200), nullable=False)
    cantidad = db.Column(db.String(100))
    via_administracion = db.Column(db.String(100))
    instrucciones = db.Column(db.Text)
    observaciones = db.Column(db.Text)

    fecha = db.Column(db.Date, nullable=False)

    documento = db.Column(db.String(300))

    mascota_id = db.Column(db.Integer, db.ForeignKey('mascota.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "medicamento_veterinario": self.medicamento_veterinario,
            "medicamento": self.medicamento,
            "cantidad": self.cantidad,
            "via_administracion": self.via_administracion,
            "instrucciones": self.instrucciones,
            "observaciones": self.observaciones,
            "fecha": self.fecha.isoformat(),
            "documento": self.documento,
            "mascota_id": self.mascota_id
        }


# ============================================================
# PREVENCIÓN
# ============================================================

class Prevencion(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    tipo = db.Column(db.String(200), nullable=False)
    cantidad = db.Column(db.String(100))
    medida = db.Column(db.String(100))

    fecha = db.Column(db.Date, nullable=False)
    fecha_refuerzo = db.Column(db.Date)

    descripcion = db.Column(db.Text)

    documento = db.Column(db.String(300))

    mascota_id = db.Column(db.Integer, db.ForeignKey('mascota.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "cantidad": self.cantidad,
            "medida": self.medida,
            "fecha": self.fecha.isoformat(),
            "fecha_refuerzo": self.fecha_refuerzo.isoformat() if self.fecha_refuerzo else None,
            "descripcion": self.descripcion,
            "documento": self.documento,
            "mascota_id": self.mascota_id
        }


# ============================================================
# CONSULTA
# ============================================================

class Consulta(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    veterinario = db.Column(db.String(200), nullable=False)
    tarjeta_profesional = db.Column(db.String(100))
    nombre_veterinaria = db.Column(db.String(200))
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(50))

    fecha = db.Column(db.Date, nullable=False)

    documento = db.Column(db.String(300))

    mascota_id = db.Column(db.Integer, db.ForeignKey('mascota.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "veterinario": self.veterinario,
            "tarjeta_profesional": self.tarjeta_profesional,
            "nombre_veterinaria": self.nombre_veterinaria,
            "direccion": self.direccion,
            "telefono": self.telefono,
            "fecha": self.fecha.isoformat(),
            "documento": self.documento,
            "mascota_id": self.mascota_id
        }


# ============================================================
# EXAMEN
# ============================================================

class Examen(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    tipo_examen = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    detalles = db.Column(db.Text)

    # Puede ser string o JSON string
    documento = db.Column(db.String(300))

    mascota_id = db.Column(db.Integer, db.ForeignKey('mascota.id'), nullable=False)

    def to_dict(self):
        # Convertir documento → lista
        docs = []
        if self.documento:
            try:
                parsed = json.loads(self.documento)
                if isinstance(parsed, list):
                    docs = parsed
                else:
                    docs = [parsed]
            except:
                docs = [self.documento]

        return {
            "id": self.id,
            "tipo_examen": self.tipo_examen,
            "fecha": self.fecha.isoformat(),
            "detalles": self.detalles,
            "documentos": docs,   # ← siempre lista
            "mascota_id": self.mascota_id
        }
