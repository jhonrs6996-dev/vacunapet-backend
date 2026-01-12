print("✅ models.py correcto cargado")

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ------------------ USUARIO ------------------

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellido = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # ✔ AGREGADO: foto del usuario en base64
    foto = db.Column(db.Text)

    mascotas = db.relationship('Mascota', backref='duenio', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


# ------------------ MASCOTA ------------------

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


# ------------------ VACUNA ------------------

class Vacuna(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    fecha_aplicacion = db.Column(db.Date, nullable=False)
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascota.id'), nullable=False)


# ------------------ DIAGNOSTICO ------------------

class Diagnostico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.Text)
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascota.id'), nullable=False)


# ------------------ RECETA ------------------

class Receta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicamento = db.Column(db.String(200), nullable=False)
    dosis = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    instrucciones = db.Column(db.Text)
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascota.id'), nullable=False)


# ------------------ PREVENCION ------------------

class Prevencion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.Text)
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascota.id'), nullable=False)
