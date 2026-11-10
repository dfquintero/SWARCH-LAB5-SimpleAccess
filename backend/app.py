from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import time

app = Flask(__name__)
CORS(app) # Permite la comunicación entre puertos (8080 -> 5000)

# REPOSITORY LAYER (Gestión de conexión)
def get_db_connection():
    # Reintentos automáticos por si la BD tarda unos segundos en arrancar en Docker
    for _ in range(5):
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                database=os.environ.get('DB_NAME', 'mydb'),
                user=os.environ.get('DB_USER', 'user'),
                password=os.environ.get('DB_PASSWORD', 'password')
            )
            return conn
        except psycopg2.OperationalError:
            time.sleep(2)
    raise Exception("No se pudo conectar a la base de datos PostgreSQL")

# SERVICE LAYER (Inicialización automática de la tabla de la asignatura)
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Crea la tabla si no existe
    cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                                                     id SERIAL PRIMARY KEY,
                                                     username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(50) NOT NULL
                    );
                """)
    conn.commit()
    cur.close()
    conn.close()

# CONTROLLER LAYER & SERVICE LAYER (Login)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "message": "Faltan datos requeridos"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # REPOSITORY: Consulta SQL directo
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            return jsonify({"success": True, "message": f"¡Bienvenido, {username}!"}), 200
        else:
            return jsonify({"success": False, "message": "Credenciales incorrectas"}), 401
    except Exception as e:
        return jsonify({"success": False, "message": f"Error en el servidor: {str(e)}"}), 500

# CONTROLLER LAYER & SERVICE LAYER (Registro de usuario)
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "message": "Faltan datos requeridos"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # REPOSITORY: Validar si el usuario ya existe para evitar errores duplicados
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "El nombre de usuario ya está registrado"}), 409

        # REPOSITORY: Insertar nuevo registro
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()

        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Usuario registrado exitosamente"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Error al registrar: {str(e)}"}), 500

if __name__ == '__main__':
    init_db() # Se ejecuta al levantar el contenedor de Flask
    app.run(host='0.0.0.0', port=5000)
