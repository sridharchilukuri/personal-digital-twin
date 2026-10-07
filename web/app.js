// ---- Theme toggle (dark default, persisted) ----
const themeToggle = document.getElementById("theme-toggle");
function syncThemeLabel() {
  const light = document.documentElement.getAttribute("data-theme") === "light";
  themeToggle.setAttribute("aria-label", light ? "Switch to dark mode" : "Switch to light mode");
}
syncThemeLabel();
themeToggle.addEventListener("click", () => {
  const light = document.documentElement.getAttribute("data-theme") === "light";
  const next = light ? "dark" : "light";
  if (next === "light") document.documentElement.setAttribute("data-theme", "light");
  else document.documentElement.removeAttribute("data-theme");
  try {
    localStorage.setItem("theme", next);
  } catch (e) {}
  syncThemeLabel();
});

// ---- Scroll-spy nav (single-page anchors) ----
const navLinks = document.querySelectorAll(".tab-link");
const sections = [...navLinks].map((a) => document.querySelector(a.getAttribute("href")));

if ("IntersectionObserver" in window) {
  const spy = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        navLinks.forEach((a) =>
          a.classList.toggle("is-active", a.getAttribute("href") === `#${e.target.id}`)
        );
      });
    },
    { rootMargin: "-45% 0px -50% 0px" }
  );
  sections.forEach((s) => s && spy.observe(s));
}

// ---- Live status badge: reflects the real /healthz, not a hard-coded "online" ----
const statusEl = document.getElementById("twin-status");
fetch("/healthz")
  .then((r) => {
    if (!r.ok) throw new Error("unhealthy");
  })
  .catch(() => {
    statusEl.classList.add("is-offline");
    statusEl.querySelector(".status-text").textContent = "twin offline";
  });

// ---- Markdown (tiny, safe): escape first, then allow only bold / italic / code / bullets ----
function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderInline(s) {
  return escapeHtml(s)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[\s(])[*_]([^*_\n]+)[*_](?=$|[\s).,!?:;])/g, "$1<em>$2</em>");
}

function renderMarkdown(src) {
  const out = [];
  let list = null; // current <ul> items, or null
  let para = []; // current paragraph lines
  const flushPara = () => {
    if (para.length) out.push(`<p>${para.map(renderInline).join("<br>")}</p>`);
    para = [];
  };
  const flushList = () => {
    if (list) out.push(`<ul>${list.map((li) => `<li>${renderInline(li)}</li>`).join("")}</ul>`);
    list = null;
  };
  for (const line of src.split("\n")) {
    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    if (bullet) {
      flushPara();
      (list = list || []).push(bullet[1]);
    } else if (!line.trim()) {
      flushPara();
      flushList();
    } else {
      flushList();
      para.push(line);
    }
  }
  flushPara();
  flushList();
  return out.join("");
}

// ---- Chat ----
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-text");
const sendBtn = document.getElementById("chat-send");
const messagesEl = document.getElementById("messages");
const suggestionsEl = document.getElementById("suggestions");

const MAX_HISTORY_TURNS = 10; // keep in sync with MAX_HISTORY_TURNS in app.py
const history = []; // [{role, content}, ...]

// Mirror the server's decline phrases (core/prompt.py) so refusals get a distinct look.
const DECLINES = [
  { match: "i don't have that in what sridhar has shared", tag: "Not in what he's shared" },
  { match: "i'm only here to talk about sridhar", tag: "Off-topic" },
];

// Follow-up pool: questions the corpus can answer. Shown 3 at a time, skipping ones already asked.
const FOLLOW_UPS = [
  "What's Sridhar most proud of?",
  "What tech does he work with?",
  "What is he learning right now?",
  "Tell me about his time at Proofpoint",
  "How did he cut cloud costs?",
  "What does he do outside work?",
  "What's his educational background?",
  "Where is he based?",
];
const asked = new Set();

function renderSuggestions() {
  const next = FOLLOW_UPS.filter((q) => !asked.has(q)).slice(0, 3);
  suggestionsEl.replaceChildren(
    ...next.map((q) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.textContent = q;
      b.addEventListener("click", () => sendMessage(q));
      return b;
    })
  );
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  if (role === "assistant") div.innerHTML = renderMarkdown(text);
  else div.textContent = text;
  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}

function markDeclined(bubble, reply) {
  const low = reply.toLowerCase();
  const hit = DECLINES.find((d) => low.includes(d.match));
  if (hit) {
    bubble.classList.add("declined");
    bubble.dataset.tag = hit.tag;
  }
}

async function sendMessage(text) {
  if (!text.trim() || sendBtn.disabled) return;

  asked.add(text);
  addMessage("user", text);
  history.push({ role: "user", content: text });
  input.value = "";
  input.disabled = sendBtn.disabled = true;

  const bubble = addMessage("assistant", "");
  bubble.classList.add("streaming", "thinking"); // typing dots until the first token arrives
  bubble.innerHTML = "<i></i><i></i><i></i>";
  let reply = "";

  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // Server caps history at 10 turns; send only the most recent ones.
      body: JSON.stringify({ message: text, history: history.slice(0, -1).slice(-MAX_HISTORY_TURNS) }),
    });
    if (!resp.ok || !resp.body) throw new Error("bad response");

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      reply += decoder.decode(value, { stream: true });
      bubble.classList.remove("thinking");
      bubble.innerHTML = renderMarkdown(reply);
      scrollToBottom();
    }
  } catch (err) {
    reply = reply || "Sorry — something went wrong. Please try again.";
    bubble.innerHTML = renderMarkdown(reply);
  } finally {
    bubble.classList.remove("streaming", "thinking");
    markDeclined(bubble, reply);
    history.push({ role: "assistant", content: reply });
    renderSuggestions();
    input.disabled = sendBtn.disabled = false;
    input.focus({ preventScroll: true });
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage(input.value);
});

// "Ask the twin" buttons on the Work section: jump to the console and ask.
document.querySelectorAll(".ask-btn").forEach((btn) =>
  btn.addEventListener("click", () => {
    document.getElementById("hero").scrollIntoView({ behavior: "smooth" });
    sendMessage(btn.dataset.ask);
  })
);

// Rotating placeholder so the empty input suggests what to ask.
const PLACEHOLDERS = [
  "Ask the twin a question…",
  "Try: how did he cut cloud costs?",
  "Try: what is he learning right now?",
  "Try: what does he do outside work?",
];
let placeholderIdx = 0;
setInterval(() => {
  if (document.activeElement === input || input.value) return;
  placeholderIdx = (placeholderIdx + 1) % PLACEHOLDERS.length;
  input.placeholder = PLACEHOLDERS[placeholderIdx];
}, 4000);

renderSuggestions();

// ---- Motion polish (all skipped under prefers-reduced-motion) ----
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// Cursor spotlight: feed pointer position to the hovered card as CSS vars.
document.addEventListener("pointermove", (e) => {
  const card = e.target.closest?.(".metric, .job, .depth-card, .chat");
  if (!card) return;
  const r = card.getBoundingClientRect();
  card.style.setProperty("--mx", `${e.clientX - r.left}px`);
  card.style.setProperty("--my", `${e.clientY - r.top}px`);
});

// Count the first number in a metric up from 0 (e.g. "10TB+" -> 0..10), keeping the rest verbatim.
function countUp(el) {
  const text = el.textContent;
  const m = text.match(/\d+(\.(\d+))?/);
  if (!m) return;
  const target = parseFloat(m[0]);
  const decimals = m[2] ? m[2].length : 0;
  const pre = text.slice(0, m.index);
  const post = text.slice(m.index + m[0].length);
  const start = performance.now();
  const step = (now) => {
    const t = Math.min((now - start) / 1000, 1);
    const v = target * (1 - Math.pow(1 - t, 3));
    el.textContent = pre + v.toFixed(decimals) + post;
    if (t < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

if (!reduceMotion && "IntersectionObserver" in window) {
  const reveal = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        e.target.classList.add("is-in");
        if (e.target.classList.contains("metric")) countUp(e.target.querySelector(".metric-num"));
        reveal.unobserve(e.target);
      });
    },
    { threshold: 0.15 }
  );
  document.querySelectorAll(".metric, .job, .about, .depth-card, .toolkit-row, .contact").forEach((el, i) => {
    el.classList.add("reveal");
    el.style.transitionDelay = `${(i % 4) * 70}ms`;
    reveal.observe(el);
  });
}

// ---- Command palette (Ctrl/Cmd+K) ----
const palette = document.getElementById("palette");
const paletteInput = document.getElementById("palette-input");
const paletteList = document.getElementById("palette-list");

const goTo = (id) => () => document.getElementById(id).scrollIntoView({ behavior: "smooth" });
const COMMANDS = [
  { label: "Ask the twin", hint: "focus chat", run: () => { goTo("hero")(); input.focus({ preventScroll: true }); } },
  { label: "Expertise", hint: "section", run: goTo("expertise") },
  { label: "Work", hint: "section", run: goTo("work") },
  { label: "Download résumé", hint: "pdf", run: () => document.querySelector(".hero-links a[download]").click() },
  { label: "GitHub", hint: "link", run: () => window.open("https://github.com/sridharchilukuri", "_blank", "noopener") },
  { label: "About", hint: "section", run: goTo("about") },
  { label: "Contact", hint: "section", run: goTo("contact") },
  { label: "Toggle light / dark", hint: "theme", run: () => themeToggle.click() },
  { label: "Email Sridhar", hint: "link", run: () => { window.location.href = "mailto:sridharchilukuri9@gmail.com"; } },
  { label: "LinkedIn", hint: "link", run: () => window.open("https://www.linkedin.com/in/sridharchilukuri", "_blank", "noopener") },
];
let visible = COMMANDS;
let selected = 0;

function drawPalette() {
  paletteList.replaceChildren(
    ...visible.map((c, i) => {
      const li = document.createElement("li");
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", String(i === selected));
      const label = document.createElement("span");
      label.textContent = c.label;
      const hint = document.createElement("small");
      hint.textContent = c.hint;
      li.append(label, hint);
      li.addEventListener("click", () => runCommand(c));
      return li;
    })
  );
}

function runCommand(c) {
  palette.close();
  c.run();
}

function openPalette() {
  paletteInput.value = "";
  visible = COMMANDS;
  selected = 0;
  drawPalette();
  palette.showModal();
  paletteInput.focus();
}

paletteInput.addEventListener("input", () => {
  const q = paletteInput.value.trim().toLowerCase();
  visible = COMMANDS.filter((c) => c.label.toLowerCase().includes(q));
  selected = 0;
  drawPalette();
});

paletteInput.addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown" || e.key === "ArrowUp") {
    e.preventDefault();
    if (!visible.length) return;
    selected = (selected + (e.key === "ArrowDown" ? 1 : -1) + visible.length) % visible.length;
    drawPalette();
  } else if (e.key === "Enter") {
    e.preventDefault();
    const q = paletteInput.value.trim();
    if (visible[selected]) runCommand(visible[selected]);
    else if (q) {
      // Nothing matched: treat the text as a question for the twin.
      palette.close();
      document.getElementById("hero").scrollIntoView({ behavior: "smooth" });
      sendMessage(q);
    }
  }
});

palette.addEventListener("click", (e) => { if (e.target === palette) palette.close(); }); // backdrop click
document.getElementById("palette-open").addEventListener("click", openPalette);
document.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    if (palette.open) palette.close();
    else openPalette();
  }
});
