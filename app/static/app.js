const messages = document.querySelector("#messages");
const userId = document.querySelector("#userId");
const answer = document.querySelector("#answer");
const form = document.querySelector("#form");
const statusText = document.querySelector("#statusText");
const buttons = [...document.querySelectorAll("button")];

function addMessage(role, text) {
  const node = document.createElement("div");
  node.className = `message ${role}`;
  node.textContent = text;
  messages.appendChild(node);
  messages.scrollTop = messages.scrollHeight;
}

function setBusy(isBusy, label = "ready") {
  statusText.textContent = label;
  buttons.forEach((button) => {
    button.disabled = isBusy;
  });
}

async function callApi(path, payload) {
  setBusy(true, "thinking");
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`${response.status}: ${text}`);
    }
    const data = await response.json();
    addMessage("bot", data.reply);
  } catch (error) {
    addMessage("bot", `Ошибка API: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

document.querySelector("#startBtn").addEventListener("click", () => {
  messages.innerHTML = "";
  callApi("/interviews/start", { user_id: Number(userId.value || 1) });
});

document.querySelector("#resetBtn").addEventListener("click", () => {
  messages.innerHTML = "";
  callApi("/interviews/reset", { user_id: Number(userId.value || 1) });
});

document.querySelector("#finishBtn").addEventListener("click", () => {
  callApi("/interviews/finish", { user_id: Number(userId.value || 1) });
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = answer.value.trim();
  if (!text) return;
  addMessage("user", text);
  answer.value = "";
  callApi("/interviews/answer", { user_id: Number(userId.value || 1), text });
});

addMessage("bot", "Привет. Нажмите «Начать», и я задам первый вопрос.");
