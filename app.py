import os
from datetime import datetime

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    jsonify,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Usuario, Mascota, Vacuna, Diagnostico, Receta, Prevencion
from api import api  # Blueprint con la API REST

# ------------------ CONFIGURACIÓN DE LA APP ------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vacunapet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# ------------------ LOGIN MANAGER ------------------

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
  return Usuario.query.get(int(user_id))

# ------------------ BLUEPRINT DE API (FLUTTER) ------------------

# Todas las rutas definidas en api.py quedarán bajo /api/...
app.register_blueprint(api, url_prefix='/api')

# ------------------ ENDPOINT SIMPLE PARA PROBAR EL SERVIDOR ------------------

@app.route('/ping', methods=['GET'])
def root_ping():
  return jsonify({"success": True, "message": "Servidor Flask funcionando"}), 200

# ------------------ RUTAS PRINCIPALES WEB ------------------

@app.route('/')
def servidor_activo():
  return "Servidor Flask funcionando correctamente"

@app.route('/web')
def web_home():
  return redirect(url_for('login'))

# ------------------ REGISTRO WEB (NO FLUTTER) ------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    email = request.form['email']
    password_plain = request.form['password']

    if Usuario.query.filter_by(email=email).first():
      flash('El correo ya está registrado.')
      return redirect(url_for('register'))

    password_hash = generate_password_hash(password_plain)
    nuevo = Usuario(
      nombre=nombre,
      apellido=apellido,
      email=email,
      password=password_hash,
      foto=""  # compatibilidad con Flutter
    )
    db.session.add(nuevo)
    db.session.commit()

    flash('Registro exitoso. Inicia sesión.')
    return redirect(url_for('login'))

  return render_template('register.html')

# ------------------ LOGIN WEB (FORMULARIO) ------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    email = request.form['email']
    password_plain = request.form['password']

    usuario = Usuario.query.filter_by(email=email).first()

    if usuario and check_password_hash(usuario.password, password_plain):
      login_user(usuario)
      return redirect(url_for('dashboard'))

    flash('Credenciales incorrectas.')
    return redirect(url_for('login'))

  return render_template('login.html')

# ------------------ LOGOUT WEB ------------------

@app.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('login'))

# ------------------ DASHBOARD WEB ------------------

@app.route('/dashboard')
@login_required
def dashboard():
  mascotas = Mascota.query.filter_by(user_id=current_user.id).all()
  return render_template('dashboard.html', mascotas=mascotas)

# ------------------ AGREGAR MASCOTA WEB ------------------

@app.route('/add_pet', methods=['GET', 'POST'])
@login_required
def add_pet():
  if request.method == 'POST':
    nombre = request.form.get("nombre")
    especie = request.form.get("especie")
    raza = request.form.get("raza")

    fecha_nacimiento_str = request.form.get("fecha_nacimiento")
    fecha_nacimiento = None
    if fecha_nacimiento_str:
      try:
        fecha_nacimiento = datetime.strptime(
          fecha_nacimiento_str, "%Y-%m-%d"
        ).date()
      except ValueError:
        flash("La fecha de nacimiento no tiene un formato válido.")
        return redirect(url_for("add_pet"))

    peso = request.form.get("peso")
    microchip = request.form.get("microchip")
    castrado = request.form.get("castrado") == "True"

    foto = request.files.get("foto")
    filename = None
    if foto and foto.filename != '':
      filename = secure_filename(foto.filename)
      foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    nueva = Mascota(
      nombre=nombre,
      especie=especie,
      raza=raza,
      fecha_nacimiento=fecha_nacimiento,
      peso=peso,
      microchip=microchip,
      castrado=castrado,
      foto=filename,
      user_id=current_user.id
    )

    db.session.add(nueva)
    db.session.commit()
    flash("Mascota registrada correctamente.")
    return redirect(url_for("dashboard"))

  return render_template("add_pet_form.html")

# ------------------ EJECUCIÓN ------------------

if __name__ == '__main__':
  with app.app_context():
    db.create_all()
  app.run(host="0.0.0.0", port=5000, debug=True)
