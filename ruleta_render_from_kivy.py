# Archivo completo corregido: ruleta_render_from_kivy.py
# NOTA: Inserta aquí tu lógica original de la ruleta dentro de los métodos marcados.

from flask import Flask, request, jsonify
import json
import os

APP = Flask(__name__)

# =============================
# 1. HISTORIAL LOCAL
# =============================
HISTORIAL_FILE = "historial.json"


def cargar_historial_local():
    if not os.path.exists(HISTORIAL_FILE):
        return []
    try:
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def guardar_historial_local(historial):
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)


historial = cargar_historial_local()

# =============================
# 2. HTML COMPLETO (CORREGIDO)
# =============================
HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Ruleta Kivy Render</title>
<style>
    body {
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
        background: #222;
        color: #eee;
        text-align: center;
    }

    h1 {
        margin-top: 20px;
        color: #fff;
    }

    .container {
        margin: 20px auto;
        max-width: 500px;
        background: #333;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    }

    .input-group {
        margin-bottom: 15px;
    }

    label {
        display: block;
        margin-bottom: 5px;
        font-size: 14px;
    }

    input[type="number"] {
        width: 100%;
        padding: 10px;
        border: 1px solid #555;
        border-radius: 4px;
        background: #111;
        color: #fff;
    }

    button {
        background: #28a745;
        color: #fff;
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
    }

    button:hover {
        background: #218838;
    }

    .historial {
        margin-top: 20px;
        max-height: 240px;
        overflow-y: auto;
        text-align: left;
        padding: 10px;
        background: #111;
        border-radius: 4px;
    }

    .historial-entry {
        border-bottom: 1px solid #333;
        padding: 6px 0;
        font-size: 14px;
    }

</style>
</head>
<body>
<h1>Ruleta Kivy – Web</h1>
<div class="container">

    <div class="input-group">
        <label>Número ingresado</label>
        <input id="numero" type="number" placeholder="Ingresa un número" />
    </div>

    <button onclick="enviarNumero()">Enviar número</button>
    <button style="background:#c00;margin-left:10px" onclick="limpiarHistorial()">Limpiar Historial</button>

    <div class="historial" id="historial"></div>
</div>

<script>
function enviarNumero() {
    const valor = document.getElementById("numero").value;
    if (!valor) return alert("Ingresa un número válido");

    fetch('/ingresar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ numero: valor })
    })
    .then(r => r.json())
    .then(actualizarHistorial);
}

function limpiarHistorial() {
    fetch('/clear', { method: 'POST' })
    .then(r => r.json())
    .then(() => cargarHistorial());
}

function cargarHistorial() {
    fetch('/historial')
        .then(r => r.json())
        .then(actualizarHistorial);
}

function actualizarHistorial(data) {
    const div = document.getElementById("historial");
    div.innerHTML = "";
    data.forEach(e => {
        div.innerHTML += `<div class='historial-entry'>${e}</div>`;
    });
}

cargarHistorial();
</script>
</body>
</html>
"""

# =============================
# 3. ENDPOINTS
# =============================
@APP.route("/")
def home():
    return HTML


@APP.route('/ingresar', methods=['POST'])
def ingresar():
    global historial
    data = request.get_json()
    numero = data.get("numero", None)

    # Aquí integras tu lógica de ruleta real:
    resultado = f"Ingresado número: {numero}"

    historial.append(resultado)
    guardar_historial_local(historial)

    return jsonify(historial)


@APP.route('/historial')
def get_hist():
    return jsonify(historial)


@APP.route('/clear', methods=['POST'])
def clear_hist():
    global historial
    historial = []
    guardar_historial_local(historial)
    return jsonify([])

# =============================
# 4. EJECUCIÓN
# =============================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    APP.run(host="0.0.0.0", port=port)
