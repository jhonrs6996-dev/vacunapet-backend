# -*- coding: utf-8 -*-

from flask import Flask, send_from_directory
from flask_cors import CORS
from models import db
from api import api as api_bp
import os

app = Flask(__name__)

# Configuración de la base de datos
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vacunapet.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar extensiones
db.init_app(app)
CORS(app)

# Registrar Blueprint de API
app.register_blueprint(api_bp, url_prefix="/api")

# Ruta basada en la ubicación real de app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCUMENTOS_DIR = os.path.join(BASE_DIR, "uploads", "documentos")

print("📌 Carpeta base del proyecto:", BASE_DIR)
print("📌 Carpeta de documentos configurada:", DOCUMENTOS_DIR)

@app.route("/uploads/documentos/<path:filename>")
def serve_document(filename):
    # Diagnóstico: mostrar dónde está buscando Flask
    print("📂 Flask está buscando en:", DOCUMENTOS_DIR)
    print("📄 Archivo solicitado:", filename)

    return send_from_directory(DOCUMENTOS_DIR, filename)

# Crear tablas si no existen
with app.app_context():
    db.create_all()

# Iniciar servidor
if __name__ == "__main__":
    app.run(debug=True)
