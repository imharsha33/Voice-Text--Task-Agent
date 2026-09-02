/* ═══════════════════════════════════════════════════════════
   VoxFlow Agent — Ultra-Aesthetic Interactive Client Engine
   Implements:
   1. Tap-to-Record Voice (Browser MediaRecorder -> Whisper API)
   2. Master Start / Stop Agent Controls
   3. Real-Time Telemetry & Log Stream Filter
   4. Dynamic Waveform Visualization
   ═══════════════════════════════════════════════════════════ */

"use strict";

// ─── State ───────────────────────────────────────────────────────
let ws = null;
let reconnectTimer = null;
let agentActive = true;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let recordStream = null;
let currentFilter = "all";
let currentState = "idle";
let wavePhase = 0;
let waveAnimId = null;

// ─── DOM References ──────────────────────────────────────────────
const agentToggleBtn = document.getElementById("agentToggleBtn");
const agentSwitchLabel = document.getElementById("agentSwitchLabel");
const connPill = document.getElementById("connPill");
const connLabel = document.getElementById("connLabel");

const recordHeroBtn = document.getElementById("recordHeroBtn");
const recordStatusText = document.getElementById("recordStatusText");
const recordAura = document.getElementById("recordAura");
const heroWaveCanvas = document.getElementById("heroWaveCanvas");

const statusBadge = document.getElementById("statusBadge");
const activeCommandText = document.getElementById("activeCommandText");
const commandForm = document.getElementById("commandForm");
const textCommandInput = document.getElementById("textCommandInput");

const logScrollArea = document.getElementById("logScrollArea");
const logEmptyMsg = document.getElementById("logEmptyMsg");
const feedFilters = document.getElementById("feedFilters");
const clearLogsBtn = document.getElementById("clearLogsBtn");

const responseMessage = document.getElementById("responseMessage");
const audioBars = document.getElementById("audioBars");
const copyTextBtn = document.getElementById("copyTextBtn");

// ─── WebSocket Telemetry ──────────────────────────────────────────
const WS_URL = `ws://${location.host}/ws`;

function connectWS() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    setConnState(true);
    clearTimeout(reconnectTimer);
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleTelemetry(data);
    } catch (err) {
      console.warn("Parse error:", err);
    }
  };

  ws.onclose = () => {
    setConnState(false);
    reconnectTimer = setTimeout(connectWS, 2000);
  };

  ws.onerror = () => {
    ws.close();
  };
}

function setConnState(connected) {
  if (connected) {
    connPill.className = "conn-pill connected";
    connLabel.textContent = "Live Connected";
  } else {
    connPill.className = "conn-pill";
    connLabel.textContent = "Reconnecting...";
  }
}

// ─── Telemetry Handling ──────────────────────────────────────────
function handleTelemetry(data) {
  if (data.type === "status") {
    if (typeof data.agent_active === "boolean") {
      setAgentActiveState(data.agent_active);
    }
    updateStatusUI(data.state, data.command, data.response);
  } else if (data.type === "log") {
    renderLog(data);
  }
}

const STATUS_LABELS = {
  idle:         { label: "IDLE STANDBY",   cls: "idle" },
  listening:    { label: "LISTENING",      cls: "listening" },
  transcribing: { label: "TRANSCRIBING",   cls: "listening" },
  thinking:     { label: "THINKING",       cls: "thinking" },
  acting:       { label: "EXECUTING TOOL", cls: "acting" },
  speaking:     { label: "SPEAKING",       cls: "speaking" },
  error:        { label: "ERROR",          cls: "error" },
};

function updateStatusUI(state, command, response) {
  currentState = state || "idle";
  const cfg = STATUS_LABELS[currentState] || STATUS_LABELS.idle;

  statusBadge.className = `status-badge-chip ${cfg.cls}`;
  statusBadge.textContent = cfg.label;

  if (command && state !== "idle") {
    activeCommandText.innerHTML = `<span>"${escapeHtml(command)}"</span>`;
  }

  if (response) {
    responseMessage.textContent = response;
  }

  if (state === "speaking") {
    audioBars.classList.add("active");
  } else {
    audioBars.classList.remove("active");
  }
}

// ─── Master Start / Stop Agent ────────────────────────────────────
function setAgentActiveState(active) {
  agentActive = active;
  if (agentActive) {
    agentToggleBtn.className = "master-btn active";
    agentSwitchLabel.textContent = "AGENT ACTIVE";
  } else {
    agentToggleBtn.className = "master-btn stopped";
    agentSwitchLabel.textContent = "AGENT STOPPED";
  }
}

agentToggleBtn.addEventListener("click", async () => {
  const target = !agentActive;
  setAgentActiveState(target);

  try {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "toggle_agent", active: target }));
    } else {
      await fetch("/api/agent/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: target })
      });
    }
  } catch (err) {
    console.error("Toggle error:", err);
  }
});

// ─── Tap-to-Record Audio Engine ──────────────────────────────────
recordHeroBtn.addEventListener("click", async () => {
  if (!isRecording) {
    startVoiceRecording();
  } else {
    stopVoiceRecording();
  }
});

async function startVoiceRecording() {
  try {
    audioChunks = [];
    recordStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // Choose optimal mimeType
    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/mp4";

    mediaRecorder = new MediaRecorder(recordStream, { mimeType });

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: mimeType });
      await uploadVoiceAudio(audioBlob);
    };

    mediaRecorder.start(200);
    isRecording = true;

    // UI Updates
    recordHeroBtn.classList.add("recording");
    recordStatusText.textContent = "RECORDING... TAP TO SEND";
    updateStatusUI("listening", "", "Recording your voice...");

  } catch (err) {
    console.error("Microphone access failed:", err);
    alert("Microphone permission needed: Please allow microphone access in your browser.");
  }
}

function stopVoiceRecording() {
  if (!isRecording || !mediaRecorder) return;
  isRecording = false;

  recordHeroBtn.classList.remove("recording");
  recordStatusText.textContent = "TRANSCRIBING...";

  mediaRecorder.stop();
  if (recordStream) {
    recordStream.getTracks().forEach(t => t.stop());
    recordStream = null;
  }
}

async function uploadVoiceAudio(blob) {
  recordStatusText.textContent = "SENDING TO AI...";
  const formData = new FormData();
  formData.append("file", blob, "voice_command.webm");

  try {
    const res = await fetch("/api/voice_upload", {
      method: "POST",
      body: formData
    });
    const result = await res.json();
    if (result.transcription) {
      activeCommandText.innerHTML = `<span>"${escapeHtml(result.transcription)}"</span>`;
      await sendCommand(result.transcription);
    }
  } catch (err) {
    console.error("Voice upload error:", err);
  } finally {
    recordStatusText.textContent = "TAP TO RECORD";
  }
}

// ─── Direct Command Execution ─────────────────────────────────────
async function sendCommand(text) {
  if (!text || !text.trim()) return;
  const cmd = text.trim();

  activeCommandText.innerHTML = `<span>"${escapeHtml(cmd)}"</span>`;
  updateStatusUI("thinking", cmd, "Processing command...");

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "command", command: cmd }));
  } else {
    try {
      await fetch("/api/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd })
      });
    } catch (err) {
      console.error("Failed to execute command:", err);
    }
  }
}

commandForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = textCommandInput.value;
  if (text.trim()) {
    sendCommand(text);
    textCommandInput.value = "";
  }
});

// Quick Presets
document.querySelectorAll(".preset-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    const cmd = chip.dataset.cmd;
    if (cmd) sendCommand(cmd);
  });
});

// Copy response button
copyTextBtn.addEventListener("click", () => {
  const text = responseMessage.textContent;
  if (text) {
    navigator.clipboard.writeText(text).then(() => {
      const orig = copyTextBtn.innerHTML;
      copyTextBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
      setTimeout(() => { copyTextBtn.innerHTML = orig; }, 1500);
    });
  }
});

// ─── Log Stream Rendering ────────────────────────────────────────
const LOG_ICONS = {
  voice:   "🎙️",
  brain:   "🧠",
  action:  "⚡",
  success: "✅",
  error:   "❌",
  warning: "⚠️",
  info:    "ℹ️",
};

function renderLog(data) {
  if (logEmptyMsg) logEmptyMsg.style.display = "none";

  const level = data.level || "info";
  const icon = LOG_ICONS[level] || "•";
  const time = new Date((data.timestamp || Date.now() / 1000) * 1000).toLocaleTimeString();

  const item = document.createElement("div");
  item.className = `log-item ${level}`;
  item.dataset.level = level;

  if (currentFilter !== "all" && !matchesCategory(level, currentFilter)) {
    item.style.display = "none";
  }

  item.innerHTML = `
    <span class="log-item-icon">${icon}</span>
    <div class="log-item-body">
      <div class="log-item-msg">${escapeHtml(data.message)}</div>
      <div class="log-item-time">${time}</div>
    </div>
  `;

  logScrollArea.appendChild(item);

  while (logScrollArea.children.length > 250) {
    const first = logScrollArea.querySelector(".log-item");
    if (first) first.remove();
  }

  logScrollArea.scrollTop = logScrollArea.scrollHeight;
}

function matchesCategory(level, filter) {
  if (filter === "all") return true;
  if (filter === "voice" && level === "voice") return true;
  if (filter === "brain" && level === "brain") return true;
  if (filter === "action" && (level === "action" || level === "success")) return true;
  return false;
}

// Feed Filter Buttons
feedFilters.addEventListener("click", (e) => {
  const btn = e.target.closest(".filter-btn");
  if (!btn) return;

  feedFilters.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");

  currentFilter = btn.dataset.filter;
  const items = logScrollArea.querySelectorAll(".log-item");
  items.forEach(item => {
    item.style.display = matchesCategory(item.dataset.level, currentFilter) ? "" : "none";
  });
});

// Clear Logs
clearLogsBtn.addEventListener("click", () => {
  logScrollArea.querySelectorAll(".log-item").forEach(el => el.remove());
  if (logEmptyMsg) logEmptyMsg.style.display = "flex";
});

// ─── Waveform Canvas Visualizer ──────────────────────────────────
const ctx = heroWaveCanvas.getContext("2d");

function drawHeroWaveform() {
  const W = heroWaveCanvas.width;
  const H = heroWaveCanvas.height;
  ctx.clearRect(0, 0, W, H);

  const active = (isRecording || currentState === "speaking" || currentState === "acting");

  if (!active) {
    ctx.beginPath();
    ctx.moveTo(0, H / 2);
    for (let x = 0; x <= W; x += 4) {
      const y = H / 2 + Math.sin(x * 0.04 + wavePhase * 0.04) * 2;
      ctx.lineTo(x, y);
    }
    ctx.strokeStyle = "rgba(0, 210, 255, 0.35)";
    ctx.lineWidth = 1.5;
    ctx.stroke();
  } else {
    // Dynamic glowing sine waves
    const colors = [
      { color: "rgba(0, 210, 255, 0.8)", amp: 14, speed: 0.1 },
      { color: "rgba(59, 130, 246, 0.7)", amp: 10, speed: 0.08 },
      { color: "rgba(244, 63, 94, 0.6)", amp: 8, speed: 0.12 }
    ];

    colors.forEach((c, idx) => {
      ctx.beginPath();
      for (let x = 0; x <= W; x += 2) {
        const y = H / 2 + Math.sin(x * 0.03 + wavePhase * c.speed + idx) * c.amp;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = c.color;
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  }

  wavePhase++;
  waveAnimId = requestAnimationFrame(drawHeroWaveform);
}

drawHeroWaveform();

// ─── Utility ─────────────────────────────────────────────────────
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ─── Start Engine ────────────────────────────────────────────────
fetch("/status")
  .then(r => r.json())
  .then(data => {
    if (data.state) updateStatusUI(data.state, data.command, data.response);
    if (typeof data.agent_active === "boolean") setAgentActiveState(data.agent_active);
  })
  .catch(() => {});

connectWS();
