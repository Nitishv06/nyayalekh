// NyayaLekh frontend — plain JS, no build step needed.
// API_BASE: empty string means "same origin" (backend serves this file too).
const API_BASE = "";

let state = {
  facts: null,
  analysis: null,
};

// ---------- Step navigation ----------
function goToStep(n) {
  for (let i = 1; i <= 4; i++) {
    document.getElementById(`panel-${i}`).classList.toggle("hidden", i !== n);
  }
  document.querySelectorAll(".step").forEach((el) => {
    const step = parseInt(el.dataset.step, 10);
    el.classList.toggle("active", step === n);
    el.classList.toggle("done", step < n);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ---------- Speech-to-text (Web Speech API, browser-native, no backend cost) ----------
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognizer = null;
let recording = false;

function setupMic() {
  const micBtn = document.getElementById("mic-btn");
  const micLabel = document.getElementById("mic-label");
  if (!SpeechRecognition) {
    micLabel.textContent = "Voice input not supported here";
    micBtn.disabled = true;
    return;
  }
  recognizer = new SpeechRecognition();
  recognizer.continuous = true;
  recognizer.interimResults = true;
  recognizer.lang = "en-IN"; // change to 'hi-IN' or 'te-IN' if you add a language picker before recording

  const textarea = document.getElementById("narrative-input");
  let finalTranscript = textarea.value;

  recognizer.onresult = (event) => {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript + " ";
      } else {
        interim += transcript;
      }
    }
    textarea.value = finalTranscript + interim;
  };

  recognizer.onerror = () => stopRecording();
  recognizer.onend = () => { if (recording) recognizer.start(); }; // keep listening until user stops

  micBtn.addEventListener("click", () => {
    if (recording) stopRecording();
    else startRecording();
  });

  function startRecording() {
    finalTranscript = textarea.value ? textarea.value + " " : "";
    recognizer.start();
    recording = true;
    micBtn.classList.add("recording");
    micLabel.textContent = "Stop recording";
  }
  function stopRecording() {
    recording = false;
    try { recognizer.stop(); } catch (e) {}
    micBtn.classList.remove("recording");
    micLabel.textContent = "Speak instead";
  }
}

// ---------- API helpers ----------
async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

function linesToList(text) {
  return text.split("\n").map((l) => l.trim()).filter(Boolean);
}
function listToLines(list) {
  return (list || []).join("\n");
}

// ---------- Step 1: Extract facts ----------
document.getElementById("btn-extract").addEventListener("click", async () => {
  const narrative = document.getElementById("narrative-input").value.trim();
  const statusEl = document.getElementById("extract-status");
  if (!narrative) {
    statusEl.textContent = "Please describe what happened first.";
    statusEl.className = "status-line error";
    return;
  }
  statusEl.textContent = "Reading your narrative and extracting facts…";
  statusEl.className = "status-line";
  document.getElementById("btn-extract").disabled = true;

  try {
    const facts = await apiPost("/api/extract-facts", { narrative });
    state.facts = facts;
    populateFactsForm(facts);
    statusEl.textContent = "";
    goToStep(2);
  } catch (e) {
    statusEl.textContent = `Something went wrong: ${e.message}`;
    statusEl.className = "status-line error";
  } finally {
    document.getElementById("btn-extract").disabled = false;
  }
});

function populateFactsForm(facts) {
  document.getElementById("f-name").value = facts.complainant_name || "";
  document.getElementById("f-datetime").value = facts.date_time || "";
  document.getElementById("f-location").value = facts.location || "";
  document.getElementById("f-accused").value = facts.accused_description || "";
  document.getElementById("f-summary").value = facts.narrative_summary || "";
  document.getElementById("f-acts").value = listToLines(facts.acts_described);
  document.getElementById("f-loss").value = facts.loss_or_harm || "";
  document.getElementById("f-evidence").value = listToLines(facts.evidence_mentioned);
  document.getElementById("f-witnesses").value = listToLines(facts.witnesses_mentioned);

  const clarifyBox = document.getElementById("clarify-box");
  const clarifyList = document.getElementById("clarify-list");
  clarifyList.innerHTML = "";
  if (facts.clarifying_questions && facts.clarifying_questions.length) {
    facts.clarifying_questions.forEach((q) => {
      const li = document.createElement("li");
      li.textContent = q;
      clarifyList.appendChild(li);
    });
    clarifyBox.classList.remove("hidden");
  } else {
    clarifyBox.classList.add("hidden");
  }
}

function readFactsForm() {
  return {
    complainant_name: document.getElementById("f-name").value.trim() || null,
    date_time: document.getElementById("f-datetime").value.trim() || null,
    location: document.getElementById("f-location").value.trim() || null,
    accused_description: document.getElementById("f-accused").value.trim() || null,
    narrative_summary: document.getElementById("f-summary").value.trim(),
    acts_described: linesToList(document.getElementById("f-acts").value),
    loss_or_harm: document.getElementById("f-loss").value.trim() || null,
    evidence_mentioned: linesToList(document.getElementById("f-evidence").value),
    witnesses_mentioned: linesToList(document.getElementById("f-witnesses").value),
  };
}

document.getElementById("btn-back-1").addEventListener("click", () => goToStep(1));

// ---------- Step 2 -> 3: Analyze ----------
document.getElementById("btn-analyze").addEventListener("click", async () => {
  const facts = readFactsForm();
  state.facts = facts;
  const statusEl = document.getElementById("analyze-status");
  statusEl.textContent = "Checking your facts against BNS section ingredients…";
  statusEl.className = "status-line";
  document.getElementById("btn-analyze").disabled = true;

  try {
    const analysis = await apiPost("/api/analyze", { facts });
    state.analysis = analysis;
    renderAnalysis(analysis);
    statusEl.textContent = "";
    goToStep(3);
  } catch (e) {
    statusEl.textContent = `Something went wrong: ${e.message}`;
    statusEl.className = "status-line error";
  } finally {
    document.getElementById("btn-analyze").disabled = false;
  }
});

function verdictClass(v) {
  if (v === "likely_applies") return "likely";
  if (v === "possible_but_unclear") return "possible";
  return "unlikely";
}
function verdictLabel(v) {
  return { likely_applies: "Likely applies", possible_but_unclear: "Possible, unclear", unlikely_to_apply: "Unlikely" }[v] || v;
}
function ingIcon(s) {
  if (s === "yes") return '<span class="ing-yes">✓ satisfied</span>';
  if (s === "no") return '<span class="ing-no">✗ not satisfied</span>';
  return '<span class="ing-unclear">? unclear</span>';
}

function renderAnalysis(analysis) {
  const flagsBox = document.getElementById("flags-box");
  if (analysis.flags && analysis.flags.length) {
    flagsBox.innerHTML = "<strong>⚠ Please note:</strong><ul>" +
      analysis.flags.map((f) => `<li>${f}</li>`).join("") + "</ul>";
    flagsBox.classList.remove("hidden");
  } else {
    flagsBox.classList.add("hidden");
  }

  const list = document.getElementById("matches-list");
  list.innerHTML = "";

  const sorted = [...(analysis.matches || [])].sort((a, b) => {
    const order = { likely_applies: 0, possible_but_unclear: 1, unlikely_to_apply: 2 };
    return order[a.verdict] - order[b.verdict];
  });

  sorted.forEach((m) => {
    const off = OFFENCE_LOOKUP[m.offence_code];
    if (!off) return;
    const card = document.createElement("div");
    card.className = `offence-card ${verdictClass(m.verdict)}`;
    const primaryTag = m.offence_code === analysis.recommended_primary_offence
      ? ' <span style="color:var(--amber); font-weight:700; font-size:12px;">★ MOST APPLICABLE</span>' : "";

    card.innerHTML = `
      <div class="offence-head">
        <div>
          <div class="offence-title">${off.title}${primaryTag}</div>
          <span class="offence-section">${off.section}</span>
          <span style="font-size:12px;color:var(--text-muted);"> · formerly ${off.old_ipc}</span>
        </div>
        <span class="verdict-badge ${m.verdict}">${verdictLabel(m.verdict)}</span>
      </div>
      <p class="offence-reasoning">${m.overall_reasoning || ""}</p>
      <span class="ingredients-toggle">View ingredient-by-ingredient analysis</span>
      <ul class="ingredients-list hidden">
        ${(m.ingredient_analysis || []).map((ia) => `<li>${ingIcon(ia.satisfied)} — ${ia.ingredient}<br><span style="color:var(--text-muted)">${ia.reasoning}</span></li>`).join("")}
      </ul>
      <div class="offence-meta">
        ${off.cognizable ? "Cognizable" : "Non-cognizable"} · ${off.bailable ? "Bailable" : "Non-bailable"} · ${off.punishment}
      </div>
    `;
    const toggle = card.querySelector(".ingredients-toggle");
    const ul = card.querySelector(".ingredients-list");
    toggle.addEventListener("click", () => ul.classList.toggle("hidden"));

    list.appendChild(card);
  });
}

document.getElementById("btn-back-2").addEventListener("click", () => goToStep(2));
document.getElementById("btn-goto-pdf").addEventListener("click", () => goToStep(4));

// ---------- Step 4: Generate PDF ----------
document.getElementById("btn-download").addEventListener("click", async () => {
  const statusEl = document.getElementById("pdf-status");
  const langLabel = document.querySelector('input[name="lang"]:checked').value;
  statusEl.textContent = "Building your complaint document…";
  statusEl.className = "status-line";
  document.getElementById("btn-download").disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/generate-pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ facts: state.facts, analysis: state.analysis, language_label: langLabel }),
    });
    if (!res.ok) throw new Error("PDF generation failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "NyayaLekh_Complaint.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    statusEl.textContent = "Downloaded. Good luck — and take a copy for yourself too.";
    statusEl.className = "status-line success";
  } catch (e) {
    statusEl.textContent = `Something went wrong: ${e.message}`;
    statusEl.className = "status-line error";
  } finally {
    document.getElementById("btn-download").disabled = false;
  }
});

document.getElementById("btn-restart").addEventListener("click", () => {
  state = { facts: null, analysis: null };
  document.getElementById("narrative-input").value = "";
  goToStep(1);
});

// ---------- Load offence metadata for rendering ----------
let OFFENCE_LOOKUP = {};
async function loadOffences() {
  try {
    const res = await fetch(`${API_BASE}/api/offences`);
    const data = await res.json();
    data.offences.forEach((o) => { OFFENCE_LOOKUP[o.code] = o; });
  } catch (e) {
    console.error("Could not load offence metadata", e);
  }
}

// ---------- Init ----------
loadOffences();
setupMic();
