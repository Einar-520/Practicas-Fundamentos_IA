/* Componentes compartidos. Todo texto de usuarios, MongoDB y LLM se escapa. */
export const $ = (selector, root = document) => root.querySelector(selector);
export const $$ = (selector, root = document) => [
  ...root.querySelectorAll(selector),
];
export const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const paths = {
  grid: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z",
  truck:
    "M2 5h12v12H2zM14 9h4l4 5v3h-8M6 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4ZM18 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z",
  gate: "M4 21V3h12v18M2 21h20M11 12h1M17 6h4v15",
  mail: "M3 5h18v14H3zM3 6l9 7 9-7",
  spark:
    "m12 3 2.8 6.2L21 12l-6.2 2.8L12 21l-2.8-6.2L3 12l6.2-2.8ZM20 2v4M18 4h4",
  branches:
    "M12 7v5M5 12h14M5 12v5M19 12v5M9 2h6v5H9zM2 17h6v5H2zM16 17h6v5h-6z",
  shield: "m12 2 8 3v6c0 5-4 8-8 11-4-3-8-6-8-11V5ZM8 12l3 3 5-6",
  pulse: "M2 12h5l3-8 4 16 3-8h5",
  flask: "M8 2h8M9 2v7L3 19a2 2 0 0 0 2 3h14a2 2 0 0 0 2-3L15 9V2M7 14h10",
  download: "M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5",
  settings:
    "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2",
  refresh:
    "M20 7a9 9 0 0 0-15-2L2 8M2 3v5h5M4 17a9 9 0 0 0 15 2l3-3M22 21v-5h-5",
  menu: "M4 6h16M4 12h16M4 18h16",
  close: "m6 6 12 12M6 18 18 6",
  plus: "M12 4v16M4 12h16",
  arrow: "M4 12h16m-5-5 5 5-5 5",
  search: "M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14ZM15 15l6 6",
  edit: "m4 16-1 5 5-1L20 8l-4-4ZM14 6l4 4",
  trash: "M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12ZM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z",
  check: "m5 12 4 4L19 6",
  warning: "m12 3 10 18H2ZM12 9v5M12 17v1",
  chat: "M3 3h18v14H8l-5 4ZM7 8h10M7 12h6",
  code: "m8 5-7 7 7 7M16 5l7 7-7 7M14 3l-4 18",
  lock: "M5 10h14v11H5zM8 10V6a4 4 0 0 1 8 0v4M12 14v3",
  book: "M12 4v17M12 4C8 1 3 3 2 4v15c4-2 7-2 10 2 3-4 6-4 10-2V4c-1-1-6-3-10 0Z",
  send: "m3 3 19 9-19 9 4-9ZM7 12h15",
  clock: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20ZM12 6v6l4 2",
  file: "M5 2h9l5 5v15H5ZM14 2v6h5M8 12h8M8 16h8",
};
export function icon(name) {
  return `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.grid}"/></svg>`;
}
export function icons(root = document) {
  $$("[data-icon]", root).forEach((e) => (e.innerHTML = icon(e.dataset.icon)));
}
export const labels = {
  materiales_peligrosos: "Materiales peligrosos",
  sobrepeso: "Sobrepeso",
  acceso_no_autorizado: "Acceso no autorizado",
  falla_hardware: "Falla de hardware",
  falla_software: "Falla de software",
  somnolencia_conductor: "Somnolencia del conductor",
  otro: "Otro",
  en_atencion: "En atención",
  nuevo: "Nuevo",
  cerrado: "Cerrado",
  critica: "Crítica",
  alta: "Alta",
  media: "Media",
  baja: "Baja",
  autorizado: "Autorizado",
  inspeccion: "Inspección",
  retenido: "Retenido",
  denegado: "Denegado",
  camiones: "Camiones",
  accesos: "Control de acceso",
  incidentes: "Incidentes",
  riesgos_eticos: "Riesgos éticos",
  evaluaciones_llm: "Evaluaciones LLM",
  panel: "Panel de control",
  tablas: "Tablas de verdad",
  asistente: "Asistente con fuentes",
  experimento: "Experimento",
  reportes: "Reportes",
  configuracion: "Configuración",
  sesgo: "Sesgo",
  privacidad: "Privacidad",
  transparencia: "Transparencia",
  seguridad: "Seguridad",
  responsabilidad: "Responsabilidad",
  respaldo_reglas: "Respaldo por reglas",
  hibrido: "Híbrido",
  reglas: "Reglas",
  llm: "LLM",
  sin_respuesta: "Sin respuesta",
  informe_registros: "Informe generado con registros guardados",
};
export const label = (value) =>
  labels[value] || String(value ?? "").replaceAll("_", " ");
export function badge(value) {
  let color =
    {
      autorizado: "green",
      cerrado: "green",
      baja: "green",
      denegado: "red",
      retenido: "red",
      critica: "red",
      alta: "amber",
      inspeccion: "amber",
      nuevo: "amber",
      media: "blue",
      en_atencion: "blue",
    }[value] || "";
  return `<span class="badge ${color}"><span class="dot"></span>${esc(label(value))}</span>`;
}
export function date(value) {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime())
    ? esc(value)
    : d.toLocaleString("es-MX", {
        timeZone: "America/Mexico_City",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
}
export function empty(
  title = "Todavía no hay registros",
  text = "Crea el primero para comenzar.",
  symbol = "file",
) {
  return `<div class="empty">${icon(symbol)}<h3>${esc(title)}</h3><p>${esc(text)}</p></div>`;
}
export function notice(text, type = "") {
  return `<div class="notice ${type}">${icon(type === "error" ? "warning" : "shield")}<span>${esc(text)}</span></div>`;
}
export function pageHead(
  title,
  description,
  actions = "",
  overline = "LOGISMART / OPERACIÓN",
) {
  return `<div class="page-head"><div><span class="eyebrow">${esc(overline)}</span><h1>${esc(title)}</h1><p>${esc(description)}</p></div><div class="head-actions">${actions}</div></div>`;
}
export function button(text, id = "", symbol = "plus", primary = true) {
  return `<button type="button" class="button ${primary ? "primary" : ""}" ${id ? `id="${esc(id)}"` : ""}>${icon(symbol)}${esc(text)}</button>`;
}
export function metric(title, value, detail, symbol = "truck", color = "") {
  return `<article class="metric"><div class="metric-top"><span>${esc(title)}</span><span class="metric-symbol ${color}">${icon(symbol)}</span></div><div class="metric-value">${esc(value)}</div><div class="metric-foot"><span class="dot ${color ? color + "-text" : "green-text"}"></span>${esc(detail)}</div></article>`;
}
let toastTimer;
export function toast(text, error = false) {
  const e = $("#toast");
  clearTimeout(toastTimer);
  e.textContent = text;
  e.className = "toast" + (error ? " error" : "");
  e.hidden = false;
  toastTimer = setTimeout(() => (e.hidden = true), error ? 10000 : 5000);
}
export async function api(path, method = "GET", data) {
  const response = await fetch("/api" + path, {
    method,
    headers: {
      "X-CSRF-Token": $('meta[name="csrf-token"]').content,
      ...(data !== undefined ? { "Content-Type": "application/json" } : {}),
    },
    body: data !== undefined ? JSON.stringify(data) : undefined,
  });
  const result = await response.json();
  if (!response.ok)
    throw new Error(result.error || "No se pudo completar la solicitud.");
  return result;
}
export async function download(path, fallback) {
  const r = await fetch("/api" + path, {
    headers: { "X-CSRF-Token": $('meta[name="csrf-token"]').content },
  });
  if (!r.ok) {
    const d = await r.json();
    throw new Error(d.error || "No se pudo exportar.");
  }
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = fallback;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  toast("Reporte descargado.");
}
let polling = null;
export async function pollJob(id) {
  if (polling === id) throw new Error("Esta operación ya se está consultando.");
  polling = id;
  sessionStorage.setItem("trabajo", id);
  const bar = $("#job-bar");
  bar.hidden = false;
  const start = Date.now();
  try {
    while (true) {
      const job = await api("/trabajos/" + encodeURIComponent(id));
      $("#job-title").textContent = job.titulo;
      $("#job-time").textContent =
        Math.round((Date.now() - start) / 1000) + " s";
      if (job.estado === "error") throw new Error(job.error);
      if (job.estado === "completado") return job.resultado;
      await new Promise((resolve) => setTimeout(resolve, 650));
    }
  } finally {
    bar.hidden = true;
    polling = null;
    sessionStorage.removeItem("trabajo");
  }
}
export async function job(path, data = {}) {
  const r = await api(path, "POST", data);
  return r.trabajo ? pollJob(r.trabajo) : r;
}
export function showError(error, element = $("#contenido")) {
  element.innerHTML = `<div class="card card-pad error-state"><h2>No se pudo cargar esta vista</h2><p class="muted">${esc(error.message)}</p>${button("Volver a intentar", "retry", "refresh")}</div>`;
  $("#retry", element).onclick = () => $("#refresh").click();
}
export function modal(title, html) {
  $("#dialog-title").textContent = title;
  $("#dialog-content").innerHTML = html;
  const d = $("#dialog");
  if (!d.open) d.showModal();
  return d;
}
export async function confirmAction(title, message, actionText = "Confirmar") {
  return new Promise((resolve) => {
    const d = modal(
      title,
      `<p class="muted">${esc(message)}</p><div class="form-footer">${button("Cancelar", "cancel-confirm", "close", false)}${button(actionText, "accept-confirm", "check")}</div>`,
    );
    let accepted = false;
    const close = () => {
      d.removeEventListener("close", close);
      resolve(accepted);
    };
    d.addEventListener("close", close);
    $("#cancel-confirm").onclick = () => d.close();
    $("#accept-confirm").onclick = () => {
      accepted = true;
      d.close();
    };
  });
}
export function field(name, title, type = "text", value = "", opts = {}) {
  const id = "f-" + name;
  const required = opts.optional ? "" : "required";
  const limits = ["min", "max", "maxlength", "minlength", "step", "pattern"]
    .filter((k) => opts[k] !== undefined)
    .map((k) => `${k}="${esc(opts[k])}"`)
    .join(" ");
  if (type === "checkbox")
    return `<div class="check-row ${opts.full ? "full" : ""}"><input id="${id}" name="${esc(name)}" type="checkbox" ${value ? "checked" : ""}><label for="${id}">${esc(title)}</label></div>`;
  let input;
  if (type === "select")
    input = `<select id="${id}" name="${esc(name)}" ${required}>${(
      opts.options || []
    )
      .map((o) => {
        const v = Array.isArray(o) ? o[0] : o;
        return `<option value="${esc(v)}" ${String(v) === String(value) ? "selected" : ""}>${esc(Array.isArray(o) ? o[1] : label(v))}</option>`;
      })
      .join("")}</select>`;
  else if (type === "textarea")
    input = `<textarea id="${id}" name="${esc(name)}" ${required} ${limits} placeholder="${esc(opts.placeholder || "")}">${esc(value)}</textarea>`;
  else
    input = `<input id="${id}" name="${esc(name)}" type="${type}" value="${esc(value)}" ${required} ${limits} placeholder="${esc(opts.placeholder || "")}">`;
  return `<div class="field ${opts.full ? "full" : ""}"><label for="${id}">${esc(title)}${opts.optional ? ' <span class="muted">(opcional)</span>' : ""}</label>${input}${opts.help ? `<small>${esc(opts.help)}</small>` : ""}</div>`;
}
export function formData(form) {
  const result = {};
  $$("input[name],select[name],textarea[name]", form).forEach((e) => {
    result[e.name] =
      e.type === "checkbox"
        ? e.checked
        : e.type === "number"
          ? e.value === ""
            ? null
            : Number(e.value)
          : e.value.trim();
  });
  return result;
}
export function wireForm(form, save) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submit = $('[type="submit"]', form);
    if (submit.disabled) return;
    submit.disabled = true;
    const errors = $(".form-error", form);
    if (errors) errors.innerHTML = "";
    try {
      await save(formData(form));
    } catch (error) {
      if (errors) errors.innerHTML = notice(error.message, "error");
      else toast(error.message, true);
    } finally {
      submit.disabled = false;
    }
  });
}
export function chatMessage(role, text, sources = []) {
  // Solo los bloques de código delimitados se formatean; jamás se interpreta HTML del LLM.
  const parts = String(text).split(/```(?:[a-zA-Z]+)?\n?/g);
  const safe = parts
    .map((p, i) => (i % 2 ? `<pre><code>${esc(p)}</code></pre>` : esc(p)))
    .join("");
  return `<article class="message ${role === "user" ? "user" : ""}"><div class="message-avatar">${role === "user" ? "TÚ" : icon("spark")}</div><div class="message-main"><div class="message-name">${role === "user" ? "Tú" : "Asistente"}</div><div class="bubble">${safe}</div>${sources.map((s) => `<span class="source-pill">${icon("file")} ${esc(s)}</span>`).join("")}</div></article>`;
}
icons();
$("#today").textContent = new Date().toLocaleDateString("es-MX", {
  timeZone: "America/Mexico_City",
  day: "numeric",
  month: "short",
  year: "numeric",
});
$("#menu-toggle").onclick = () => {
  const open = $("#sidebar").classList.toggle("open");
  $("#menu-toggle").setAttribute("aria-expanded", String(open));
};
function dialogBusy() {
  return Boolean($('#dialog [type="submit"]:disabled'));
}
$("#close-dialog").onclick = () => {
  if (dialogBusy()) toast("Espera a que termine el guardado.", true);
  else $("#dialog").close();
};
$("#dialog").addEventListener("cancel", (e) => {
  if (dialogBusy()) {
    e.preventDefault();
    toast("Espera a que termine el guardado.", true);
  }
});
document.addEventListener("click", (e) => {
  if (e.target.closest(".sidebar a")) {
    $("#sidebar").classList.remove("open");
    $("#menu-toggle").setAttribute("aria-expanded", "false");
  }
});
