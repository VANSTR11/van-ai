from flask import Flask, render_template_string, request, jsonify
import requests, json, os

app = Flask(__name__)
MISTRAL_KEY = os.environ.get("MISTRAL_KEY")
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(data):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(data, f)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>van-ai Terminal</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Courier New',monospace}
body{background:#000 url('/static/logo.jpg') center/cover no-repeat;color:#00ff41;overflow:hidden;height:100vh}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.4);z-index:0}

.wrapper{display:flex;height:100vh;position:relative;z-index:1}
.sidebar{width:200px;background:#0a0a0a;border-right:2px solid #00ff41;padding:10px;overflow-y:auto}
.sidebar h3{font-size:13px;margin-bottom:10px;color:#00ff41;border-bottom:1px solid #00ff41;padding-bottom:5px}
.chat-item{padding:6px 8px;margin:4px 0;background:#111;border:1px solid #0f0;cursor:pointer;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.chat-item:hover{background:#00ff41;color:#000}

.main{flex:1;display:flex;flex-direction:column}
.header{height:46px;background:#0a0a0a;border-bottom:2px solid #00ff41;display:flex;align-items:center;padding:0 12px;font-size:14px;font-weight:bold}
.header::before{content:'[root@van-ai]~# ';color:#00ff41}

#chat{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:6px}
.msg{max-width:75%;padding:6px 10px;border:1px solid #00ff41;border-radius:4px;font-size:12.5px;line-height:1.3;word-wrap:break-word;background:rgba(0,20,0,0.7)}
.user{margin-left:auto;border-color:#00aaff}
.user::before{content:'vanstr11@kali:~$ ';color:#00aaff}
.bot{margin-right:auto}
.bot::before{content:'van-ai@root:~$ ';color:#00ff41}

#inp{height:52px;background:#0a0a0a;border-top:2px solid #00ff41;display:flex;align-items:center;padding:0 10px;gap:6px;position:fixed;bottom:0;width:100%}
#text{flex:1;height:34px;padding:0 8px;background:#000;border:1px solid #00ff41;border-radius:3px;color:#00ff41;font-size:12.5px;outline:none}
#text::placeholder{color:#006600}
#send{height:34px;padding:0 12px;background:#000;border:1px solid #00ff41;border-radius:3px;color:#00ff41;font-size:12.5px;cursor:pointer}
#send:hover{background:#00ff41;color:#000}

@media(max-width:600px){.sidebar{width:150px}}
</style>
</head>
<body>
<div class="wrapper">
  <div class="sidebar">
    <h3>[ CHAT HISTORY ]</h3>
    <div id="history"></div>
  </div>

  <div class="main">
    <div class="header">van-ai Terminal v1.0</div>
    <div id="chat"></div>
    <div id="inp">
      <input id="text" placeholder="enter command..." autocomplete="off" />
      <button id="send" onclick="send()">RUN</button>
    </div>
  </div>
</div>

<script>
let history = {{ history|tojson }};

function loadHistorySidebar(){
  let div = document.getElementById('history');
  div.innerHTML = '';
  history.forEach((h,i)=>{
    div.innerHTML += `<div class="chat-item" onclick="alert('${h.replace(/'/g,"\\'")}')">${i+1}. ${h.substring(0,25)}...</div>`;
  });
}

async function send(){
  let t = document.getElementById('text');
  let chat = document.getElementById('chat');
  if(!t.value.trim()) return;

  chat.innerHTML += '<div class="msg user">'+t.value+'</div>';
  history.push(t.value);

  let msg = t.value;
  t.value = '';
  chat.scrollTop = chat.scrollHeight;

  let res = await fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({msg})
  });
  let data = await res.json();
  chat.innerHTML += '<div class="msg bot">'+data.reply+'</div>';
  chat.scrollTop = chat.scrollHeight;
  loadHistorySidebar();
}

document.getElementById('text').addEventListener('keypress', e => {if(e.key==='Enter') send()});
loadHistorySidebar();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML, history=load_history())

@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("msg", "")
    r = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {MISTRAL_KEY}"},
        json={"model": "mistral-small-latest", "messages": [{"role": "user", "content": msg}]}
    )
    reply = r.json()["choices"][0]["message"]["content"]
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
