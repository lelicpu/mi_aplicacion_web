from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_secreta"

ARCHIVO_USUARIOS = 'usuarios.json'
ARCHIVO_INGRESOS = 'ingresos.json'
ARCHIVO_GASTOS = 'gastos.json'

# Crear archivos si no existen
for archivo in [ARCHIVO_USUARIOS, ARCHIVO_INGRESOS, ARCHIVO_GASTOS]:
    if not os.path.exists(archivo):
        with open(archivo, 'w', encoding='utf-8') as f:
            if archivo == ARCHIVO_USUARIOS:
                json.dump([], f, indent=4)
            else:
                json.dump({}, f, indent=4)

# ---- Rutas de login/registro ----
@app.route('/')
def bienvenida():
    return render_template('bienvenida.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    correo = data.get('correo', '')
    contraseña = data.get('contraseña', '')

    if not correo or not contraseña:
        return jsonify({"ok": False, "error": "Rellene todos los campos"})

    with open(ARCHIVO_USUARIOS, 'r', encoding='utf-8') as f:
        usuarios = json.load(f)

    for usuario in usuarios:
        if usuario.get('correo') == correo:
            if check_password_hash(usuario.get('contraseña',''), contraseña):
                session['usuario'] = usuario
                return jsonify({"ok": True})
            else:
                return jsonify({"ok": False, "error": "Contraseña incorrecta"})

    return jsonify({"ok": False, "error": "Correo no registrado"})

@app.route('/registro', methods=['POST'])
def registro():
    data = request.get_json()
    nombre = data.get('nombre', '')
    correo = data.get('correo', '')
    contraseña = data.get('contraseña', '')

    if not nombre or not correo or not contraseña:
        return jsonify({"ok": False, "error": "Rellene todos los campos"})

    with open(ARCHIVO_USUARIOS, 'r', encoding='utf-8') as f:
        usuarios = json.load(f)

    for u in usuarios:
        if u.get('correo') == correo:
            return jsonify({"ok": False, "error": "Ese correo ya está registrado"})

    hash_contraseña = generate_password_hash(contraseña)
    nuevo_usuario = {'nombre': nombre, 'correo': correo, 'contraseña': hash_contraseña, 'ahorro': 0}
    usuarios.append(nuevo_usuario)

    with open(ARCHIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=4)

    session['usuario'] = nuevo_usuario
    return jsonify({"ok": True})

# ---- Panel de usuario ----
@app.route('/panel')
def panel_usuario():
    if 'usuario' not in session:
        return redirect(url_for('bienvenida'))
    usuario = session['usuario']
    return render_template('inicio_usuario.html', nombre=usuario.get('nombre','Usuario'), correo=usuario.get('correo',''))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('bienvenida'))

# ---- API para obtener datos del usuario ----
@app.route('/datos', methods=['GET'])
def obtener_datos():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401

    correo = session['usuario'].get('correo')

    with open(ARCHIVO_INGRESOS, 'r', encoding='utf-8') as f:
        ingresos_data = json.load(f)
    with open(ARCHIVO_GASTOS, 'r', encoding='utf-8') as f:
        gastos_data = json.load(f)
    with open(ARCHIVO_USUARIOS, 'r', encoding='utf-8') as f:
        usuarios = json.load(f)

    # Obtener ahorro del usuario
    ahorro = 0
    for u in usuarios:
        if u.get('correo') == correo:
            ahorro = u.get('ahorro', 0)
            break

    user_ingresos = ingresos_data.get(correo, [])
    user_gastos = gastos_data.get(correo, [])

    return jsonify({"ingresos": user_ingresos, "gastos": user_gastos, "ahorro": ahorro})

# ---- API para guardar datos del usuario ----
@app.route('/datos', methods=['POST'])
def guardar_datos():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    correo = session['usuario'].get('correo')

    # Guardar ingresos
    with open(ARCHIVO_INGRESOS, 'r', encoding='utf-8') as f:
        ingresos_data = json.load(f)
    ingresos_data[correo] = data.get('ingresos', [])
    with open(ARCHIVO_INGRESOS, 'w', encoding='utf-8') as f:
        json.dump(ingresos_data, f, indent=4)

    # Guardar gastos
    with open(ARCHIVO_GASTOS, 'r', encoding='utf-8') as f:
        gastos_data = json.load(f)
    gastos_data[correo] = data.get('gastos', [])
    with open(ARCHIVO_GASTOS, 'w', encoding='utf-8') as f:
        json.dump(gastos_data, f, indent=4)

    # Guardar ahorro en usuarios.json
    with open(ARCHIVO_USUARIOS, 'r', encoding='utf-8') as f:
        usuarios = json.load(f)
    for u in usuarios:
        if u.get('correo') == correo:
            u['ahorro'] = data.get('ahorro', 0)
            session['usuario']['ahorro'] = u['ahorro']
            break
    with open(ARCHIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=4)

    return jsonify({"ok": True})

if __name__ == '__main__':
    app.run(debug=True)
