"""
PFO 2 - Sistema de Gestión de Tareas con API y Base de Datos
Servidor: API REST con Flask + SQLite.

Endpoints:
    POST /registro  -> registra un usuario (contraseña hasheada)
    POST /login     -> verifica credenciales
    GET  /tareas    -> HTML de bienvenida (requiere autenticación básica)
"""

import os
import sqlite3
from functools import wraps

from flask import Flask, request, jsonify, render_template_string, g
from werkzeug.security import generate_password_hash, check_password_hash

# Ruta de la base de datos (se crea junto a este archivo)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tareas.db")

app = Flask(__name__)
app.json.ensure_ascii = False  # para que las respuestas JSON muestren acentos y ñ


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
def get_db():
    """Abre (una vez por request) la conexión a SQLite."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def cerrar_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Crea las tablas si no existen."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario       TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                creado_en     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def leer_credenciales_json():
    """Obtiene usuario y contraseña del cuerpo JSON.
    Acepta la clave "contraseña" (como pide la consigna) y también "contrasena".
    """
    datos = request.get_json(silent=True) or {}
    usuario = (datos.get("usuario") or "").strip()
    contrasena = datos.get("contraseña") or datos.get("contrasena") or ""
    return usuario, contrasena


def verificar_usuario(usuario, contrasena):
    """Devuelve True si el usuario existe y la contraseña coincide con el hash."""
    fila = get_db().execute(
        "SELECT password_hash FROM usuarios WHERE usuario = ?", (usuario,)
    ).fetchone()
    return fila is not None and check_password_hash(fila["password_hash"], contrasena)


def requiere_auth(f):
    """Decorador: exige autenticación HTTP Basic con un usuario registrado."""
    @wraps(f)
    def envoltura(*args, **kwargs):
        auth = request.authorization
        if not auth or not verificar_usuario(auth.username, auth.password):
            return (
                jsonify({"error": "Credenciales inválidas o ausentes"}),
                401,
                {"WWW-Authenticate": 'Basic realm="Gestor de Tareas"'},
            )
        return f(auth.username, *args, **kwargs)
    return envoltura


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.route("/registro", methods=["POST"])
def registro():
    usuario, contrasena = leer_credenciales_json()

    if not usuario or not contrasena:
        return jsonify({"error": "Se requieren 'usuario' y 'contraseña'"}), 400

    password_hash = generate_password_hash(contrasena)  # nunca se guarda en texto plano

    try:
        db = get_db()
        db.execute(
            "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
            (usuario, password_hash),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": f"El usuario '{usuario}' ya existe"}), 409

    return jsonify({"mensaje": f"Usuario '{usuario}' registrado correctamente"}), 201


@app.route("/login", methods=["POST"])
def login():
    usuario, contrasena = leer_credenciales_json()

    if not usuario or not contrasena:
        return jsonify({"error": "Se requieren 'usuario' y 'contraseña'"}), 400

    if not verificar_usuario(usuario, contrasena):
        return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

    return jsonify({
        "mensaje": f"Inicio de sesión exitoso. ¡Bienvenido/a, {usuario}!",
        "acceso": "Ya podés acceder a GET /tareas con autenticación básica",
    }), 200


PLANTILLA_BIENVENIDA = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Gestor de Tareas</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #f4f6fb; color: #222;
           display: flex; justify-content: center; align-items: center;
           min-height: 100vh; margin: 0; }
    .card { background: #fff; padding: 2.5rem 3rem; border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,.08); text-align: center; max-width: 480px; }
    h1 { margin-top: 0; color: #2b4c9b; }
    p  { line-height: 1.5; }
    .usuario { font-weight: bold; color: #2b4c9b; }
  </style>
</head>
<body>
  <div class="card">
    <h1>¡Bienvenido/a al Gestor de Tareas!</h1>
    <p>Hola <span class="usuario">{{ usuario }}</span>, iniciaste sesión correctamente.</p>
    <p>Desde aquí vas a poder organizar tus tareas.</p>
  </div>
</body>
</html>
"""


@app.route("/tareas", methods=["GET"])
@requiere_auth
def tareas(usuario):
    return render_template_string(PLANTILLA_BIENVENIDA, usuario=usuario)


@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "api": "Gestor de Tareas - PFO 2",
        "endpoints": {
            "POST /registro": "Registrar usuario",
            "POST /login": "Iniciar sesión",
            "GET /tareas": "Bienvenida (requiere autenticación básica)",
        },
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
