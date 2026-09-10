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

// ---- Chat ----
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-text");
const sendBtn = document.getElementById("chat-send");
const messagesEl = document.getElementById("messages");

const history = []; // [{role, content}, ...]

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

async function sendMessage(text) {
  if (!text.trim() || sendBtn.disabled) return;

  addMessage("user", text);
  history.push({ role: "user", content: text });
  input.value = "";
  input.disabled = sendBtn.disabled = true;

  const bubble = addMessage("assistant", "");
  bubble.classList.add("streaming");
  let reply = "";

  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history: history.slice(0, -1) }),
    });
    if (!resp.ok || !resp.body) throw new Error("bad response");

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      reply += decoder.decode(value, { stream: true });
      bubble.textContent = reply;
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }
  } catch (err) {
    reply = reply || "Sorry — something went wrong. Please try again.";
    bubble.textContent = reply;
  } finally {
    bubble.classList.remove("streaming");
    history.push({ role: "assistant", content: reply });
    input.disabled = sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage(input.value);
});

document.querySelectorAll(".chip").forEach((chip) =>
  chip.addEventListener("click", () => sendMessage(chip.textContent))
);
