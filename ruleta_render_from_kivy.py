"""
Versión web (Flask) del código Kivy del usuario.
Archivo: ruleta_render_from_kivy.py
"""

from flask import Flask, request, jsonify, render_template_string, send_file
import json
import os
import random
from collections import Counter
from io import BytesIO

APP = Flask(__name__)
ARCHIVO = "historial.json"

# -----------------------------
# Cargar / Guardar historial
# -----------------------------

def cargar_historial():
    if os.path.exists(ARCHIVO):
        try:
            with open(ARCHIVO, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def guardar_historial_local(hist):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2, ensure_ascii=False)

historial = cargar_historial()

ROJOS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}

# -----------------------------
# Funciones originales
# -----------------------------

def calcular_docenas(lista):
    if not lista: return "Sin datos de docenas."
    doc = {"1D":0, "2D":0, "3D":0}
    for n in lista:
        if 1 <= n <= 12: doc["1D"] += 1
        elif 13 <= n <= 24: doc["2D"] += 1
        elif 25 <= n <= 36: doc["3D"] += 1
    total = sum(doc.values())
    if total == 0: return "Sin datos de docenas."
    p = {k: round((v/total)*100) for k,v in doc.items()}
    return f"1D {p['1D']}% // 2D {p['2D']}% // 3D {p['3D']}%"

def calcular_mitad(lista):
    if not lista: return "Sin datos de mitades."
    mit = {"1-18":0, "19-36":0}
    for n in lista:
        if 1 <= n <= 18: mit["1-18"] += 1
        elif 19 <= n <= 36: mit["19-36"] += 1
    total = sum(mit.values())
    if total == 0: return "Sin datos de mitades."
    p = {k: round((v/total)*100) for k,v in mit.items()}
    return f"1-18 {p['1-18']}% // 19-36 {p['19-36']}%"

def ia_predecir():
    if len(historial) < 6:
        return "IA: pocos datos."
    ultimos = [h[0] for h in historial][-10:]

    doc = {"1D":0, "2D":0, "3D":0}
    mit = {"1-18":0, "19-36":0}

    for n in ultimos:
        if 1 <= n <= 12: doc["1D"] += 1
        elif 13 <= n <= 24: doc["2D"] += 1
        elif 25 <= n <= 36: doc["3D"] += 1
        if 1 <= n <= 18: mit["1-18"] += 1
        elif 19 <= n <= 36: mit["19-36"] += 1

    d_max = max(doc, key=doc.get)
    m_max = max(mit, key=mit.get)

    return f"IA Pronóstico: Docena → {d_max} | Mitad → {m_max}"

def registrar_tirada(num, direccion):
    historial.append([num, direccion])
    guardar_historial_local(historial)

def obtener_siguientes(num, direccion, cant=10):
    return Counter(
        [historial[i+1][0] for i in range(len(historial)-1)
         if historial[i][0] == num and historial[i][1] == direccion]
    ).most_common(cant)

def formatear_historial(limite=100):
    if not historial:
        return "Historial vacío"

    partes = []
    for n, dire in historial[-limite:]:
        d = dire.replace("➡️","D").replace("⬅️","I")

        if n == 0:
            col = f"<span style='color:green'>{n}</span>"
        elif n in ROJOS:
            col = f"<span style='color:red'>{n}</span>"
        else:
            col = f"<span style='color:white'>{n}</span>"

        partes.append(f"{col}({d})")

    return "Historial: " + " → ".join(partes)

# -----------------------------
# HTML — sin errores
# -----------------------------

HTML = """
<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<title>Ruleta Web</title>

<style>
body{
    background:#222;
    color:#eee;
    font-family:Arial;
    margin:20px;
}

/* Tarjetas */
.card{
    background:#333;
    padding:14px;
    border-radius:8px;
    margin-top:12px;
}

/* Teclas de números */
.key{
    display:flex;
    align-items:center;
    justify-content:center;
    width:60px;
    height:60px;
    margin:6px;
    border-radius:6px;
    cursor:pointer;
    font-size:22px;
    color:white;
}

/* Colores ruleta */
.green{background:#0a6}
.red{background:#a33}
.black{background:#444}

/* --- Diseño RESPONSIVE --- */

/* Teclado como grid flexible */
#teclado{
    display:grid;
    grid-template-columns:repeat(auto-fit, minmax(55px, 1fr));
    gap:8px;
}

/* Ajustes para celulares */
@media (max-width: 600px){

    body{margin:10px}

    h1{
        font-size:22px;
        text-align:center;
    }

    .card{
        padding:10px;
    }

    input{
        width:100%!important;
        font-size:20px;
        margin-top:8px;
    }

    button{
        margin-top:6px;
        font-size:16px;
        padding:8px 12px;
    }

    .key{
        height:48px;
        width:48px;
        font-size:18px;
        margin:4px;
    }

    #teclado{
        grid-template-columns:repeat(auto-fit, minmax(45px, 1fr));
        gap:6px;
    }
}
</style>

</head>
<body>

<h1>Ruleta Web</h1>

<div class='card'>
  <label>Dirección:</label>
  <button onclick="setDir('⬅️')">Izquierda</button>
  <button onclick="setDir('➡️')">Derecha</button>
  <div id='dirLabel' style='margin-top:6px;color:#ccc'></div>

  <br><br>

  <label>Número:</label>
  <input id='num' style='width:100px;font-size:22px'>
  <button onclick='registrar()'>Registrar</button>
  <button onclick='deshacer()'>Deshacer</button>

  <div id='msg' style='margin-top:8px;color:#bbb'></div>
</div>

<div class='card'>
  <div id='hist'></div>
  <div id='ia'></div>
  <div id='doc'></div>
  <div id='mit'></div>
</div>

<div class='card' id='teclado'></div>

<script>
let direccion = "➡️";

function setDir(d){
  direccion = d;
  document.getElementById('dirLabel').textContent = "Dirección: " + (d === "➡️" ? "Derecha" : "Izquierda");
}
setDir("➡️");

// Crear teclado 0–36
const T = document.getElementById('teclado');
const ROJOS = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];

for(let i=0;i<=36;i++){
  let b = document.createElement("div");
  b.className = "key";

  if(i==0) b.classList.add("green");
  else if(ROJOS.includes(i)) b.classList.add("red");
  else b.classList.add("black");

  b.textContent = i;
  b.onclick = ()=>{ document.getElementById("num").value = i };
  T.appendChild(b);
}

// Refrescar estado
async function refrescar(){
  const r = await fetch("/state");
  const j = await r.json();
  document.getElementById('hist').innerHTML = j.hist;
  document.getElementById('ia').textContent = j.ia;
  document.getElementById('doc').textContent = j.doc;
  document.getElementById('mit').textContent = j.mit;
}

// Registrar número
async function registrar(){
  const n = document.getElementById("num").value;
  if(n==="") return alert("Ingrese número");

  const r = await fetch("/register", {
    method:"POST",
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({num:parseInt(n), direccion})
  });

  const j = await r.json();
  document.getElementById("msg").textContent = j.mensaje;
  document.getElementById("num").value = "";
  refrescar();
}

// Deshacer
async function deshacer(){
  const r = await fetch("/undo",{method:"POST"});
  const j = await r.json();
  document.getElementById("msg").textContent = j.mensaje;
  refrescar();
}

refrescar();
</script>

</body>
</html>
"""

# -----------------------------
# Rutas Flask
# -----------------------------

@APP.route("/")
def index():
    return render_template_string(HTML)

@APP.route("/state")
def state():
    return jsonify({
        "hist": formatear_historial(),
        "ia": ia_predecir(),
        "doc": calcular_docenas([n for n,_ in historial[-50:]]),
        "mit": calcular_mitad([n for n,_ in historial[-50:]]),
    })

@APP.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    num = int(data["num"])
    direccion = data["direccion"]

    registrar_tirada(num, direccion)

    sig = obtener_siguientes(num, direccion)
    if sig:
        txt = ", ".join([f"{n} ({c})" for n,c in sig])
        d = "D" if direccion=="➡️" else "I"
        return jsonify({"mensaje":f"Después de {num} ({d}): {txt}"})
    else:
        d = "D" if direccion=="➡️" else "I"
        return jsonify({"mensaje":f"Sin datos para {num} ({d})."})

@APP.route("/undo", methods=["POST"])
def undo():
    if historial:
        n, d = historial.pop()
        guardar_historial_local(historial)
        d2 = "D" if d=="➡️" else "I"
        return jsonify({"mensaje":f"Se eliminó {n} ({d2})"})
    return jsonify({"mensaje":"Nada que deshacer."})

# -----------------------------
# Main
# -----------------------------

if __name__ == "__main__":
    APP.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
