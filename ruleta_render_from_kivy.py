"""
Versión web (Flask) del código Kivy del usuario.
Archivo: ruleta_render_from_kivy.py
- Mantiene la lógica original (historial, IA, docenas, mitades, registro, deshacer, importar/exportar)
- Expone una UI web simple y endpoints AJAX para las acciones
- Guarda el historial en el mismo archivo historial.json en la carpeta de la app

Cómo usar:
1) pip install Flask
2) python ruleta_render_from_kivy.py
3) Abrir http://127.0.0.1:5000

Este archivo fue generado a partir del código Kivy proporcionado por el usuario.
"""
from flask import Flask, request, jsonify, render_template_string, send_file, abort, make_response
import secrets
import json
import os
from collections import Counter
import random
from io import BytesIO

APP = Flask(__name__)
ARCHIVO = "historial.json"

# --- funciones originales (ajustadas) ---

def cargar_historial(ruta=ARCHIVO):
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def guardar_historial_local(hist, ruta=ARCHIVO):
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(hist, f, indent=2, ensure_ascii=False)


historial = cargar_historial()

ROJOS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}


def calcular_docenas(lista):
    if not lista: return "Sin datos de docenas."
    docenas = {"1D": 0, "2D": 0, "3D": 0}
    for n in lista:
        if 1 <= n <= 12: docenas["1D"] += 1
        elif 13 <= n <= 24: docenas["2D"] += 1
        elif 25 <= n <= 36: docenas["3D"] += 1
    total = sum(docenas.values())
    if total == 0: return "Sin datos de docenas."
    porcentajes = {k: round((v / total) * 100) for k, v in docenas.items()}
    return f"1D {porcentajes['1D']}% // 2D {porcentajes['2D']}% // 3D {porcentajes['3D']}%"


def calcular_mitad(lista):
    if not lista: return "Sin datos de mitades."
    mitades = {"1-18": 0, "19-36": 0}
    for n in lista:
        if 1 <= n <= 18: mitades["1-18"] += 1
        elif 19 <= n <= 36: mitades["19-36"] += 1
    total = sum(mitades.values())
    if total == 0: return "Sin datos de mitades."
    porcentajes = {k: round((v / total) * 100) for k, v in mitades.items()}
    return f"1-18 {porcentajes['1-18']}% // 19-36 {porcentajes['19-36']}%"


def ia_predecir():
    if len(historial) < 6:
        return "IA: pocos datos."
    numeros_historial = [h[0] for h in historial]
    ultimos = numeros_historial[-10:]
    docenas = {"1D": 0, "2D": 0, "3D": 0}
    mitades = {"1-18": 0, "19-36": 0}
    for n in ultimos:
        if 1 <= n <= 12: docenas["1D"] += 1
        elif 13 <= n <= 24: docenas["2D"] += 1
        elif 25 <= n <= 36: docenas["3D"] += 1
        if 1 <= n <= 18: mitades["1-18"] += 1
        elif 19 <= n <= 36: mitades["19-36"] += 1
    docena_prob = max(docenas, key=docenas.get)
    mitad_prob = max(mitades, key=mitades.get)
    if list(docenas.values()).count(docenas[docena_prob]) > 1:
        empates_docena = [k for k, v in docenas.items() if v == docenas[docena_prob]]
        docena_prob = random.choice(empates_docena)
    if list(mitades.values()).count(mitades[mitad_prob]) > 1:
        empates_mitad = [k for k, v in mitades.items() if v == mitades[mitad_prob]]
        mitad_prob = random.choice(empates_mitad)
    return f"IA Pronóstico: Docena → {docena_prob} | Mitad → {mitad_prob}"


def registrar_tirada(num, direccion):
    global historial
    historial.append([num, direccion])
    guardar_historial_local(historial)


def obtener_siguientes(num, direccion, cantidad=10):
    siguientes = [historial[i+1][0] for i in range(len(historial)-1)
                  if historial[i][0] == num and historial[i][1] == direccion]
    return Counter(siguientes).most_common(cantidad)


def formatear_historial(limite=100):
    if not historial:
        return "Historial vacío"
    partes = []
    for num_dir in historial[-limite:]:
        num = num_dir[0]
        direccion = num_dir[1].replace('➡️', 'D').replace('⬅️', 'I')
        if num == 0:
            color_num = f"<span style='color:green'>{num}</span>"
        elif num in ROJOS:
            color_num = f"<span style='color:red'>{num}</span>"
        else:
            color_num = f"<span style='color:white'>{num}</span>"
        partes.append(f"{color_num}({direccion})")
    return "Historial: " + " → ".join(partes)

# --- Rutas web ---

HTML = """
<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Ruleta - Web</title>
<style>
body{font-family:Arial;margin:16px;background:#222;color:#eee}
.container{max-width:960px;margin:0 auto}
.top{display:flex;justify-content:space-between;align-items:center}
.button{padding:10px 14px;margin:6px;border-radius:6px;cursor:pointer}
.btn-dir{padding:10px 18px;margin-right:8px}
.key{display:inline-block;width:60px;height:60px;margin:6px;text-align:center;line-height:60px;background:#2b5;cursor:pointer;border-radius:6px}
.green{background:#0a6}
.red{background:#a33}
.card{background:#333;padding:12px;border-radius:8px}
.small{font-size:14px;color:#ccc}
.hist{overflow:auto;max-height:80px;padding:6px}
</style>
</head>
<body>
<div class='container'>
  <div class='top'>
    <h1>RULETA - Web</h1>
    <div>
      <button class='button' id='btn-export'>Exportar</button>
      <input type='file' id='file-import' style='display:none'>
      <button class='button' id='btn-import'>Importar</button>
      <button class='button' id='btn-clear'>Limpiar</button>
    </div>
  </div>
  <div class='card'>
    <div>
      <label>Dirección:</label>
      <button class='btn-dir button' id='dir-left'>Izquierda</button>
      <button class='btn-dir button' id='dir-right'>Derecha</button>
    </div>
    <div style='margin-top:12px'>
      <label>Número:</label>
      <input id='num-input' style='font-size:22px;width:120px;padding:8px'>
      <button class='button' id='btn-register'>Registrar</button>
      <button class='button' id='btn-undo'>Deshacer</button>
    </div>
    <div style='margin-top:8px' id='resultado' class='small'></div>
    <div style='margin-top:8px' id='ia' class='small'></div>
    <div style='margin-top:8px' id='docenas' class='small'></div>
    <div style='margin-top:8px' id='mitad' class='small'></div>
  </div>

  <div style='margin-top:12px' class='card'>
    <div class='hist' id='historial'></div>
  </div>

  <div style='margin-top:12px' class='card'>
    <div id='teclado'></div>
  </div>
</div>

<script>
let direccion = '➡️';

document.getElementById('dir-left').addEventListener('click', ()=>{ direccion='⬅️'; updateDir(); });
document.getElementById('dir-right').addEventListener('click', ()=>{ direccion='➡️'; updateDir(); });
function updateDir(){ document.getElementById('resultado').textContent = 'Dirección: ' + (direccion==='➡️'? 'Derecha':'Izquierda'); }
updateDir();

// teclado 0-36
const teclado = document.getElementById('teclado');
for(let i=0;i<37;i++){
  let b = document.createElement('button');
  b.className='key';
  if(i==0) b.classList.add('green');
  else if([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36].includes(i)) b.classList.add('red');
  else b.style.background='#444';
  b.textContent = i;
  b.addEventListener('click', ()=>{ document.getElementById('num-input').value = i; });
  teclado.appendChild(b);
}

async function refresh(){
  const resp = await fetch('/state');
  const j = await resp.json();
  document.getElementById('historial').innerHTML = j.hist;
  document.getElementById('ia').textContent = j.ia;
  document.getElementById('docenas').textContent = j.docenas;
  document.getElementById('mitad').textContent = j.mitad;
}

document.getElementById('btn-register').addEventListener('click', async ()=>{
  const n = document.getElementById('num-input').value;
  if(n==='') return alert('Ingrese número');
  const resp = await fetch('/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({num:parseInt(n), direccion:direccion})});
  const j = await resp.json();
  document.getElementById('resultado').textContent = j.mensaje;
  document.getElementById('num-input').value='';
  refresh();
});

document.getElementById('btn-undo').addEventListener('click', async ()=>{
  const resp = await fetch('/undo', {method:'POST'});
  const j = await resp.json();
  document.getElementById('resultado').textContent = j.mensaje;
  refresh();
});

document.getElementById('btn-clear').addEventListener('click', async ()=>{
  if(!confirm('Borrar todo el historial?')) return;
  const resp = await fetch('/clear', {method:'POST'});
  const j = await resp.json();
  document.getElementById('resultado').textContent = j.mensaje;
  refresh();
});

document.getElementById('btn-export').addEventListener('click', ()=>{
  window.location.href = '/export';
});

document.getElementById('btn-import').addEventListener('click', ()=>{ document.getElementById('file-import').click(); });

document.getElementById('file-import').addEventListener('change', async (e)=>{
  const f = e.target.files[0];
  if(!f) return;
  const fd = new FormData();
  fd.append('file', f);
  const resp = await fetch('/import', {method:'POST', body:fd});
  const j = await resp.json();
  document.getElementById('resultado').textContent = j.mensaje;
  refresh();
});

// inicial
refresh();
</script>
</body>
</html>
"""

@APP.route('/')
def index():
    return render_template_string(HTML)

@APP.route('/state')
def state():
    return jsonify({
        'hist': formatear_historial(),
        'ia': ia_predecir(),
        'docenas': calcular_docenas([n for n,_ in historial[-50:]]),
        'mitad': calcular_mitad([n for n,_ in historial[-50:]]),
    })

@APP.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    try:
        num = int(data.get('num'))
        direccion = data.get('direccion')
    except Exception:
        return jsonify({'mensaje':'Datos inválidos'}), 400
    if not (0 <= num <= 36):
        return jsonify({'mensaje':'Número fuera de rango (0-36).'}), 400
    registrar_tirada(num, direccion)
    siguientes = obtener_siguientes(num, direccion)
    if siguientes:
        texto_coloreado = ", ".join([f"{n} ({c})" for n, c in siguientes])
        dir_letra = 'D' if direccion == '➡️' else 'I'
        mensaje = f"Después de {num} ({dir_letra}): {texto_coloreado}"
    else:
        dir_letra = 'D' if direccion == '➡️' else 'I'
        mensaje = f"Sin datos para {num} ({dir_letra})."
    return jsonify({'mensaje':mensaje})

@APP.route('/undo', methods=['POST'])
def undo():
    global historial
    if historial:
        ultimo = historial.pop()
        guardar_historial_local(historial)
        dir_letra = 'D' if ultimo[1] == '➡️' else 'I'
        return jsonify({'mensaje':f"Se eliminó {ultimo[0]} ({dir_letra})"})
    return jsonify({'mensaje':'Nada que deshacer.'})

@APP.route('/export')
def export_file():
    buf = BytesIO()
    buf.write(json.dumps(historial, ensure_ascii=False, indent=2).encode('utf-8'))
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='historial.json', mimetype='application/json')

@APP.route('/import', methods=['POST'])
def import_file():
    if 'file' not in request.files:
        return jsonify({'mensaje':'No se recibió archivo.'}), 400
    f = request.files['file']
    try:
        data = json.load(f)
        if isinstance(data, list):
            global historial
            historial = data
            guardar_historial_local(historial)
            return jsonify({'mensaje':f'Historial importado ({len(historial)} registros).'})
        else:
            return jsonify({'mensaje':'Formato inválido.'}), 400
    except Exception as e:
        return jsonify({'mensaje':'Error leyendo archivo.'}), 400

@APP.route('/clear', methods=['POST'])
def clear_hist():
    global historial
    historial = []
    guardar_historial_local(historial)
    return jsonify({'mensaje':'Historial limpiado.'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    APP.run(host="0.0.0.0", port=port)

