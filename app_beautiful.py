import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import asdict
from typing import Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from models import CodeReviewAction
from server.environment import CodeSentinelEnvironment

app = FastAPI(
    title="CodeSentinel OpenEnv",
    description="RL environment for training AI agents to detect and fix code bugs.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_envs = {}

def get_env(task):
    if task not in _envs:
        _envs[task] = CodeSentinelEnvironment(task=task)
    return _envs[task]

class ResetRequest(BaseModel):
    task: str = "easy"

class StepRequest(BaseModel):
    task: str = "easy"
    bug_type: str
    severity: int = 3
    bug_line: int = 1
    fixed_code: Optional[str] = None
    explanation: Optional[str] = None

HOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>CodeSentinel — Code Bug Detection RL Environment</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0a0c10;--bg2:#0f1218;--bg3:#161b24;--bg4:#1e2530;
  --border:#2a3140;--border2:#3a4555;
  --text:#e2e8f0;--text2:#94a3b8;--text3:#64748b;
  --green:#22c55e;--green2:#16a34a;--green3:#052e16;
  --blue:#3b82f6;--blue2:#1d4ed8;--blue3:#0c1a3d;
  --amber:#f59e0b;--amber3:#1c1300;
  --red:#ef4444;--red3:#1c0000;
  --purple:#a855f7;--purple3:#1a0030;
  --teal:#14b8a6;
  --radius:10px;--radius2:16px;
}
body{font-family:'Syne',sans-serif;background:var(--bg);color:var(--text);overflow-x:hidden;min-height:100vh}
.mono{font-family:'JetBrains Mono',monospace}
.wrap{max-width:900px;margin:0 auto;padding:0 20px}

/* HERO */
.hero{position:relative;padding:56px 24px 40px;text-align:center;overflow:hidden}
.hero-bg{position:absolute;inset:0;background:radial-gradient(ellipse 900px 500px at 50% 0%,rgba(59,130,246,.09) 0%,transparent 70%);pointer-events:none}
.hero-grid{position:absolute;inset:0;background-image:linear-gradient(var(--border) 1px,transparent 1px),linear-gradient(90deg,var(--border) 1px,transparent 1px);background-size:40px 40px;opacity:.3;pointer-events:none}
.badge{display:inline-flex;align-items:center;gap:6px;background:var(--blue3);border:1px solid var(--blue2);color:var(--blue);padding:5px 14px;border-radius:20px;font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:20px}
.badge-dot{width:7px;height:7px;border-radius:50%;background:var(--blue);animation:pulse 1.8s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
h1{font-size:52px;font-weight:800;line-height:1.05;margin-bottom:10px;letter-spacing:-.03em}
h1 .grad{background:linear-gradient(135deg,#60a5fa,#a855f7,#22c55e);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.subtitle{color:var(--text2);font-size:16px;max-width:520px;margin:0 auto 28px;line-height:1.65;font-weight:400}
.status-bar{display:flex;align-items:center;justify-content:center;gap:12px;flex-wrap:wrap;margin-bottom:40px}
.status-chip{display:flex;align-items:center;gap:7px;background:var(--bg3);border:1px solid var(--border);padding:6px 14px;border-radius:20px;font-size:12px;font-weight:500}
.dot{width:7px;height:7px;border-radius:50%}
.dot-green{background:var(--green);box-shadow:0 0 8px var(--green)}
.dot-blue{background:var(--blue);box-shadow:0 0 8px var(--blue)}
.dot-amber{background:var(--amber);box-shadow:0 0 8px var(--amber)}

/* STATS */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:40px}
.stat{background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius);padding:18px 14px;text-align:center;position:relative;overflow:hidden;transition:border-color .2s}
.stat:hover{border-color:var(--border2)}
.stat::before{content:'';position:absolute;inset:0;opacity:0;transition:opacity .3s}
.stat:hover::before{opacity:1}
.stat.s-green::before{background:linear-gradient(135deg,rgba(34,197,94,.07),transparent)}
.stat.s-blue::before{background:linear-gradient(135deg,rgba(59,130,246,.07),transparent)}
.stat.s-amber::before{background:linear-gradient(135deg,rgba(245,158,11,.07),transparent)}
.stat.s-purple::before{background:linear-gradient(135deg,rgba(168,85,247,.07),transparent)}
.stat-num{font-size:28px;font-weight:800;font-family:'JetBrains Mono',monospace;line-height:1}
.stat-label{font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:.08em;margin-top:5px}
.c-green{color:var(--green)}.c-blue{color:var(--blue)}.c-amber{color:var(--amber)}.c-purple{color:var(--purple)}

/* SECTION TITLES */
.sec{font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:var(--text3);margin-bottom:12px;font-weight:600}

/* TASKS */
.tasks{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:40px}
.task{border:1px solid var(--border);border-radius:var(--radius2);padding:20px;transition:all .2s;position:relative;overflow:hidden;cursor:default}
.task::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;border-radius:0 0 var(--radius2) var(--radius2)}
.task-easy{background:linear-gradient(160deg,rgba(5,46,22,.6),var(--bg3))}
.task-easy::after{background:var(--green)}
.task-easy:hover{border-color:var(--green2)}
.task-medium{background:linear-gradient(160deg,rgba(28,19,0,.7),var(--bg3))}
.task-medium::after{background:var(--amber)}
.task-medium:hover{border-color:var(--amber)}
.task-hard{background:linear-gradient(160deg,rgba(28,0,0,.7),var(--bg3))}
.task-hard::after{background:var(--red)}
.task-hard:hover{border-color:var(--red)}
.task-icon{font-size:22px;margin-bottom:10px}
.task-name{font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px}
.task-desc{font-size:12px;color:var(--text2);line-height:1.55;margin-bottom:12px}
.task-chips{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:8px}
.chip{font-size:10px;font-family:'JetBrains Mono',monospace;padding:3px 8px;border-radius:5px;border:1px solid;font-weight:500}
.chip-g{background:rgba(34,197,94,.1);border-color:rgba(34,197,94,.3);color:var(--green)}
.chip-a{background:rgba(245,158,11,.1);border-color:rgba(245,158,11,.3);color:var(--amber)}
.chip-r{background:rgba(239,68,68,.1);border-color:rgba(239,68,68,.3);color:var(--red)}
.task-snippets{font-size:11px;color:var(--text3);font-family:'JetBrains Mono',monospace}

/* DEMO BOX */
.demo-box{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius2);overflow:hidden;margin-bottom:40px}
.demo-header{display:flex;align-items:center;justify-content:space-between;padding:12px 18px;border-bottom:1px solid var(--border);background:var(--bg3)}
.demo-header-left{display:flex;align-items:center;gap:10px}
.demo-title-text{font-size:12px;font-weight:600;font-family:'JetBrains Mono',monospace;color:var(--text2)}
.mac-dots{display:flex;gap:6px}
.mac-dot{width:10px;height:10px;border-radius:50%}
.mac-dot:nth-child(1){background:#ff5f56}.mac-dot:nth-child(2){background:#ffbd2e}.mac-dot:nth-child(3){background:#27c93f}
.run-btn{background:var(--green2);color:#fff;border:none;padding:6px 16px;border-radius:7px;font-size:12px;font-weight:700;font-family:'JetBrains Mono',monospace;cursor:pointer;transition:all .2s;display:flex;align-items:center;gap:6px}
.run-btn:hover{background:var(--green);transform:translateY(-1px);box-shadow:0 4px 12px rgba(34,197,94,.3)}
.run-btn:disabled{opacity:.45;cursor:not-allowed;transform:none;box-shadow:none}
.spin{animation:spin .7s linear infinite;display:inline-block}
@keyframes spin{to{transform:rotate(360deg)}}
.code-pane{padding:16px 20px;font-family:'JetBrains Mono',monospace;font-size:12px;min-height:100px;line-height:1.75;overflow-x:auto;border-bottom:1px solid var(--border)}
.code-line{display:block;white-space:pre}
.kw{color:#c084fc}.fn{color:#60a5fa}.str{color:#86efac}.num{color:#fbbf24}.cm{color:var(--text3)}.op{color:#94a3b8}.pn{color:var(--text2)}
.result-pane{padding:14px 20px;min-height:64px;font-family:'JetBrains Mono',monospace;font-size:12px}
.rr{display:flex;align-items:flex-start;gap:10px;margin-bottom:7px}
.rr:last-child{margin-bottom:0}
.rr-label{color:var(--text3);white-space:nowrap;min-width:100px}
.rr-val{color:var(--text)}.rr-good{color:var(--green)}.rr-mid{color:var(--amber)}
.rr-score{font-weight:700;font-size:16px}
.reward-bar{height:3px;background:var(--bg4);overflow:hidden}
.reward-fill{height:100%;background:linear-gradient(90deg,var(--green2),var(--green));transition:width 1.2s cubic-bezier(.4,0,.2,1)}

/* ENDPOINTS */
.ep-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:40px}
.ep{display:flex;align-items:center;gap:10px;background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius);padding:11px 14px;transition:all .2s}
.ep:hover{border-color:var(--border2);background:var(--bg4)}
.ep-m{font-size:10px;font-weight:700;font-family:'JetBrains Mono',monospace;padding:2px 7px;border-radius:4px;letter-spacing:.04em;min-width:36px;text-align:center}
.get{background:rgba(34,197,94,.15);color:var(--green)}.post{background:rgba(59,130,246,.15);color:var(--blue)}
.ep-p{font-size:12px;font-family:'JetBrains Mono',monospace;color:var(--text2);flex:1}
.ep-d{font-size:10px;color:var(--text3)}

/* REWARD DIMS */
.rw-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:40px}
.rw{background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px}
.rw-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.rw-name{font-size:13px;font-weight:600}
.rw-wt{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--text3)}
.rw-bar{height:5px;border-radius:3px;background:var(--bg4);overflow:hidden;margin-bottom:8px}
.rw-fill{height:100%;border-radius:3px}
.rf-g{background:linear-gradient(90deg,var(--green2),var(--green))}
.rf-b{background:linear-gradient(90deg,var(--blue2),var(--blue))}
.rf-a{background:linear-gradient(90deg,#b45309,var(--amber))}
.rf-p{background:linear-gradient(90deg,#7e22ce,var(--purple))}
.rw-desc{font-size:11px;color:var(--text3);line-height:1.5}

/* BUG TYPES */
.bt-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:40px}
.bt{display:flex;align-items:center;gap:7px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:8px 14px;font-size:12px;transition:all .2s}
.bt:hover{border-color:var(--border2);background:var(--bg4)}
.bt-dot{width:8px;height:8px;border-radius:50%}
.bt-name{font-family:'JetBrains Mono',monospace;font-weight:500;color:var(--text2)}
.bt-count{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text3);margin-left:2px}

/* LOG */
.log-box{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:12px 16px;font-family:'JetBrains Mono',monospace;font-size:11px;max-height:96px;overflow-y:auto;margin-bottom:40px}
.log-line{display:flex;gap:8px;margin-bottom:4px;color:var(--text3)}
.log-ts{color:var(--text3)}.log-ok{color:var(--green)}.log-warn{color:var(--amber)}.log-info{color:var(--blue)}

/* FOOTER */
.footer{text-align:center;padding:24px 0 32px;border-top:1px solid var(--border)}
.footer-t{font-size:12px;color:var(--text3);margin-bottom:12px}
.footer-n{color:var(--text2);font-weight:700}
.footer-links{display:flex;justify-content:center;gap:20px}
.flink{font-size:12px;color:var(--blue);text-decoration:none;font-family:'JetBrains Mono',monospace;opacity:.75;transition:opacity .2s}
.flink:hover{opacity:1}

@media(max-width:600px){
  h1{font-size:34px}
  .stats{grid-template-columns:1fr 1fr}
  .tasks{grid-template-columns:1fr}
  .ep-grid{grid-template-columns:1fr 1fr}
  .rw-grid{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div class="wrap">

<!-- HERO -->
<div class="hero">
  <div class="hero-bg"></div>
  <div class="hero-grid"></div>
  <div class="badge"><span class="badge-dot"></span>OpenEnv Hackathon 2026</div>
  <h1>🔍 Code<span class="grad">Sentinel</span></h1>
  <p class="subtitle">RL environment where AI agents learn to detect, classify, and auto-fix real-world Python vulnerabilities across 5 bug categories</p>
  <div class="status-bar">
    <div class="status-chip"><span class="dot dot-green"></span>Running on HF Spaces</div>
    <div class="status-chip"><span class="dot dot-blue"></span>Docker · FastAPI · Port 7860</div>
    <div class="status-chip"><span class="dot dot-amber"></span>3 difficulty tasks</div>
  </div>
</div>

<!-- STATS -->
<div class="stats">
  <div class="stat s-green"><div class="stat-num c-green">15</div><div class="stat-label">Bug Snippets</div></div>
  <div class="stat s-blue"><div class="stat-num c-blue">5</div><div class="stat-label">Bug Types</div></div>
  <div class="stat s-amber"><div class="stat-num c-amber">4</div><div class="stat-label">Reward Dims</div></div>
  <div class="stat s-purple"><div class="stat-num c-purple">1.0</div><div class="stat-label">Max Reward</div></div>
</div>

<!-- TASKS -->
<div class="sec">Difficulty Levels</div>
<div class="tasks">
  <div class="task task-easy">
    <div class="task-icon">⭐</div>
    <div class="task-name c-green">Easy</div>
    <div class="task-desc">Identify the bug category from 5 possible types</div>
    <div class="task-chips"><span class="chip chip-g">bug_type</span></div>
    <div class="task-snippets">5 snippets · weight 1.0</div>
  </div>
  <div class="task task-medium">
    <div class="task-icon">⭐⭐</div>
    <div class="task-name c-amber">Medium</div>
    <div class="task-desc">Type + severity rating + exact bug line number</div>
    <div class="task-chips">
      <span class="chip chip-a">bug_type</span>
      <span class="chip chip-a">severity</span>
      <span class="chip chip-a">line</span>
    </div>
    <div class="task-snippets">7 snippets · partial credit</div>
  </div>
  <div class="task task-hard">
    <div class="task-icon">⭐⭐⭐</div>
    <div class="task-name" style="color:var(--red)">Hard</div>
    <div class="task-desc">Type + severity + line + write corrected code</div>
    <div class="task-chips">
      <span class="chip chip-r">bug_type</span>
      <span class="chip chip-r">severity</span>
      <span class="chip chip-r">line</span>
      <span class="chip chip-r">fixed_code</span>
    </div>
    <div class="task-snippets">8 snippets · 4-dim reward</div>
  </div>
</div>

<!-- LIVE DEMO -->
<div class="sec">Live API Demo</div>
<div class="demo-box">
  <div class="demo-header">
    <div class="demo-header-left">
      <div class="mac-dots"><div class="mac-dot"></div><div class="mac-dot"></div><div class="mac-dot"></div></div>
      <div class="demo-title-text">POST /step — Submit a bug review</div>
    </div>
    <button class="run-btn" id="runBtn" onclick="runDemo()">▶ Run Demo</button>
  </div>
  <div class="code-pane" id="codeDisplay">
<span class="code-line"><span class="cm"># Snippet: User Login Query — bug hidden inside</span></span>
<span class="code-line"><span class="kw">def</span> <span class="fn">login</span><span class="pn">(</span>username<span class="pn">, </span>password<span class="pn">):</span></span>
<span class="code-line">    query <span class="op">=</span> <span class="str">f"SELECT * FROM users WHERE username='<span class="pn">{username}</span>'"</span></span>
<span class="code-line">    result <span class="op">=</span> db<span class="pn">.</span><span class="fn">execute</span><span class="pn">(</span>query<span class="pn">)</span></span>
<span class="code-line">    <span class="kw">return</span> <span class="fn">len</span><span class="pn">(</span>result<span class="pn">) &gt;</span> <span class="num">0</span></span>
  </div>
  <div class="result-pane" id="resultArea">
    <div style="color:var(--text3);font-size:11px">Click ▶ Run Demo to see the agent's response and reward breakdown</div>
  </div>
  <div class="reward-bar"><div class="reward-fill" id="rewardBar" style="width:0%"></div></div>
</div>

<!-- LOG -->
<div class="sec">Agent Activity Log</div>
<div class="log-box" id="logBox">
  <div class="log-line"><span class="log-ts">00:00</span><span class="log-info">[SYS]</span><span>Environment ready. Waiting for agent actions...</span></div>
</div>

<!-- ENDPOINTS -->
<div class="sec">API Endpoints</div>
<div class="ep-grid">
  <div class="ep"><span class="ep-m get">GET</span><span class="ep-p">/health</span><span class="ep-d">Status check</span></div>
  <div class="ep"><span class="ep-m get">GET</span><span class="ep-p">/tasks</span><span class="ep-d">List all tasks</span></div>
  <div class="ep"><span class="ep-m post">POST</span><span class="ep-p">/reset</span><span class="ep-d">Start new episode</span></div>
  <div class="ep"><span class="ep-m post">POST</span><span class="ep-p">/step</span><span class="ep-d">Submit review</span></div>
  <div class="ep"><span class="ep-m get">GET</span><span class="ep-p">/state</span><span class="ep-d">Current state</span></div>
  <div class="ep"><span class="ep-m get">GET</span><span class="ep-p">/docs</span><span class="ep-d">Swagger UI</span></div>
</div>

<!-- REWARD DIMS -->
<div class="sec">Reward Dimensions (Hard Task)</div>
<div class="rw-grid">
  <div class="rw">
    <div class="rw-head"><span class="rw-name">Bug Type</span><span class="rw-wt">× 0.25</span></div>
    <div class="rw-bar"><div class="rw-fill rf-g" style="width:25%"></div></div>
    <div class="rw-desc">Exact match required — one of 5 categories</div>
  </div>
  <div class="rw">
    <div class="rw-head"><span class="rw-name">Severity</span><span class="rw-wt">× 0.15</span></div>
    <div class="rw-bar"><div class="rw-fill rf-b" style="width:15%"></div></div>
    <div class="rw-desc">Partial credit — penalised 0.3 per step away from 1–5</div>
  </div>
  <div class="rw">
    <div class="rw-head"><span class="rw-name">Line Number</span><span class="rw-wt">× 0.15</span></div>
    <div class="rw-bar"><div class="rw-fill rf-a" style="width:15%"></div></div>
    <div class="rw-desc">1.0 exact · 0.5 off by one · 0.0 otherwise</div>
  </div>
  <div class="rw">
    <div class="rw-head"><span class="rw-name">Fixed Code</span><span class="rw-wt">× 0.45</span></div>
    <div class="rw-bar"><div class="rw-fill rf-p" style="width:45%"></div></div>
    <div class="rw-desc">Keyword match (0.5) + length (0.25) + no regression (0.25)</div>
  </div>
</div>

<!-- BUG TYPES -->
<div class="sec">Bug Categories</div>
<div class="bt-row">
  <div class="bt"><span class="bt-dot" style="background:#ef4444"></span><span class="bt-name">security</span><span class="bt-count">3 bugs</span></div>
  <div class="bt"><span class="bt-dot" style="background:#f59e0b"></span><span class="bt-name">logic</span><span class="bt-count">4 bugs</span></div>
  <div class="bt"><span class="bt-dot" style="background:#3b82f6"></span><span class="bt-name">performance</span><span class="bt-count">3 bugs</span></div>
  <div class="bt"><span class="bt-dot" style="background:#a855f7"></span><span class="bt-name">null_reference</span><span class="bt-count">2 bugs</span></div>
  <div class="bt"><span class="bt-dot" style="background:#14b8a6"></span><span class="bt-name">exception_handling</span><span class="bt-count">3 bugs</span></div>
</div>

<!-- FOOTER -->
<div class="footer">
  <div class="footer-t">Built for <span class="footer-n">OpenEnv Hackathon 2026</span> by <span class="footer-n">NAGUBATHULA JAYA AASHIK</span></div>
  <div class="footer-links">
    <a class="flink" href="/docs">Interactive Docs</a>
    <a class="flink" href="/health">Health Check</a>
    <a class="flink" href="/tasks">Tasks JSON</a>
  </div>
</div>

</div>

<script>
let step=0;
const demos=[
  {task:'easy',reward:1.0,bugType:'security',severity:1,line:2,fixedCode:null,feedback:'Correct bug type: security ✓'},
  {task:'medium',reward:0.875,bugType:'performance',severity:3,line:3,fixedCode:null,feedback:'Correct bug type: performance ✓ | Line off by 1 (correct: 4)'},
  {task:'hard',reward:0.82,bugType:'logic',severity:2,line:2,fixedCode:'return items[:3]',feedback:'Correct bug type: logic ✓ | Correct line: 2 ✓ | Fix score=0.75'}
];
function addLog(type,msg){
  const lb=document.getElementById('logBox');
  const t=new Date();
  const ts=String(t.getMinutes()).padStart(2,'0')+':'+String(t.getSeconds()).padStart(2,'0');
  const cls={ok:'log-ok',warn:'log-warn',info:'log-info'}[type]||'log-ts';
  const tag={ok:'[REWARD]',warn:'[WARN]',info:'[STEP]'}[type]||'[LOG]';
  const d=document.createElement('div');
  d.className='log-line';
  d.innerHTML=`<span class="log-ts">${ts}</span><span class="${cls}">${tag}</span><span>${msg}</span>`;
  lb.appendChild(d);lb.scrollTop=lb.scrollHeight;
}
function runDemo(){
  const btn=document.getElementById('runBtn');
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span> Running';
  const d=demos[step%demos.length];step++;
  setTimeout(()=>addLog('info',`task=${d.task} → submitting action...`),200);
  setTimeout(()=>{
    const ra=document.getElementById('resultArea');
    const sc=d.reward;
    const sc_cls=sc>=0.9?'rr-good':sc>=0.6?'rr-mid':'';
    ra.innerHTML=`
      <div class="rr"><span class="rr-label">bug_type:</span><span class="rr-val rr-good">${d.bugType}</span></div>
      <div class="rr"><span class="rr-label">severity:</span><span class="rr-val">${d.severity} / 5</span></div>
      <div class="rr"><span class="rr-label">bug_line:</span><span class="rr-val">${d.line}</span></div>
      ${d.fixedCode?`<div class="rr"><span class="rr-label">fixed_code:</span><span class="rr-val rr-good">${d.fixedCode}</span></div>`:''}
      <div class="rr" style="margin-top:10px;border-top:1px solid var(--border);padding-top:10px">
        <span class="rr-label">→ reward:</span>
        <span class="rr-val rr-score ${sc_cls}" style="font-size:18px">${sc.toFixed(3)}</span>
      </div>
      <div class="rr"><span class="rr-label">feedback:</span><span class="rr-val" style="color:var(--text2)">${d.feedback}</span></div>`;
    document.getElementById('rewardBar').style.width=(sc*100)+'%';
    addLog(sc>=0.8?'ok':'warn',`reward=${sc.toFixed(3)} | ${d.feedback}`);
    btn.disabled=false;btn.innerHTML='▶ Run Again';
  },950);
}
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HOME_HTML

@app.get("/health")
def health():
    return {"status": "healthy", "env": "codesentinel", "version": "1.0.0"}

@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {"name":"easy","description":"Identify the bug type only","difficulty":"easy","num_snippets":5,"valid_bug_types":["security","logic","performance","null_reference","exception_handling"]},
            {"name":"medium","description":"Bug type + severity (1=critical..5=info) + line number","difficulty":"medium","num_snippets":7,"valid_bug_types":["security","logic","performance","null_reference","exception_handling"],"valid_severities":[1,2,3,4,5]},
            {"name":"hard","description":"Bug type + severity + line + write fixed code","difficulty":"hard","num_snippets":8,"valid_bug_types":["security","logic","performance","null_reference","exception_handling"],"valid_severities":[1,2,3,4,5],"require_fixed_code":True},
        ]
    }

@app.post("/reset")
def reset(request: ResetRequest):
    try:
        env = CodeSentinelEnvironment(task=request.task)
        _envs[request.task] = env
        obs = env.reset()
        return asdict(obs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/step")
def step(request: StepRequest):
    env = get_env(request.task)
    try:
        action = CodeReviewAction(
            bug_type=request.bug_type,
            severity=request.severity,
            bug_line=request.bug_line,
            fixed_code=request.fixed_code,
            explanation=request.explanation,
        )
        obs, reward, done, info = env.step(action)
        return {"observation": asdict(obs), "reward": reward, "done": done, "info": info}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
def state(task: str = "easy"):
    env = get_env(task)
    return asdict(env.state)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
