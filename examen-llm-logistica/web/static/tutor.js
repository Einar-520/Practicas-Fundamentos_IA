import {
  $,
  esc,
  icon,
  pageHead,
  button,
  chatMessage,
  notice,
  api,
  job,
  pollJob,
  wireForm,
  download,
  confirmAction,
  toast,
  showError,
} from "./comun.js";

const main = $("#contenido");
let state,
  summary = "",
  busy = false;
function render() {
  main.innerHTML =
    pageHead(
      "Una consulta. Un nuevo aprendizaje.",
      "Tu tutor de SQL para entender, practicar y conectar ideas.",
      "",
      "EJERCICIO 01 / TUTOR LOCAL",
    ) +
    `<div class="chat-layout"><section class="chat-card"><div class="chat-header"><div class="assistant-avatar">${icon("code")}</div><div><strong>Tu tutor de SQL</strong><small>Ejemplos de una biblioteca escolar</small></div><span class="badge green">Modelo local</span></div><div class="messages" id="messages">${state.historial.length ? state.historial.map((m) => chatMessage(m.role, m.content)).join("") : `<div class="chat-welcome"><div class="welcome-symbol">${icon("book")}</div><h2>Vamos a entender SQL.</h2><p>Haz una pregunta, escribe una consulta o pide un ejemplo. Construiremos la respuesta paso a paso.</p><div class="suggestions"><button class="suggestion" data-question="¿Cómo consulto los títulos de una tabla libros con SELECT?">${icon("search")}Mi primera consulta con SELECT</button><button class="suggestion" data-question="¿Cómo filtro los libros publicados después de 2020 con WHERE?">${icon("file")}Encuentra libros con WHERE</button><button class="suggestion" data-question="Explícame un JOIN entre libros y autores con un ejemplo.">${icon("branches")}Conecta tablas con JOIN</button><button class="suggestion" data-question="¿Cómo cuento los libros por autor usando GROUP BY?">${icon("grid")}Agrupa resultados con GROUP BY</button></div></div>`}</div><form class="chat-form" id="tutor-form"><div class="composer"><textarea id="question" name="pregunta" required maxlength="2000" rows="2" aria-label="Pregunta para el tutor de SQL" placeholder="¿Qué te gustaría aprender hoy?"></textarea><button type="submit" aria-label="Enviar pregunta">${icon("send")}</button></div><div class="composer-note"><span>Contexto: las últimas 6 interacciones.</span><span>Ctrl + Enter para enviar</span></div><div class="form-error" role="alert"></div></form></section><aside class="chat-side"><section class="card card-pad"><span class="eyebrow">TU RECORRIDO</span><div class="chat-sidebar-stat"><strong id="question-count">${state.consultas}</strong><span>consultas guardadas<br>en tu historial</span></div><hr><h3>De lo simple a lo útil.</h3><div class="lesson-item"><span class="lesson-number">01</span><div><strong>Explora tus datos</strong><small>SELECT · WHERE</small></div></div><div class="lesson-item"><span class="lesson-number">02</span><div><strong>Conecta información</strong><small>JOIN · claves</small></div></div><div class="lesson-item"><span class="lesson-number">03</span><div><strong>Encuentra patrones</strong><small>GROUP BY · COUNT</small></div></div></section><section class="card card-pad"><span class="eyebrow">PAUSA PARA RECORDAR</span><h2>Lo que hemos conversado.</h2><p style="margin-top:10px">Recupera los temas y las dudas de tus últimas seis interacciones.</p><div class="summary" id="summary">${esc(summary)}</div><div style="margin-top:18px">${button("Resumir mi historial", "summary-card", "spark", false)}</div></section><p class="muted" style="font-size:10px;line-height:1.8">Modelo configurado: ${esc(state.modelo)}.<br>El tutor orienta; verifica las consultas y practica por tu cuenta.</p></aside></div>`;
  main.setAttribute("aria-busy", "false");
  $("#connection").textContent = "Ollama local";
  const form = $("#tutor-form");
  wireForm(form, async (data) => {
    if (busy) throw new Error("Espera a que termine la respuesta actual.");
    busy = true;
    try {
      const result = await job("/preguntar", data);
      const messages = $("#messages");
      if ($(".chat-welcome", messages)) messages.innerHTML = "";
      messages.insertAdjacentHTML(
        "beforeend",
        chatMessage("user", data.pregunta) +
          chatMessage("assistant", result.respuesta),
      );
      state.consultas++;
      state.historial.push(
        { role: "user", content: data.pregunta },
        { role: "assistant", content: result.respuesta },
      );
      $("#question-count").textContent = state.consultas;
      $("#question").value = "";
      messages.scrollTop = messages.scrollHeight;
      toast(`Respuesta guardada · ${(result.latencia_ms / 1000).toFixed(1)} s`);
    } finally {
      busy = false;
    }
  });
  document.querySelectorAll("[data-question]").forEach(
    (b) =>
      (b.onclick = () => {
        $("#question").value = b.dataset.question;
        $("#question").focus();
      }),
  );
  $("#question").onkeydown = (e) => {
    if (e.ctrlKey && e.key === "Enter") {
      e.preventDefault();
      form.requestSubmit();
    }
  };
  $("#summary-card").onclick = summarize;
  $("#messages").scrollTop = $("#messages").scrollHeight;
}
async function summarize() {
  if (busy) {
    toast("Espera a que termine la operación actual.", true);
    return;
  }
  busy = true;
  try {
    const r = await job("/resumen");
    summary = r.resumen;
    $("#summary").textContent = summary;
    $("#summary").scrollIntoView({ block: "nearest", behavior: "smooth" });
  } catch (e) {
    toast(e.message, true);
  } finally {
    busy = false;
  }
}
async function load() {
  if (busy) {
    toast("Hay una respuesta en curso. Espera antes de actualizar.", true);
    return;
  }
  try {
    state = await api("/estado");
    render();
  } catch (e) {
    showError(e);
  }
}
$("#summary-action").onclick = summarize;
$("#export-action").onclick = async () => {
  try {
    await download("/exportar", "historial_tutor_sql.json");
  } catch (e) {
    toast(e.message, true);
  }
};
$("#new-action").onclick = async () => {
  if (busy) {
    toast("Espera a que termine la respuesta actual.", true);
    return;
  }
  if (
    await confirmAction(
      "Comenzar una conversación nueva",
      "Se vaciará el historial local del tutor. Puedes exportarlo primero para conservar una copia.",
      "Comenzar de nuevo",
    )
  ) {
    try {
      await api("/historial", "DELETE", { confirmar: true });
      summary = "";
      await load();
      toast("Tu nueva conversación está lista.");
    } catch (e) {
      toast(e.message, true);
    }
  }
};
$("#refresh").onclick = load;
await load();
const pending = state?.trabajo_activo || sessionStorage.getItem("trabajo");
if (pending) {
  busy = true;
  try {
    const r = await pollJob(pending);
    if (r.resumen) summary = r.resumen;
  } catch (e) {
    toast(e.message, true);
  } finally {
    busy = false;
    await load();
  }
}
