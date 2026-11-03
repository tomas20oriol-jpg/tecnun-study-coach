"""Minimal web chat for the tecnun-study-coach agent (Flask)."""

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
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tecnun Study Coach</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.1.6/purify.min.js"></script>
<style>
:root{--bg:#f6f7f9;--card:#fff;--text:#1d2430;--muted:#667085;--accent:#1f3b5c;--me:#e7eef7;--border:#dde2e8}
@media (prefers-color-scheme:dark){:root{--bg:#12161c;--card:#1b2129;--text:#e6e9ee;--muted:#98a2b3;--accent:#8db4e2;--me:#22303f;--border:#2c3440}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif;display:flex;flex-direction:column;height:100vh}
header{padding:12px 16px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
header h1{font-size:17px;margin:0;color:var(--accent)}header small{color:var(--muted)}
button{background:var(--accent);color:var(--bg);border:0;border-radius:8px;padding:8px 14px;font:inherit;cursor:pointer}
button:disabled{opacity:.5}#new{background:transparent;color:var(--accent);border:1px solid var(--border)}
#log{flex:1;overflow-y:auto;padding:16px;max-width:860px;width:100%;margin:0 auto}
.msg{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 14px;margin:10px 0;overflow-x:auto}
.me{background:var(--me);margin-left:15%}.tools{font-size:12px;color:var(--muted)}
.msg table{border-collapse:collapse}.msg td,.msg th{border:1px solid var(--border);padding:4px 8px}
form{display:flex;gap:8px;padding:12px 16px;border-top:1px solid var(--border);max-width:860px;width:100%;margin:0 auto}
textarea{flex:1;resize:none;font:inherit;padding:8px;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--text)}
</style></head><body>
<header><div><h1>Tecnun Study Coach</h1><small>Agent: {{AGENT}} · Microsoft Foundry</small></div><button id="new">Nueva conversación</button></header>
<div id="log"><div class="msg">¡Hola! Pregúntame por tus exámenes, la guía de una asignatura, cuánto necesitas sacar en el final o pídeme un plan de estudio.</div></div>
<form id="f"><textarea id="q" rows="2" placeholder="Escribe tu pregunta... (Enter para enviar)"></textarea><button id="send">Enviar</button></form>
<script>
const log=document.getElementById('log'),q=document.getElementById('q'),send=document.getElementById('send');
function add(html,cls){const d=document.createElement('div');d.className='msg '+(cls||'');d.innerHTML=html;log.appendChild(d);log.scrollTop=log.scrollHeight;return d}
const md=t=>DOMPurify.sanitize(marked.parse(t||''));
document.getElementById('f').onsubmit=async e=>{e.preventDefault();const m=q.value.trim();if(!m)return;
 add(md(m),'me');q.value='';send.disabled=true;const w=add('<i>Pensando...</i>');
 try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});const j=await r.json();
  w.innerHTML=j.error?'<b>Error:</b> '+DOMPurify.sanitize(j.error):(j.tools.length?'<div class="tools">Herramientas: '+j.tools.join(', ')+'</div>':'')+md(j.text);
 }catch(err){w.textContent='Error de red: '+err}send.disabled=false;q.focus()};
q.onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();document.getElementById('f').requestSubmit()}};
document.getElementById('new').onclick=async()=>{await fetch('/api/reset',{method:'POST'});log.innerHTML='';add('Nueva conversación iniciada.')};
</script></body></html>"""

if __name__ == "__main__":
    main()
