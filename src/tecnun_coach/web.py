"""Web chat for the tecnun-study-coach agent (Flask)."""

import atexit
import os
import secrets
import shutil
import subprocess
import sys
import threading
import webbrowser

from flask import Flask, jsonify, request, session

from .agent import AGENT_NAME, StudyCoach

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(16))
_coaches: dict[str, StudyCoach] = {}  # one agent conversation per browser session


@atexit.register
def _close_all():
    """On shutdown (Ctrl+C) delete every open conversation from Foundry."""
    for coach in _coaches.values():
        coach.close()
    _coaches.clear()


def _coach() -> StudyCoach:
    sid = session.setdefault("sid", secrets.token_hex(8))
    if sid not in _coaches:
        _coaches[sid] = StudyCoach()
    return _coaches[sid]


@app.get("/")
def index():
    return PAGE.replace("{{AGENT}}", AGENT_NAME)


@app.post("/api/chat")
def chat():
    text = (request.get_json(silent=True) or {}).get("message", "").strip()
    if not text:
        return jsonify(error="Empty message"), 400
    try:
        reply = _coach().ask(text)
    except Exception as e:
        return jsonify(error=str(e)), 502
    return jsonify(text=reply.text, tools=reply.tools)


@app.post("/api/reset")
def reset():
    _coach().reset()
    return jsonify(ok=True)


def _open_browser(url: str):
    """Open the chat in the default browser; on WSL use the Windows browser."""
    if shutil.which("cmd.exe"):
        subprocess.Popen(["cmd.exe", "/c", "start", "", url], cwd="/mnt/c",
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        webbrowser.open(url)


def main():
    port = int(os.getenv("PORT", "5000"))
    url = f"http://127.0.0.1:{port}"
    print(f"Tecnun Study Coach web: {url}  (Ctrl+C para parar)")
    if "--no-browser" not in sys.argv:
        threading.Timer(1.0, _open_browser, args=[url]).start()
    app.run(host="127.0.0.1", port=port, debug=False)


PAGE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Tecnun Study Coach</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.1.6/purify.min.js"></script>
<style>
:root{--bg:#f5f5f7;--surface:#fff;--text:#1d1d1f;--muted:#6e6e73;--hair:rgba(0,0,0,.08);--fill:#ececf0;--accent:#0071e3;--on-accent:#fff;
 --bar:rgba(245,245,247,.72);--shadow:0 1px 2px rgba(0,0,0,.04),0 6px 24px rgba(0,0,0,.05);--danger:#d70015}
@media (prefers-color-scheme:dark){:root{--bg:#000;--surface:#1c1c1e;--text:#f5f5f7;--muted:#98989d;--hair:rgba(255,255,255,.1);--fill:#2c2c2e;
 --accent:#0a84ff;--bar:rgba(22,22,23,.72);--shadow:0 0 0 1px rgba(255,255,255,.06);--danger:#ff453a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);height:100vh;height:100dvh;display:flex;flex-direction:column;
 font:15px/1.55 Inter,-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
button{font:inherit;color:inherit;border:0;background:none;cursor:pointer}
svg{display:block}
header{position:sticky;top:0;z-index:2;height:56px;padding:0 20px;display:flex;align-items:center;justify-content:space-between;
 background:var(--bar);-webkit-backdrop-filter:saturate(180%) blur(20px);backdrop-filter:saturate(180%) blur(20px);border-bottom:1px solid var(--hair)}
.brand{display:flex;align-items:center;gap:10px}
.logo{width:30px;height:30px;border-radius:8px;display:grid;place-items:center;color:#fff;background:linear-gradient(160deg,#3a8dff,#0058d0)}
.brand b{display:block;font-size:15px;font-weight:600;letter-spacing:-.01em;line-height:1.25}
.brand small{display:block;font-size:12px;color:var(--muted);line-height:1.25}
#new{display:flex;align-items:center;gap:6px;height:32px;padding:0 14px;border-radius:999px;background:var(--fill);font-size:13px;font-weight:500;transition:opacity .15s}
#new:hover{opacity:.75}
#log{flex:1;overflow-y:auto}
.col{max-width:760px;margin:0 auto;padding:28px 20px 12px}
.row{display:flex;margin:0 0 18px;animation:in .25s ease-out}
@keyframes in{from{opacity:0;transform:translateY(6px)}}
.row.me{justify-content:flex-end}
.me .bubble{max-width:78%;background:var(--accent);color:var(--on-accent);padding:10px 16px;border-radius:20px 20px 6px 20px;white-space:pre-wrap;overflow-wrap:anywhere}
.bot .bubble{width:100%;background:var(--surface);padding:18px 22px;border-radius:20px;box-shadow:var(--shadow);overflow-x:auto}
.bubble>:first-child{margin-top:0}.bubble>:last-child{margin-bottom:0}
.bubble h1,.bubble h2,.bubble h3{font-size:17px;font-weight:600;letter-spacing:-.01em;margin:22px 0 8px}
.bubble p{margin:0 0 12px}.bubble ul,.bubble ol{margin:0 0 12px;padding-left:22px}.bubble li{margin:3px 0}
.bubble strong{font-weight:600}.bubble a{color:var(--accent);text-decoration:none}.bubble a:hover{text-decoration:underline}
.bubble code{font:13px ui-monospace,"SF Mono",Menlo,Consolas,monospace;background:var(--fill);padding:1px 6px;border-radius:6px}
.bubble pre{background:var(--fill);padding:12px 14px;border-radius:12px;overflow-x:auto}.bubble pre code{padding:0;background:none}
.bubble table{width:100%;border-collapse:separate;border-spacing:0;margin:6px 0 16px;font-size:14px;border:1px solid var(--hair);border-radius:12px;overflow:hidden}
.bubble th{background:var(--fill);font-weight:600;text-align:left}
.bubble th,.bubble td{padding:8px 12px;border-bottom:1px solid var(--hair)}.bubble tr:last-child td{border-bottom:0}
.cite{display:inline-grid;place-items:center;min-width:17px;height:17px;padding:0 4px;margin-left:2px;border-radius:999px;
 background:var(--fill);color:var(--muted);font-size:10.5px;font-weight:600;line-height:1;vertical-align:2px}
.tools{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}
.chip{display:inline-flex;align-items:center;gap:6px;height:24px;padding:0 10px;border-radius:999px;background:var(--fill);color:var(--muted);font-size:12px;font-weight:500}
.chip i{width:6px;height:6px;border-radius:50%;background:var(--accent)}
.err{color:var(--danger)}
.dots{display:flex;gap:5px;padding:4px 0}.dots span{width:7px;height:7px;border-radius:50%;background:var(--muted);opacity:.35;animation:b 1.2s infinite}
.dots span:nth-child(2){animation-delay:.15s}.dots span:nth-child(3){animation-delay:.3s}
@keyframes b{0%,60%,100%{opacity:.35;transform:none}30%{opacity:.9;transform:translateY(-3px)}}
.hero{text-align:center;padding:9vh 0 28px}
.hero .logo{width:56px;height:56px;border-radius:15px;margin:0 auto 18px;box-shadow:0 8px 24px rgba(0,113,227,.25)}
.hero .logo svg{width:30px;height:30px}
.hero h2{font-size:30px;font-weight:700;letter-spacing:-.025em;margin:0 0 6px}
.hero p{color:var(--muted);margin:0}
.ideas{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:30px;text-align:left}
.ideas button{text-align:left;background:var(--surface);box-shadow:var(--shadow);border-radius:16px;padding:14px 16px;font-size:14px;font-weight:500;line-height:1.35;transition:transform .15s}
.ideas button:hover{transform:translateY(-1px)}.ideas small{display:block;color:var(--muted);font-size:12.5px;font-weight:400;margin-top:2px}
footer{padding:8px 20px 16px}
form{max-width:720px;margin:0 auto;display:flex;align-items:flex-end;gap:8px;background:var(--surface);border-radius:26px;
 padding:7px 7px 7px 18px;box-shadow:var(--shadow);border:1px solid var(--hair)}
textarea{flex:1;border:0;outline:0;resize:none;background:none;color:var(--text);font:inherit;padding:6px 0;max-height:180px}
textarea::placeholder{color:var(--muted)}
#send{width:34px;height:34px;flex:none;border-radius:50%;display:grid;place-items:center;background:var(--accent);color:#fff;transition:opacity .15s,transform .1s}
#send:disabled{background:var(--fill);color:var(--muted);cursor:default}#send:not(:disabled):active{transform:scale(.92)}
.note{max-width:720px;margin:8px auto 0;text-align:center;font-size:11.5px;color:var(--muted)}
@media (max-width:560px){.ideas{grid-template-columns:1fr}.me .bubble{max-width:88%}.bot .bubble{padding:16px 18px}}
</style></head><body>
<header><div class="brand"><div class="logo"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/></svg></div>
 <div><b>Tecnun Study Coach</b><small>{{AGENT}} · Microsoft Foundry</small></div></div>
 <button id="new" title="Nueva conversación"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>Nueva</button></header>
<main id="log"><div class="col" id="col"></div></main>
<footer><form id="f"><textarea id="q" rows="1" placeholder="Pregunta lo que quieras sobre IT-302"></textarea>
 <button id="send" disabled aria-label="Enviar"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg></button></form>
 <div class="note">Las respuestas salen de los documentos del curso. Comprueba fechas y notas en la guía docente.</div></footer>
<script>
const log=document.getElementById('log'),col=document.getElementById('col'),q=document.getElementById('q'),send=document.getElementById('send'),f=document.getElementById('f');
const LOGO=document.querySelector('.logo').outerHTML;
const TOOLS={'mcp:challenge4_kb':'Base de conocimiento','code_interpreter':'Code Interpreter','mcp:microsoft_learn':'Microsoft Learn','mcp:github_issues':'GitHub'};
const IDEAS=[['Plan de estudio','Prepara el Lab 4 en 3 días','Hazme un plan de estudio de 3 días para preparar el Lab 4 de IT-302, con bloques de tiempo y descansos.'],
 ['Tutorías','Quién da la asignatura y cuándo','¿Quién es la profesora de IT-302 y cuál es su horario de tutorías?'],
 ['Nota necesaria','Cuánto necesito en el final','Llevo un 6,5 en los labs y un 5 en el parcial. ¿Qué nota necesito en el final para aprobar?'],
 ['Reportar un problema','Abre un ticket al profesorado','El dataset del Lab 3 tiene filas duplicadas. ¿Puedes avisar al profesorado?']];
function hero(){col.innerHTML='<div class="hero">'+LOGO+'<h2>¿En qué te ayudo hoy?</h2><p>Guía docente, laboratorios, notas y planes de estudio de IT-302.</p><div class="ideas"></div></div>';
 const g=col.querySelector('.ideas');IDEAS.forEach(([t,s,p])=>{const b=document.createElement('button');b.innerHTML=t+'<small>'+s+'</small>';b.onclick=()=>{q.value=p;f.requestSubmit()};g.appendChild(b)})}
function bubble(cls){col.querySelector('.hero')?.remove();const r=document.createElement('div');r.className='row '+cls;const b=document.createElement('div');b.className='bubble';r.appendChild(b);col.appendChild(r);log.scrollTop=log.scrollHeight;return b}
function md(t){const n={};t=(t||'').replace(/【[^】]*】/g,c=>'<sup class="cite">'+(n[c]??=Object.keys(n).length+1)+'</sup>');return DOMPurify.sanitize(marked.parse(t))}
function chips(tools){return tools.length?'<div class="tools">'+tools.map(t=>'<span class="chip"><i></i>'+(TOOLS[t]||t)+'</span>').join('')+'</div>':''}
function grow(){q.style.height='auto';q.style.height=q.scrollHeight+'px';send.disabled=!q.value.trim()||q.readOnly}
f.onsubmit=async e=>{e.preventDefault();const m=q.value.trim();if(!m||q.readOnly)return;
 bubble('me').textContent=m;q.value='';q.readOnly=true;grow();
 const w=bubble('bot');w.innerHTML='<div class="dots"><span></span><span></span><span></span></div>';
 try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});const j=await r.json();
  w.innerHTML=j.error?'<p class="err"><strong>Error:</strong> '+DOMPurify.sanitize(j.error)+'</p>':chips(j.tools)+md(j.text);
  w.querySelectorAll('th,td').forEach(c=>{if(c.textContent.length<=16)c.style.whiteSpace='nowrap'});
 }catch(err){w.innerHTML='<p class="err">Error de red. ¿Sigue en marcha el servidor?</p>'}
 q.readOnly=false;grow();q.focus();log.scrollTop=w.parentNode.offsetTop-80};
q.oninput=grow;
q.onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();f.requestSubmit()}};
document.getElementById('new').onclick=async()=>{await fetch('/api/reset',{method:'POST'});hero();q.focus()};
hero();q.focus();
</script></body></html>"""

if __name__ == "__main__":
    main()
