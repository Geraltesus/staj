"""HTML page for a lightweight local chat interface."""

CHAT_HTML = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Interview Mentor</title>
  <style>
    :root {
      --ink: #17211b;
      --muted: #657267;
      --paper: #fffaf0;
      --panel: rgba(255, 250, 240, 0.86);
      --line: rgba(23, 33, 27, 0.16);
      --accent: #e05d2f;
      --accent-dark: #a33c1d;
      --sage: #57745b;
      --bot: #f5e6c8;
      --user: #dbe9d1;
      --shadow: 0 24px 70px rgba(42, 31, 18, 0.2);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at 15% 15%, rgba(224, 93, 47, 0.22), transparent 28rem),
        radial-gradient(circle at 85% 5%, rgba(87, 116, 91, 0.24), transparent 24rem),
        linear-gradient(135deg, #f3dfb8 0%, #fffaf0 46%, #cad9b7 100%);
    }

    .grain {
      min-height: 100vh;
      padding: 32px;
      background-image: linear-gradient(rgba(23, 33, 27, 0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(23, 33, 27, 0.03) 1px, transparent 1px);
      background-size: 22px 22px;
    }

    .shell {
      width: min(1120px, 100%);
      margin: 0 auto;
      display: grid;
      grid-template-columns: 330px minmax(0, 1fr);
      gap: 24px;
      align-items: stretch;
    }

    .card {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }

    .sidebar { padding: 28px; }

    .eyebrow {
      margin: 0 0 12px;
      color: var(--accent-dark);
      font: 700 12px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }

    h1 {
      margin: 0;
      font-size: clamp(34px, 6vw, 58px);
      line-height: 0.92;
      letter-spacing: -0.05em;
    }

    .lead {
      margin: 20px 0 0;
      color: var(--muted);
      font-size: 17px;
      line-height: 1.55;
    }

    .controls {
      margin-top: 26px;
      display: grid;
      gap: 12px;
    }

    label {
      display: grid;
      gap: 8px;
      color: var(--muted);
      font: 700 12px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    input, textarea, button {
      font: inherit;
    }

    input, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 13px 14px;
      color: var(--ink);
      background: rgba(255, 255, 255, 0.58);
      outline: none;
    }

    input:focus, textarea:focus { border-color: rgba(224, 93, 47, 0.7); }

    .button-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 6px;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 16px;
      cursor: pointer;
      color: #fffaf0;
      background: var(--ink);
      transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease;
    }

    button:hover { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(23, 33, 27, 0.18); }
    button:disabled { cursor: wait; opacity: 0.64; transform: none; }

    .primary { background: var(--accent); }
    .secondary { background: var(--sage); }
    .ghost { background: rgba(23, 33, 27, 0.72); }

    .chat-card {
      display: grid;
      grid-template-rows: auto 1fr auto;
      min-height: calc(100vh - 64px);
      overflow: hidden;
    }

    .chat-top {
      padding: 20px 24px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
    }

    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font: 700 12px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #83aa62;
      box-shadow: 0 0 0 6px rgba(131, 170, 98, 0.16);
    }

    .messages {
      padding: 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .message {
      max-width: min(680px, 88%);
      padding: 16px 18px;
      border-radius: 22px;
      line-height: 1.5;
      white-space: pre-wrap;
      animation: rise 220ms ease both;
    }

    .bot {
      align-self: flex-start;
      background: var(--bot);
      border-top-left-radius: 6px;
    }

    .user {
      align-self: flex-end;
      background: var(--user);
      border-top-right-radius: 6px;
    }

    .composer {
      padding: 18px;
      border-top: 1px solid var(--line);
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: end;
    }

    textarea {
      min-height: 58px;
      max-height: 180px;
      resize: vertical;
    }

    .send { padding-inline: 24px; min-height: 58px; }

    @keyframes rise {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 860px) {
      .grain { padding: 16px; }
      .shell { grid-template-columns: 1fr; }
      .chat-card { min-height: 68vh; }
      .composer { grid-template-columns: 1fr; }
      .send { width: 100%; }
    }
  </style>
</head>
<body>
  <main class="grain">
    <section class="shell">
      <aside class="card sidebar">
        <p class="eyebrow">LangGraph + Ollama</p>
        <h1>Mock interview, но без лишней драмы</h1>
        <p class="lead">Локальный чат для учебного агента. Начните интервью, отвечайте на вопросы, а агент сам решит: уточнить, дать подсказку, показать эталон или завершить.</p>
        <div class="controls">
          <label>User ID<input id="userId" type="number" min="1" value="1" /></label>
          <div class="button-row">
            <button class="primary" id="startBtn">Начать</button>
            <button class="secondary" id="finishBtn">Завершить</button>
          </div>
          <button class="ghost" id="resetBtn">Сбросить сессию</button>
        </div>
      </aside>

      <section class="card chat-card">
        <header class="chat-top">
          <div>
            <p class="eyebrow">Interview Mentor</p>
            <strong>golang_backend / junior</strong>
          </div>
          <span class="status"><i class="dot"></i><span id="statusText">ready</span></span>
        </header>
        <div class="messages" id="messages"></div>
        <form class="composer" id="form">
          <textarea id="answer" placeholder="Напишите ответ кандидата..." required></textarea>
          <button class="primary send" type="submit">Отправить</button>
        </form>
      </section>
    </section>
  </main>

  <script>
    const messages = document.querySelector('#messages');
    const userId = document.querySelector('#userId');
    const answer = document.querySelector('#answer');
    const form = document.querySelector('#form');
    const statusText = document.querySelector('#statusText');
    const buttons = [...document.querySelectorAll('button')];

    function addMessage(role, text) {
      const node = document.createElement('div');
      node.className = `message ${role}`;
      node.textContent = text;
      messages.appendChild(node);
      messages.scrollTop = messages.scrollHeight;
    }

    function setBusy(isBusy, label = 'ready') {
      statusText.textContent = label;
      buttons.forEach((button) => { button.disabled = isBusy; });
    }

    async function callApi(path, payload) {
      setBusy(true, 'thinking');
      try {
        const response = await fetch(path, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          const text = await response.text();
          throw new Error(`${response.status}: ${text}`);
        }
        const data = await response.json();
        addMessage('bot', data.reply);
      } catch (error) {
        addMessage('bot', `Ошибка API: ${error.message}`);
      } finally {
        setBusy(false);
      }
    }

    document.querySelector('#startBtn').addEventListener('click', () => {
      messages.innerHTML = '';
      callApi('/interviews/start', { user_id: Number(userId.value || 1) });
    });

    document.querySelector('#resetBtn').addEventListener('click', () => {
      messages.innerHTML = '';
      callApi('/interviews/reset', { user_id: Number(userId.value || 1) });
    });

    document.querySelector('#finishBtn').addEventListener('click', () => {
      callApi('/interviews/finish', { user_id: Number(userId.value || 1) });
    });

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const text = answer.value.trim();
      if (!text) return;
      addMessage('user', text);
      answer.value = '';
      callApi('/interviews/answer', { user_id: Number(userId.value || 1), text });
    });

    addMessage('bot', 'Привет. Нажмите «Начать», и я задам первый вопрос.');
  </script>
</body>
</html>
"""
