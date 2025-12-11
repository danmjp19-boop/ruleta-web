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

/* COLORES ORIGINALES */
.green{background:#0a6}
.red{background:#a33}
.card{background:#333;padding:12px;border-radius:8px}
.small{font-size:14px;color:#ccc}
.hist{overflow:auto;max-height:80px;padding:6px}

/* --------- NUEVOS ESTILOS PARA EL TECLADO --------- */
.key {
    color: white !important;
    font-weight: bold;
}
.key.green {
    color: black !important; /* el 0 queda como estaba */
}
.key.red {
    color: white !important; /* texto blanco sobre fondo rojo */
}
/* --------------------------------------------------- */

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
