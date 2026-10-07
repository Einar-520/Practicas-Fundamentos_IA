import {
  $,
  $$,
  esc,
  icon,
  icons,
  label,
  badge,
  date,
  empty,
  notice,
  pageHead,
  button,
  metric,
  toast,
  api,
  download,
  job,
  pollJob,
  showError,
  modal,
  confirmAction,
  field,
  formData,
  wireForm,
  chatMessage,
} from "./comun.js";

const main = $("#contenido");
let meta,
  current = "panel",
  epoch = 0,
  records = [],
  query = "",
  status = "",
  page = 1,
  resultExperiment = null;
let period = { desde: "", hasta: "" };
const names = [
  "panel",
  "camiones",
  "accesos",
  "incidentes",
  "asistente",
  "tablas",
  "riesgos_eticos",
  "evaluaciones_llm",
  "experimento",
  "reportes",
  "configuracion",
];
const crud = [
  "camiones",
  "accesos",
  "incidentes",
  "riesgos_eticos",
  "evaluaciones_llm",
];
const singular = {
  camiones: "camión",
  accesos: "acceso",
  incidentes: "incidente",
  riesgos_eticos: "riesgo",
  evaluaciones_llm: "evaluación",
};
const colors = {
  autorizado: "#4c9071",
  inspeccion: "#ddbb76",
  retenido: "#e7a89b",
  denegado: "#7e9ca0",
};
const submit = (text = "Guardar registro") =>
  `<button class="button primary" type="submit">${icon("check")}${esc(text)}</button>`;
const guarded =
  (fn) =>
  async (...args) => {
    try {
      await fn(...args);
    } catch (e) {
      toast(e.message, true);
    }
  };
const params = () => new URLSearchParams(period).toString();

function bindPeriod(callback) {
  $("#period-form").onsubmit = async (e) => {
    e.preventDefault();
    period = { desde: $("#desde").value, hasta: $("#hasta").value };
    await callback();
  };
}
function periodForm() {
  return `<form class="filter-bar" id="period-form"><div class="field"><label for="desde">Desde</label><input id="desde" type="date" value="${esc(period.desde)}"></div><div class="field"><label for="hasta">Hasta</label><input id="hasta" type="date" value="${esc(period.hasta)}"></div><button class="button" type="submit">${icon("search")}Consultar</button><span class="period-note">Fecha de creación · período en UTC</span></form>`;
}

function weeklyChart(rows) {
  if (!rows.length)
    return empty(
      "Sin incidentes en este período",
      "Prueba con otras fechas o registra un correo.",
      "pulse",
    );
  const max = Math.max(...rows.map((r) => r.total), 1),
    height = rows.length * 40 + 30;
  return `<svg class="chart" role="img" aria-label="Incidentes por categoría y semana" viewBox="0 0 550 ${height}">${[0, 0.25, 0.5, 0.75, 1].map((x) => `<line class="axis" x1="${245 + 260 * x}" y1="0" x2="${245 + 260 * x}" y2="${height - 20}"/>`).join("")}${rows.map((r, i) => `<text x="0" y="${i * 40 + 17}">${esc(label(r.categoria))}</text><text x="0" y="${i * 40 + 30}" font-size="9">${r.anio} · semana ${r.semana}</text><rect x="245" y="${i * 40 + 9}" width="${(260 * r.total) / max}" height="15" rx="4" fill="${i % 2 ? "#a6d3b6" : "#39785d"}"/><text class="value" x="${253 + (260 * r.total) / max}" y="${i * 40 + 20}">${r.total}</text>`).join("")}</svg>`;
}
function donut(distribution) {
  const total = Object.values(distribution).reduce((a, b) => a + b, 0);
  const percentage = new Intl.NumberFormat("es-MX", {
    maximumFractionDigits: 1,
  });
  const entries = Object.entries(distribution).map(([key, count]) => {
    const percent = total ? (count / total) * 100 : 0;
    const percentText = `${percentage.format(percent)}%`;
    return {
      key,
      count,
      percent,
      percentText,
      info: `${label(key)}: ${percentText} · ${count} de ${total} accesos`,
    };
  });
  let offset = 0;
  const paths = entries
    .map(({ key, percent, info }) => {
      if (!percent) return "";
      const attributes = `class="donut-segment" data-donut-key="${esc(key)}" data-donut-info="${esc(info)}" tabindex="0" role="img" aria-label="${esc(info)}" fill="none" stroke="${colors[key]}" stroke-width="16"`;
      const start = ((offset * 3.6 - 90) * Math.PI) / 180;
      offset += percent;
      const end = ((offset * 3.6 - 90) * Math.PI) / 180;
      if (percent === 100)
        return `<circle ${attributes} cx="80" cy="80" r="57"><title>${esc(info)}</title></circle>`;
      const point = (angle) =>
        `${80 + 57 * Math.cos(angle)} ${80 + 57 * Math.sin(angle)}`;
      return `<path ${attributes} d="M ${point(start)} A 57 57 0 ${percent > 50 ? 1 : 0} 1 ${point(end)}"><title>${esc(info)}</title></path>`;
    })
    .join("");
  const labels = entries
    .map(
      ({ key, count, percentText, info }) =>
        `<div data-donut-info="${esc(info)}" tabindex="0" aria-label="${esc(info)}" title="${esc(info)}"><span class="dot" style="color:${colors[key]}"></span><span class="donut-label-detail">${esc(label(key))}<small>${count} de ${total} accesos</small></span><b class="donut-percent">${percentText}</b></div>`,
    )
    .join("");
  return `<div class="donut-wrap"><svg class="donut" viewBox="0 0 160 160" role="group" aria-label="${total} accesos en el período"><circle cx="80" cy="80" r="57" fill="none" stroke="#edf3ee" stroke-width="16"/>${paths}<text x="80" y="79" text-anchor="middle" font-size="28" fill="#244934" font-family="inherit">${total}</text><text x="80" y="98" text-anchor="middle" font-size="9" fill="#96a598">ACCESOS</text></svg><div class="donut-labels">${labels}</div><div class="donut-tooltip" role="tooltip" hidden></div></div>`;
}

function wireDonut() {
  const chart = $(".donut-wrap");
  if (!chart) return;
  const tooltip = $(".donut-tooltip", chart);
  const hide = () => {
    tooltip.hidden = true;
  };
  const show = (target, event) => {
    tooltip.textContent = target.dataset.donutInfo;
    tooltip.hidden = false;
    const bounds = chart.getBoundingClientRect();
    const item = target.getBoundingClientRect();
    const x = event?.clientX ?? item.x + item.width / 2;
    const y = event?.clientY ?? item.y + item.height / 2;
    tooltip.style.left =
      Math.max(
        0,
        Math.min(x - bounds.x + 12, bounds.width - tooltip.offsetWidth),
      ) + "px";
    tooltip.style.top =
      Math.max(
        0,
        Math.min(y - bounds.y + 12, bounds.height - tooltip.offsetHeight),
      ) + "px";
  };
  $$("[data-donut-info]", chart).forEach((target) => {
    target.addEventListener("pointerenter", (event) => show(target, event));
    target.addEventListener("pointermove", (event) => show(target, event));
    target.addEventListener("pointerleave", hide);
    target.addEventListener("focus", () => show(target));
    target.addEventListener("blur", hide);
  });
  chart.addEventListener("keydown", (event) => {
    if (event.key === "Escape") hide();
  });
}

function dashboard(data) {
  main.innerHTML =
    pageHead(
      "Tu operación, en perspectiva.",
      "Consulta el patio, identifica prioridades y decide con evidencia.",
      button("Registrar acceso", "new-access", "plus"),
      "LOGISMART / VISIÓN GENERAL",
    ) +
    periodForm() +
    `<section class="metrics" aria-label="Indicadores de operación">${metric("Camiones atendidos", data.camiones_atendidos, "Unidades distintas en el período", "truck")}${metric("Accesos registrados", data.accesos, "Decisiones con trazabilidad", "gate", "blue")}${metric("Incidentes abiertos", data.incidentes_abiertos, "Pendientes de atención", "mail", "amber")}${metric("Riesgos críticos", data.riesgos_criticos, "Puntaje residual ≥ " + meta.config.umbral_riesgo, "shield", "red")}</section>` +
    `<div class="grid-2"><section class="card"><div class="card-head"><div><h2>Incidentes por categoría y semana</h2><p>Agregación de registros del período seleccionado</p></div><span class="tag-outline">SEMANAS ISO</span></div><div class="card-body">${weeklyChart(data.por_semana)}</div></section><section class="card"><div class="card-head"><div><h2>Resultado de los accesos</h2><p>Distribución de decisiones operativas</p></div></div><div class="card-body">${donut(data.distribucion)}</div></section></div>` +
    `<div class="grid-2"><section class="card"><div class="card-head"><div><h2>Actividad reciente</h2><p>Últimos accesos registrados · hora de México</p></div><a class="text-link" href="#accesos">Ver bitácora ${icon("arrow")}</a></div>${data.ultimos_accesos.length ? `<div class="table-wrap"><table><thead><tr><th>Unidad</th><th>Resultado</th><th>Registro</th></tr></thead><tbody>${data.ultimos_accesos.map((r) => `<tr><td><strong>${esc(r.camion_id)}</strong><small>${esc(r.placa)}</small></td><td>${badge(r.resultado)}</td><td>${date(r.creado_en)}</td></tr>`).join("")}</tbody></table></div>` : empty()}</section><section class="card"><div class="card-head"><div><h2>Atención prioritaria</h2><p>Incidentes abiertos, ordenados por prioridad</p></div><a class="text-link" href="#incidentes">Ver todos ${icon("arrow")}</a></div><div class="card-body mini-list">${
      data.incidentes
        .filter((i) => i.estado !== "cerrado")
        .sort(
          (a, b) =>
            meta.prioridades.indexOf(b.clasificacion.prioridad) -
            meta.prioridades.indexOf(a.clasificacion.prioridad),
        )
        .slice(0, 3)
        .map(
          (i) =>
            `<div class="mini-item"><div class="mini-symbol">${icon("warning")}</div><div><strong>${esc(label(i.clasificacion.categoria))}</strong><small>${esc(i.correo_original.asunto)}</small></div>${badge(i.clasificacion.prioridad)}</div>`,
        )
        .join("") ||
      empty("Todo está al día", "No hay incidentes abiertos.", "check")
    }</div></section></div>`;
  wireDonut();
  bindPeriod(() => navigate("panel"));
  $("#new-access").onclick = () => editRecord("accesos");
}

const columns = {
  camiones: [
    "Unidad / placa",
    "Empresa",
    "Autorización",
    "Certificación",
    "Vigencia",
  ],
  accesos: ["Unidad / placa", "Resultado", "A / E", "Operador", "Registro"],
  incidentes: ["Incidente", "Prioridad", "Estado", "Revisión", "Registro"],
  riesgos_eticos: ["Módulo", "Categoría", "Antes", "Residual", "Nivel"],
  evaluaciones_llm: [
    "Tipo / modelo",
    "Estado",
    "Latencia",
    "Coincidió con reglas",
    "Registro",
  ],
};
const descriptions = {
  camiones:
    "Administra las unidades, su autorización y la vigencia del conductor.",
  accesos:
    "Evalúa las premisas, consulta el resultado y conserva cada decisión.",
  incidentes:
    "Clasifica correos, revisa discrepancias y da seguimiento a cada caso.",
  riesgos_eticos:
    "Visualiza el riesgo inicial, su mitigación y la valoración residual.",
  evaluaciones_llm:
    "Consulta prompts, respuestas, latencias y correcciones con historial.",
};
function rowCells(type, r) {
  if (type === "camiones")
    return [
      `<strong>${esc(r.camion_id)}</strong><small>${esc(r.placa)}</small>`,
      esc(r.empresa),
      badge(r.autorizacion ? "autorizado" : "denegado"),
      `<span class="badge ${r.certificacion_conductor ? "green" : "amber"}">${r.certificacion_conductor ? "Certificado" : "Sin certificación"}</span>`,
      esc(r.certificacion_hasta),
    ];
  if (type === "accesos")
    return [
      `<strong>${esc(r.camion_id)}</strong><small>${esc(r.placa)}</small>`,
      badge(r.resultado),
      `A: ${r.A ? "V" : "F"} · E: ${r.E ? "V" : "F"}`,
      esc(r.operador),
      date(r.creado_en),
    ];
  if (type === "incidentes")
    return [
      `<strong>${esc(label(r.clasificacion.categoria))}</strong><small>${esc(r.correo_original.asunto)}</small>`,
      badge(r.clasificacion.prioridad),
      badge(r.estado),
      `<span class="badge ${r.requiere_revision_humana ? "amber" : "green"}">${r.requiere_revision_humana ? "Pendiente" : "Revisado"}</span>`,
      date(r.creado_en),
    ];
  if (type === "riesgos_eticos")
    return [
      `<strong>${esc(r.modulo)}</strong><small>${esc(r.descripcion.slice(0, 80))}</small>`,
      esc(label(r.categoria)),
      String(r.puntaje_inicial),
      `<strong>${r.puntaje_residual}</strong> / 25`,
      `<span class="badge ${r.puntaje_residual >= 17 ? "red" : r.puntaje_residual >= 10 ? "amber" : "green"}">${esc(r.nivel_residual)}</span>`,
    ];
  return [
    `<strong>${esc(label(r.tipo))}</strong><small>${esc(r.modelo)}</small>`,
    esc(label(r.estado)),
    Number(r.latencia_ms).toFixed(1) + " ms",
    r.coincidio_reglas == null
      ? "No evaluado"
      : r.coincidio_reglas
        ? "Sí"
        : "No",
    date(r.creado_en),
  ];
}
function tableSection(type, data) {
  const options =
    type === "incidentes"
      ? [...meta.estados, ...meta.prioridades]
      : type === "accesos"
        ? ["autorizado", "inspeccion", "retenido", "denegado"]
        : [];
  return `<section class="card"><div class="table-tools"><div class="search">${icon("search")}<input id="table-search" type="search" placeholder="Buscar en los registros…" aria-label="Buscar registros" value="${esc(query)}"></div>${options.length ? `<select id="table-filter" aria-label="Filtrar por estado o prioridad"><option value="">Todos los estados</option>${options.map((o) => `<option value="${o}" ${status === o ? "selected" : ""}>${esc(label(o))}</option>`).join("")}</select>` : ""}<span class="card-label">${data.length} registros activos</span></div><div id="table-body"></div></section>`;
}
function paintTable() {
  const filtered = records.filter((r) => {
    const searchable = JSON.stringify({
      ...r,
      historico: undefined,
    }).toLocaleLowerCase("es");
    const statusMatch =
      !status ||
      r.resultado === status ||
      r.estado === status ||
      r.clasificacion?.prioridad === status;
    return statusMatch && searchable.includes(query.toLocaleLowerCase("es"));
  });
  const pages = Math.max(1, Math.ceil(filtered.length / 8));
  page = Math.min(page, pages);
  const rows = filtered.slice((page - 1) * 8, page * 8),
    type = current;
  $("#table-body").innerHTML =
    (rows.length
      ? `<div class="table-wrap"><table><thead><tr>${columns[type].map((c) => `<th>${c}</th>`).join("")}<th>Acciones</th></tr></thead><tbody>${rows
          .map(
            (r) =>
              `<tr>${rowCells(type, r)
                .map((v) => `<td>${v}</td>`)
                .join(
                  "",
                )}<td><div class="row-actions"><button class="icon-button view" data-id="${esc(r._id)}" title="Ver detalle e historial" aria-label="Ver detalle de ${esc(r.camion_id || singular[type])}">${icon("eye")}</button><button class="icon-button edit" data-id="${esc(r._id)}" title="Editar" aria-label="Editar ${esc(r.camion_id || singular[type])}">${icon("edit")}</button><button class="icon-button delete" data-id="${esc(r._id)}" title="Dar de baja" aria-label="Dar de baja ${esc(r.camion_id || singular[type])}">${icon("trash")}</button></div></td></tr>`,
          )
          .join("")}</tbody></table></div>`
      : empty(
          query || status
            ? "No encontramos coincidencias"
            : "Todavía no hay registros",
          query || status
            ? "Prueba con otro texto o filtro."
            : "Usa el botón de arriba para crear el primero.",
        )) +
    `<div class="table-foot"><span>${filtered.length} registros · hora de México</span><div class="pagination"><button id="prev-page" aria-label="Página anterior" ${page === 1 ? "disabled" : ""}>←</button><span>${page} / ${pages}</span><button id="next-page" aria-label="Página siguiente" ${page === pages ? "disabled" : ""}>→</button></div></div>`;
  $("#prev-page").onclick = () => {
    page--;
    paintTable();
  };
  $("#next-page").onclick = () => {
    page++;
    paintTable();
  };
  $$(".edit").forEach(
    (b) =>
      (b.onclick = () =>
        editRecord(
          type,
          records.find((r) => r._id === b.dataset.id),
        )),
  );
  $$(".view").forEach(
    (b) =>
      (b.onclick = () =>
        detail(
          type,
          records.find((r) => r._id === b.dataset.id),
        )),
  );
  $$(".delete").forEach(
    (b) =>
      (b.onclick = guarded(async () => {
        const r = records.find((r) => r._id === b.dataset.id);
        if (
          await confirmAction(
            "Dar de baja " + singular[type],
            "El registro dejará de aparecer en las consultas. Su historial quedará conservado para auditoría.",
            "Dar de baja",
          )
        ) {
          await api(
            "/registros/" + type + "/" + encodeURIComponent(r._id),
            "DELETE",
            { version: r.version, confirmar: true },
          );
          toast("Registro dado de baja.");
          await navigate(type);
        }
      })),
  );
}
function risksChart(data) {
  return `<section class="card" style="margin-bottom:22px"><div class="card-head"><div><h2>Antes y después de la mitigación</h2><p>Probabilidad × impacto · valoraciones estimadas, escala de 1 a 25</p></div><span class="tag-outline">UMBRAL CRÍTICO ${meta.config.umbral_riesgo}</span></div><div class="card-body"><div class="legend"><span><i style="background:#ddb594"></i>Riesgo inicial</span><span><i style="background:#4b8967"></i>Riesgo residual</span><span>│ Umbral crítico</span></div>${
    [...data]
      .sort((a, b) => b.puntaje_residual - a.puntaje_residual)
      .map(
        (r) =>
          `<div class="risk-row"><div><h3>${esc(r.modulo)}</h3><small>${esc(label(r.categoria))}</small></div><div class="risk-bars"><svg role="img" aria-label="${esc(r.modulo)}: inicial ${r.puntaje_inicial}, residual ${r.puntaje_residual}" viewBox="0 0 500 30" preserveAspectRatio="none"><rect y="0" width="500" height="11" rx="3" fill="#f7f3ee"/><rect y="18" width="500" height="11" rx="3" fill="#f0f5ef"/><rect y="0" width="${r.puntaje_inicial * 20}" height="11" rx="3" fill="#ddb594"/><rect y="18" width="${r.puntaje_residual * 20}" height="11" rx="3" fill="#4b8967"/><line x1="${meta.config.umbral_riesgo * 20}" x2="${meta.config.umbral_riesgo * 20}" y1="0" y2="30" stroke="#aaa08b" stroke-dasharray="3 2"/></svg></div><div class="risk-values">${r.puntaje_inicial} → <strong>${r.puntaje_residual}</strong></div></div>`,
      )
      .join("") ||
    empty(
      "Sin riesgos registrados",
      "Agrega un riesgo para comparar sus puntajes.",
      "shield",
    )
  }</div></section>`;
}
function crudPage(type, data) {
  records = data;
  main.innerHTML =
    pageHead(
      label(type),
      descriptions[type],
      button(
        type === "incidentes" ? "Clasificar correo" : "Nuevo " + singular[type],
        "new-record",
        type === "incidentes" ? "mail" : "plus",
      ),
    ) +
    (type === "riesgos_eticos" ? risksChart(data) : "") +
    tableSection(type, data);
  paintTable();
  $("#table-search").oninput = (e) => {
    query = e.target.value;
    page = 1;
    paintTable();
  };
  if ($("#table-filter"))
    $("#table-filter").onchange = (e) => {
      status = e.target.value;
      page = 1;
      paintTable();
    };
  $("#new-record").onclick = () => editRecord(type);
}

function recordFields(type, r) {
  if (type === "camiones")
    return (
      field("camion_id", "Identificador", "text", r.camion_id, {
        placeholder: "CAM-105",
        pattern: "CAM-[0-9]{1,8}",
      }) +
      field("placa", "Placa", "text", r.placa, {
        placeholder: "ABC-105-D",
        minlength: 5,
        maxlength: 15,
      }) +
      field("empresa", "Empresa", "text", r.empresa, {
        full: true,
        minlength: 2,
        maxlength: 120,
      }) +
      field("autorizacion", "Autorización previa", "checkbox", r.autorizacion) +
      field(
        "certificacion_conductor",
        "Conductor certificado",
        "checkbox",
        r.certificacion_conductor,
      ) +
      field(
        "certificado_id",
        "Folio del certificado",
        "text",
        r.certificado_id,
        { maxlength: 60 },
      ) +
      field(
        "certificacion_hasta",
        "Certificación vigente hasta",
        "date",
        r.certificacion_hasta,
      )
    );
  if (type === "accesos")
    return (
      field("camion_id", "Identificador", "text", r.camion_id, {
        placeholder: "CAM-102",
      }) +
      field("placa", "Placa", "text", r.placa, { placeholder: "ABC-102-D" }) +
      `<div class="full actions">${button("Buscar placa y cargar P / S", "find-plate", "search", false)}<small class="muted">Confirma los datos antes de guardar.</small></div>` +
      premiseFields(r) +
      field(
        "observacion",
        "Observaciones de la captura",
        "textarea",
        r.observacion,
        { optional: true, full: true, maxlength: 500 },
      ) +
      (r._id
        ? field("motivo", "Motivo de la corrección", "text", "", {
            minlength: 5,
            maxlength: 500,
            full: true,
          })
        : "") +
      `<div class="full" id="access-preview"></div>`
    );
  if (type === "riesgos_eticos")
    return (
      field("modulo", "Módulo", "text", r.modulo, {
        minlength: 2,
        maxlength: 120,
      }) +
      field("categoria", "Categoría ética", "select", r.categoria, {
        options: meta.categorias_eticas,
      }) +
      field(
        "descripcion",
        "Descripción del riesgo",
        "textarea",
        r.descripcion,
        { full: true, minlength: 5, maxlength: 1000 },
      ) +
      field(
        "probabilidad",
        "Probabilidad inicial (1–5)",
        "number",
        r.probabilidad ?? 3,
        { min: 1, max: 5, step: 1 },
      ) +
      field("impacto", "Impacto inicial (1–5)", "number", r.impacto ?? 3, {
        min: 1,
        max: 5,
        step: 1,
      }) +
      field("mitigacion", "Medida de mitigación", "textarea", r.mitigacion, {
        full: true,
        minlength: 5,
        maxlength: 1000,
      }) +
      field(
        "probabilidad_residual",
        "Probabilidad residual (1–5)",
        "number",
        r.probabilidad_residual ?? 2,
        { min: 1, max: 5, step: 1 },
      ) +
      field(
        "impacto_residual",
        "Impacto residual (1–5)",
        "number",
        r.impacto_residual ?? 3,
        { min: 1, max: 5, step: 1 },
      ) +
      field(
        "evidencia",
        "Evidencia o referencia a prueba",
        "textarea",
        r.evidencia,
        { full: true, minlength: 5, maxlength: 1000 },
      )
    );
  if (type === "incidentes") {
    if (!r._id)
      return (
        field("remitente", "Remitente", "email", "operador@ejemplo.test", {
          full: true,
          maxlength: 180,
        }) +
        field("asunto", "Asunto del correo", "text", "", {
          full: true,
          maxlength: 200,
        }) +
        field("cuerpo", "Contenido del correo", "textarea", "", {
          full: true,
          maxlength: 10000,
          placeholder:
            "Pega aquí el correo recibido. Se extraerán la placa, el camión, el peso y la ubicación cuando aparezcan.",
        }) +
        `<div class="full">${notice(meta.config.usar_llm ? "Se consultará Ollama y se comparará su respuesta con las reglas. Las discrepancias quedarán marcadas para revisión." : "El LLM está deshabilitado. Se utilizará el respaldo por reglas y se marcará la revisión humana.", "warning")}</div>`
      );
    const c = r.clasificacion,
      e = r.datos_extraidos;
    return (
      field("categoria", "Categoría", "select", c.categoria, {
        options: meta.categorias,
      }) +
      field("prioridad", "Prioridad", "select", c.prioridad, {
        options: meta.prioridades,
      }) +
      field("estado", "Estado del incidente", "select", r.estado, {
        options: meta.estados,
      }) +
      field(
        "requiere_revision_humana",
        "Pendiente de revisión humana",
        "checkbox",
        r.requiere_revision_humana,
      ) +
      field("resumen", "Resumen revisado", "textarea", c.resumen, {
        full: true,
        maxlength: 500,
      }) +
      field("placa", "Placa extraída", "text", e.placa, {
        optional: true,
        maxlength: 20,
      }) +
      field("camion_id", "Camión extraído", "text", e.camion_id, {
        optional: true,
        maxlength: 20,
      }) +
      field(
        "peso_reportado_kg",
        "Peso en kilogramos",
        "number",
        e.peso_reportado_kg,
        { optional: true, min: 0, max: 1000000, step: "any" },
      ) +
      field("ubicacion", "Ubicación extraída", "text", e.ubicacion, {
        optional: true,
        maxlength: 100,
      }) +
      field("motivo", "Motivo de la corrección", "textarea", "", {
        full: true,
        minlength: 5,
        maxlength: 500,
      })
    );
  }
  return (
    field("modelo", "Modelo", "text", r.modelo || meta.config.modelo, {
      maxlength: 100,
    }) +
    field(
      "latencia_ms",
      "Latencia en milisegundos",
      "number",
      r.latencia_ms ?? 0,
      { min: 0, step: "any" },
    ) +
    field("prompt", "Prompt o solicitud", "textarea", r.prompt, {
      full: true,
      maxlength: 20000,
    }) +
    field("respuesta", "Respuesta registrada", "textarea", r.respuesta, {
      full: true,
      optional: true,
      maxlength: 20000,
    }) +
    field(
      "coincidio_reglas",
      "Coincidencia con las reglas",
      "select",
      r.coincidio_reglas == null ? "" : String(r.coincidio_reglas),
      {
        optional: true,
        options: [
          ["", "No evaluado"],
          ["true", "Sí"],
          ["false", "No"],
        ],
      },
    ) +
    field(
      "observacion",
      "Motivo / observación manual",
      "textarea",
      r.observacion,
      { full: true, minlength: 5, maxlength: 1000 },
    )
  );
}
const premises = {
  P: ["Autorización previa", "Unidad autorizada para ingresar"],
  Q: ["Exceso de peso", "La carga excede el límite"],
  R: ["Materiales peligrosos", "La carga necesita inspección"],
  S: ["Certificación vigente", "Conductor certificado"],
  H: ["Horario permitido", "Dentro del horario configurado"],
  T: ["Alerta de fatiga", "Conductor con somnolencia"],
};
function premiseFields(values) {
  return Object.entries(premises)
    .map(
      ([k, [title, desc]]) =>
        `<label class="switch-label" for="f-${k}"><span><strong>${k} · ${title}</strong><small>${desc}</small></span><input type="checkbox" name="${k}" id="f-${k}" ${values[k] ? "checked" : ""}></label>`,
    )
    .join("");
}
function decision(r) {
  const color =
    r.semaforo === "verde"
      ? "green"
      : r.semaforo === "amarillo"
        ? "amber"
        : "red";
  return `<div class="rule-summary"><div class="decision ${color}-text"><span class="dot"></span>${esc(label(r.resultado))}</div><div class="rule-badges">${["A", "E", "B", "F"].map((k) => `<span>${k} = <strong>${r[k] ? "Verdadero" : "Falso"}</strong></span>`).join("")}</div><ol class="step-list">${r.explicacion.map((p) => `<li>${esc(p)}</li>`).join("")}</ol></div>`;
}
function wirePremises(form, target, onResult) {
  let sequence = 0;
  const preview = async () => {
    const id = ++sequence;
    try {
      const p = Object.fromEntries(
        Object.keys(premises).map((k) => [k, $(`[name="${k}"]`, form).checked]),
      );
      const r = await api("/simular", "POST", p);
      if (sequence === id) {
        target.innerHTML = decision(r);
        onResult?.(p);
      }
    } catch (e) {
      target.innerHTML = notice(e.message, "error");
    }
  };
  Object.keys(premises).forEach((k) =>
    $(`[name="${k}"]`, form).addEventListener("change", preview),
  );
  preview();
  return preview;
}

function editRecord(type, previous = null) {
  const record = previous || { H: meta.horario_permitido, T: false };
  const d = modal(
    previous
      ? "Editar " + singular[type]
      : type === "incidentes"
        ? "Clasificar un correo"
        : "Nuevo " + singular[type],
    `<form id="record-form"><div class="form-grid">${recordFields(type, record)}</div><div class="form-error" role="alert"></div><div class="form-footer">${button("Cancelar", "cancel-edit", "close", false)}${submit(type === "incidentes" && !previous ? "Clasificar y guardar" : "Guardar registro")}</div></form>`,
  );
  const form = $("#record-form");
  $("#cancel-edit").onclick = () => {
    if ($('[type="submit"]', form).disabled)
      toast("Espera a que termine el guardado.", true);
    else d.close();
  };
  if (type === "accesos") {
    const preview = wirePremises(form, $("#access-preview"));
    $("#find-plate").onclick = guarded(async () => {
      const r = await api(
        "/camion?placa=" + encodeURIComponent($("#f-placa").value),
      );
      for (const k of ["placa", "camion_id"]) $("#f-" + k).value = r[k];
      for (const k of ["P", "S"]) $("#f-" + k).checked = r[k];
      await preview();
      toast(
        "Autorización y vigencia cargadas. Confirma el resto de las premisas.",
      );
    });
  }
  wireForm(form, async (data) => {
    if (type === "incidentes" && previous)
      for (const k of ["placa", "camion_id", "ubicacion"])
        data[k] = data[k] || null;
    if (type === "evaluaciones_llm")
      data.coincidio_reglas =
        data.coincidio_reglas === "" ? null : data.coincidio_reglas === "true";
    if (previous) {
      data.id = previous._id;
      data.version = previous.version;
    }
    const saved = await job("/registros/" + type, data);
    d.close();
    toast(
      type === "incidentes" && !previous
        ? "Correo clasificado y guardado."
        : "Registro guardado correctamente.",
    );
    await navigate(type);
    if (type === "incidentes" && !previous)
      detail(type, saved.registro || saved);
  });
}

function detail(type, r) {
  let content = "";
  if (type === "accesos") content = decision(r);
  else if (type === "incidentes")
    content = `<div class="actions">${badge(r.clasificacion.prioridad)}${badge(r.estado)}<span class="badge">${esc(label(r.origen))}</span></div><h3 style="margin-top:18px">${esc(r.correo_original.asunto)}</h3><p class="muted" style="margin-top:7px">${esc(r.correo_original.remitente)}</p><div class="review-body">${esc(r.correo_original.cuerpo)}</div><h3>Clasificación: ${esc(label(r.clasificacion.categoria))}</h3><p style="margin-top:10px">${esc(r.clasificacion.resumen)}</p><div style="margin-top:15px">${notice(r.requiere_revision_humana ? "Este resultado requiere revisión humana." : "Resultado revisado por el operador.", r.requiere_revision_humana ? "warning" : "")}</div><div class="actions" style="margin-top:18px">${button(meta.config.simulacion_correo ? "Simular notificación" : "Notificar a soporte", "notify", "mail", false)}</div>`;
  else {
    const exclude = new Set([
      "_id",
      "version",
      "creado_en",
      "actualizado_en",
      "historico",
      "alumno",
      "proyecto",
      "eliminado",
    ]);
    content = `<dl class="detail-list">${Object.entries(r)
      .filter(([k]) => !exclude.has(k))
      .map(
        ([k, v]) =>
          `<dt>${esc(label(k))}</dt><dd>${esc(typeof v === "object" ? JSON.stringify(v, null, 2) : typeof v === "boolean" ? (v ? "Sí" : "No") : (v ?? "No evaluado"))}</dd>`,
      )
      .join("")}</dl>`;
  }
  content += `<hr><h3>Historial del registro</h3><p class="muted" style="font-size:10px;margin:8px 0 18px">ID ${esc(r._id)} · versión ${r.version} · hora de México</p>${[
    ...r.historico,
  ]
    .reverse()
    .map(
      (h) =>
        `<div class="history-item"><strong>${esc(h.motivo)}</strong><p>${date(h.fecha)} · ${esc(h.operador)}</p>${h.anterior && Object.keys(h.anterior).length ? `<details><summary>Ver datos anteriores</summary><pre class="code">${esc(JSON.stringify(h.anterior, null, 2))}</pre></details>` : ""}</div>`,
    )
    .join(
      "",
    )}<details><summary class="text-link">Ver registro completo</summary><pre class="code">${esc(JSON.stringify(r, null, 2))}</pre></details>`;
  modal("Detalle de " + singular[type], content);
  if ($("#notify"))
    $("#notify").onclick = guarded(async () => {
      if (
        await confirmAction(
          "Notificar a soporte",
          meta.config.simulacion_correo
            ? "Se preparará una notificación de prueba. No se enviará ningún correo."
            : "Se enviará el resumen de este incidente al destinatario SMTP_TO configurado en tu archivo .env.",
          "Confirmar notificación",
        )
      ) {
        const result = await job("/notificar/" + encodeURIComponent(r._id), {
          confirmar: true,
        });
        toast(result.mensaje);
      }
    });
}

function truthPage() {
  main.innerHTML =
    pageHead(
      "Las reglas, paso a paso.",
      "Cambia las premisas y observa cómo se construye cada decisión.",
      "",
      "LOGISMART / LÓGICA PROPOSICIONAL",
    ) +
    `<div class="grid-2"><section class="card card-pad"><h2>Simulador de condiciones</h2><p class="muted" style="font-size:12px;margin:8px 0 22px">Este simulador no guarda accesos en la bitácora.</p><form id="truth-form" class="form-grid">${premiseFields({ P: true, S: true, H: true })}</form><hr><div class="formula">A = P ∧ S ∧ ¬Q<br>E = P ∧ (R ∨ Q)</div><p class="muted" style="font-size:11px;margin-top:12px">Reglas nuevas: B = R ∧ ¬H · F = P ∧ T</p></section><div id="truth-result"></div></div><section class="card"><div class="card-head"><div><h2>Tabla de verdad completa</h2><p>La fila activa se resalta con tus premisas actuales.</p></div></div><div class="card-body"><div class="tabs" id="truth-tabs">${Object.keys(
      meta.tablas,
    )
      .map(
        (name, i) =>
          `<button class="${i === 0 ? "active" : ""}" data-table="${esc(name)}">${esc(name)}</button>`,
      )
      .join(
        "",
      )}</div><div class="table-wrap" id="truth-table"></div></div></section><div style="margin-top:20px">${notice("A y E pueden ser verdaderas a la vez. La política operativa prioriza la inspección sin modificar las fórmulas originales.")}</div>`;
  let selected = Object.keys(meta.tablas)[0],
    p = { P: true, Q: false, R: false, S: true, H: true, T: false };
  const paint = () => {
    const rows = meta.tablas[selected],
      keys = Object.keys(rows[0]);
    $("#truth-table").innerHTML =
      `<table class="truth-table"><thead><tr>${keys.map((k) => `<th>${esc(k)}</th>`).join("")}</tr></thead><tbody>${rows
        .map(
          (r) =>
            `<tr class="${
              Object.keys(r)
                .filter((k) => k in p)
                .every((k) => r[k] === p[k])
                ? "highlight"
                : ""
            }">${Object.values(r)
              .map(
                (v) =>
                  `<td class="${v ? "true" : "false"}">${v ? "V" : "F"}</td>`,
              )
              .join("")}</tr>`,
        )
        .join("")}</tbody></table>`;
  };
  $$("#truth-tabs button").forEach(
    (b) =>
      (b.onclick = () => {
        selected = b.dataset.table;
        $$("#truth-tabs button").forEach((x) =>
          x.classList.toggle("active", x === b),
        );
        paint();
      }),
  );
  wirePremises($("#truth-form"), $("#truth-result"), (values) => {
    p = values;
    paint();
  });
  paint();
}

function assistantReply(r) {
  const report = r.informe && r._id;
  return (
    chatMessage("assistant", r.respuesta_mostrada, r.fuentes || []) +
    `<small class="muted">${r.creado_en ? esc(date(r.creado_en)) + " · " : ""}${esc(label(r.estado))}</small>` +
    (report
      ? `<section class="assistant-report" aria-label="Descargar informe">
      <strong>${icon("file")} ${esc(r.informe.titulo)}</strong>
      <p>${esc(r.informe.total_accesos)} accesos · ${esc(r.informe.camiones_unicos)} camiones únicos</p>
      <div class="actions">${["pdf", "csv", "json"]
        .map(
          (format) =>
            `<button type="button" class="button secondary" data-report-id="${esc(r._id)}" data-report-format="${format}">${icon("download")} Descargar ${format.toUpperCase()}</button>`,
        )
        .join("")}</div>
      <small>Copia guardada al generar el informe. Incluye todos los registros consultados.</small>
    </section>`
      : "")
  );
}

function reportsReady() {
  return (
    meta.capacidades?.includes("informes_accesos_v1") &&
    meta.capacidades?.includes("consulta_datos_v1")
  );
}

function serverWarning() {
  return `<div class="server-warning" role="alert"><strong>Servidor pendiente de reinicio</strong><p>La página se actualizó, pero el servidor sigue ejecutando una versión anterior. Detén LogiSmart con Ctrl+C en su terminal, vuelve a iniciarlo y abre la dirección que indique. Después recarga esta página.</p>${button("Volver a comprobar", "check-server", "refresh", false)}</div>`;
}

function dataSummary(data) {
  const origin = data.origen;
  return `<strong>${origin.tipo === "mongodb" ? "MongoDB consultado" : "Demostración local consultada"}</strong>
    <p>Base: <b>${esc(origin.base)}</b><br>Servidor: ${esc(origin.servidor)}</p>
    <dl class="data-counts"><div><dt>Camiones guardados</dt><dd>${esc(data.colecciones.camiones)}</dd></div><div><dt>Accesos guardados</dt><dd>${esc(data.colecciones.accesos)}</dd></div>${Object.entries(
      data.resultados,
    )
      .map(
        ([state, count]) =>
          `<div><dt>${state === "denegado" ? "Rechazados" : esc(label(state))}</dt><dd>${esc(count)}</dd></div>`,
      )
      .join("")}</dl>
    <p>${origin.tipo === "demo" ? "Estás usando un archivo local. Para guardar en el clúster del profesor, inicia LogiSmart con --atlas." : "Cada informe vuelve a consultar los accesos de este proyecto y guarda su copia en evaluaciones_llm."}</p>
    ${data.colecciones.accesos === 0 ? notice("No hay accesos guardados en esta base. Registra una decisión en Control de acceso para generar el informe.", "warning") : ""}
    <p>Última lectura: ${esc(date(data.consultado_en))}.</p>`;
}

function assistantPage(history) {
  const ready = reportsReady();
  const suggestions = [
    "Genera un informe de los camiones rechazados y sus motivos",
    "Informe de camiones retenidos hoy",
    "¿Por qué CAM-102 fue enviado a inspección?",
  ];
  main.innerHTML =
    pageHead(
      "Pregunta. Recupera. Comprueba.",
      "Explicaciones e informes respaldados por los registros de tu operación.",
      "",
      "LOGISMART / ASISTENTE",
    ) +
    (ready ? "" : serverWarning()) +
    `<div class="chat-layout"><section class="chat-card">
    <div class="chat-header"><div class="assistant-avatar">${icon("spark")}</div><div><strong>Asistente de LogiSmart</strong><small>Primero los datos, después la respuesta</small></div><span class="badge green">Con fuentes</span></div>
    <div class="messages" id="messages">${
      history.length
        ? history
            .map((r) => chatMessage("user", r.pregunta) + assistantReply(r))
            .join("")
        : `<div class="chat-welcome"><div class="welcome-symbol">${icon("search")}</div><h2>¿Qué necesitas consultar?</h2><p>Pregunta por un camión o solicita un informe de accesos rechazados, retenidos, autorizados o en inspección.</p></div>`
    }</div>
    <form class="chat-form" id="assistant-form"><div class="composer"><textarea name="pregunta" id="question" rows="2" required minlength="3" maxlength="1500" placeholder="Ejemplo: informe de camiones rechazados y sus motivos…" aria-label="Pregunta al asistente"></textarea><button type="submit" aria-label="Enviar pregunta">${icon("send")}</button></div><div class="composer-note"><span>Informes con fuentes y descarga PDF, CSV o JSON.</span><span>Ctrl + Enter para enviar</span></div><div class="form-error" role="alert"></div></form>
    </section><aside class="chat-side"><section class="card card-pad"><span class="eyebrow">DATOS DEL INFORME</span><h2>Base de datos consultada</h2><div id="assistant-data" class="assistant-data" role="status" aria-live="polite"></div>${button("Consultar datos ahora", "refresh-assistant-data", "refresh", false)}<p>Versión del servidor: ${esc(meta.version_servidor || "anterior a informes")}.</p></section><section class="card card-pad"><span class="eyebrow">CONSULTAS RÁPIDAS</span><h2>De la pregunta al informe.</h2>
    <div class="report-suggestions">${suggestions.map((prompt) => `<button type="button" class="suggestion" data-prompt="${esc(prompt)}">${icon("chat")}${esc(prompt)}</button>`).join("")}</div>
    <p>Filtra por un resultado y, si lo necesitas, por camión o placa. Para fechas usa <strong>hoy</strong>, <strong>ayer</strong>, <strong>esta semana</strong>, <strong>este mes</strong> o <strong>desde 2026-10-01 hasta 2026-10-07</strong>.</p>
    <p>Las fechas se consultan en UTC. Sin fechas se incluyen todos los registros activos. “Rechazados” corresponde al resultado denegado; las retenciones tienen su propio informe.</p>
    </section><section class="card card-pad"><span class="eyebrow">ESTADO DEL MODELO</span><h3>${meta.config.usar_llm ? "Ollama habilitado" : "Modo extractivo"}</h3><p style="margin-top:10px">${meta.config.usar_llm ? "El modelo selecciona fuentes para las preguntas individuales." : "El LLM está deshabilitado. Se muestran hechos de los registros."} Los informes se calculan directamente con los datos guardados y funcionan también sin Ollama.</p></section></aside></div>`;
  $$("[data-prompt]").forEach(
    (b) =>
      (b.onclick = () => {
        $("#question").value = b.dataset.prompt;
        $("#question").focus();
      }),
  );
  $("#messages").onclick = guarded(async (event) => {
    const b = event.target.closest("[data-report-id]");
    if (!b) return;
    b.disabled = true;
    try {
      await download(
        `/asistente/informes/${encodeURIComponent(b.dataset.reportId)}/${b.dataset.reportFormat}`,
        `LogiSmart_informe.${b.dataset.reportFormat}`,
      );
    } finally {
      b.disabled = false;
    }
  });
  const form = $("#assistant-form");
  const dataContainer = $("#assistant-data");
  const refreshData = $("#refresh-assistant-data");
  const readData = async () => {
    refreshData.disabled = true;
    dataContainer.textContent = "Consultando registros guardados…";
    try {
      const data = await api("/asistente/datos");
      if (dataContainer.isConnected)
        dataContainer.innerHTML = dataSummary(data);
    } catch (error) {
      if (dataContainer.isConnected)
        dataContainer.innerHTML = notice(error.message, "error");
    } finally {
      refreshData.disabled = false;
    }
  };
  if (!ready) {
    dataContainer.textContent =
      "Reinicia el servidor para consultar los datos y generar informes.";
    $$(
      "#assistant-form textarea, #assistant-form button, [data-prompt], [data-report-id], #refresh-assistant-data",
    ).forEach((e) => (e.disabled = true));
    $("#check-server").onclick = () => navigate("asistente");
    return;
  }
  refreshData.onclick = readData;
  void readData();
  wireForm(form, async (d) => {
    const r = await job("/asistente", d);
    if (!form.isConnected) {
      toast("Respuesta guardada en el historial del asistente.");
      return;
    }
    const messages = $("#messages");
    if ($(".chat-welcome", messages)) messages.innerHTML = "";
    messages.insertAdjacentHTML(
      "beforeend",
      chatMessage("user", d.pregunta) + assistantReply(r),
    );
    $("#question").value = "";
    messages.scrollTop = messages.scrollHeight;
    void readData();
  });
  $("#question").onkeydown = (e) => {
    if (e.ctrlKey && e.key === "Enter") {
      e.preventDefault();
      form.requestSubmit();
    }
  };
  $("#messages").scrollTop = $("#messages").scrollHeight;
}

function configPage() {
  const c = meta.config;
  main.innerHTML =
    pageHead(
      "Un entorno a tu medida.",
      "Configura el modelo local y los criterios operativos.",
      "",
      "LOGISMART / CONFIGURACIÓN",
    ) +
    `<div class="settings-grid"><section class="card card-pad"><h2>Preferencias de la aplicación</h2><p class="muted" style="font-size:12px;margin:8px 0 25px">Las preferencias se conservan en este equipo.</p><form id="config-form"><div class="form-grid">${field("operador", "Nombre del operador", "text", c.operador, { minlength: 2, maxlength: 80 })}${field("modelo", "Modelo instalado en Ollama", "text", c.modelo, { maxlength: 100, help: "Ejemplo: llama3.2:3b" })}${field("url_ollama", "Servidor local de Ollama", "text", c.url_ollama, { full: true })}${field("timeout", "Espera máxima por llamada (segundos)", "number", c.timeout, { min: 5, max: 300, step: 1 })}${field("umbral_riesgo", "Umbral de riesgo crítico", "number", c.umbral_riesgo, { min: 1, max: 25, step: 1 })}${field("hora_inicio", "Inicio del horario permitido", "number", c.hora_inicio, { min: 0, max: 23, step: 1, help: "Hora de México · 0 a 23" })}${field("hora_fin", "Fin del horario (exclusivo)", "number", c.hora_fin, { min: 1, max: 24, step: 1, help: "Materiales peligrosos · 1 a 24" })}${field("usar_llm", "Habilitar el modelo local", "checkbox", c.usar_llm)}${field("simulacion_correo", "Simular correo, sin envío real", "checkbox", c.simulacion_correo)}</div><div class="form-error" role="alert"></div><div class="form-footer">${submit("Guardar configuración")}</div></form></section><aside><section class="card card-pad"><span class="eyebrow">ALMACENAMIENTO</span><h2>${meta.modo.includes("DEMOSTRACIÓN") ? "Demostración local" : "MongoDB"}</h2><div class="settings-actions" style="margin-top:18px"><p>${meta.modo.includes("DEMOSTRACIÓN") ? "Los datos de esta sesión se guardan en un archivo JSON local. Para trabajar en Atlas inicia el programa sin --demo." : "Los registros se guardan en la base configurada en tu archivo .env. Comprueba la conexión antes de tu exposición."}</p>${button("Comprobar conexión", "check-connection", "pulse", false)}<p id="connection-result" role="status"></p></div></section><section class="card card-pad" style="margin-top:20px"><span class="eyebrow">DATOS PARA ENSAYAR</span><h2>Prepara una demostración</h2><p class="muted" style="font-size:12px;margin:12px 0 20px">Agrega camiones, accesos, incidentes y riesgos ficticios al almacenamiento activo. Los existentes se conservan.</p>${button("Cargar datos de ejemplo", "load-demo", "plus", false)}</section>${notice("Las credenciales se mantienen en .env y nunca se muestran en esta pantalla. Cambiar el modelo aquí no lo descarga.")}</aside></div>`;
  wireForm($("#config-form"), async (d) => {
    await api("/configuracion", "POST", d);
    meta.config = d;
    toast("Preferencias guardadas.");
    await navigate("configuracion");
  });
  $("#check-connection").onclick = guarded(async () => {
    const r = await job("/conexion");
    if ($("#connection-result"))
      $("#connection-result").textContent = r.mensaje;
    toast(r.mensaje);
  });
  $("#load-demo").onclick = guarded(async () => {
    if (
      await confirmAction(
        "Cargar datos ficticios",
        "Se agregarán datos de ejemplo al almacenamiento activo: " +
          meta.modo +
          ". Los registros existentes se conservan.",
        "Cargar demostración",
      )
    ) {
      const r = await job("/demostracion", { confirmar: true });
      toast(r.mensaje);
    }
  });
}

function reportsPage() {
  if (!reportsReady()) {
    main.innerHTML =
      pageHead("Reportes", "Actualiza el servidor para consultar tus datos.") +
      serverWarning();
    $("#check-server").onclick = () => navigate("reportes");
    return;
  }
  main.innerHTML =
    pageHead(
      "La evidencia, lista para compartir.",
      "Exporta los registros de tu operación y sus historiales.",
      "",
      "LOGISMART / REPORTES",
    ) +
    `<div class="settings-grid"><section class="card card-pad"><h2>Crear un reporte</h2><form id="report-form" style="margin-top:23px"><div class="form-grid">${field("coleccion", "Información que quieres exportar", "select", "accesos", { full: true, options: crud })}${field(
      "resultado",
      "Resultado del acceso",
      "select",
      "todos",
      {
        full: true,
        options: [
          ["todos", "Todos los accesos"],
          ["denegado", "Rechazados (denegados)"],
          ["retenido", "Retenidos"],
          ["inspeccion", "En inspección"],
          ["autorizado", "Autorizados"],
        ],
      },
    )}${field("desde", "Desde (UTC)", "date", "", { optional: true })}${field("hasta", "Hasta (UTC)", "date", "", { optional: true })}</div><div class="report-options" aria-label="Formato de descarga">${[
      ["pdf", "PDF", "Para presentar o imprimir"],
      ["csv", "CSV", "Para analizar en una hoja"],
      ["json", "JSON", "Para conservar la estructura"],
    ]
      .map(
        ([v, n, t], i) =>
          `<button type="button" class="${i === 0 ? "active" : ""}" data-format="${v}" aria-pressed="${i === 0}">${icon("file")}<strong>${n}</strong><small>${t}</small></button>`,
      )
      .join(
        "",
      )}</div><div class="form-error" role="alert"></div>${submit("Descargar reporte")}</form></section><aside class="card card-pad"><span class="eyebrow">TRAZABILIDAD</span><h2>Un registro, su contexto.</h2><p class="muted" style="font-size:12px;line-height:1.9;margin:14px 0 20px">El informe de accesos incluye totales, camiones únicos, motivos y fuentes. Las demás colecciones incluyen los registros activos y sus historiales. Deja las fechas vacías para incluir todo.</p>${notice("Los correos y prompts pueden contener datos personales. Comparte únicamente la información necesaria.", "warning")}</aside></div>`;
  let format = "pdf";
  $$("[data-format]").forEach(
    (b) =>
      (b.onclick = () => {
        format = b.dataset.format;
        $$("[data-format]").forEach((x) => {
          x.classList.toggle("active", x === b);
          x.setAttribute("aria-pressed", String(x === b));
        });
      }),
  );
  const collection = $("#report-form [name=coleccion]");
  const result = $("#report-form [name=resultado]");
  collection.onchange = () => {
    result.disabled = collection.value !== "accesos";
    result.closest(".field").hidden = result.disabled;
  };
  wireForm($("#report-form"), async (d) => {
    const access = d.coleccion === "accesos";
    const query = { desde: d.desde, hasta: d.hasta };
    if (access) query.resultado = d.resultado;
    await download(
      (access ? "/informes/accesos/" : "/exportar/" + d.coleccion + "/") +
        format +
        "?" +
        new URLSearchParams(query),
      `LogiSmart_${d.coleccion}.${format}`,
    );
  });
}

function experimentResults(r) {
  if (!r)
    return empty(
      "Tu experimento comienza aquí",
      "Revisa las etiquetas y ejecuta la comparación para ver las métricas reales.",
      "flask",
    );
  return `<div class="experiment-result">${notice(`${r.etiquetas_revisadas_por_persona}/${r.correos} etiquetas revisadas por una persona. ${r.estado_etiquetado === "revisado" ? "Conjunto revisado." : "Las etiquetas siguen siendo provisionales."}`, r.estado_etiquetado === "revisado" ? "" : "warning")}<div class="metrics" style="margin-top:20px">${[
    "reglas",
    "llm",
    "hibrido",
  ]
    .map((m) => {
      const d = r.metricas[m];
      return metric(
        label(m),
        d.exactitud_categoria == null
          ? "—"
          : (100 * d.exactitud_categoria).toFixed(1) + "%",
        d.estado === "no_ejecutado"
          ? "Modelo no ejecutado"
          : `Exactitud por categoría · ${d.respuestas_validas}/${d.n} respuestas`,
        m === "llm" ? "spark" : "pulse",
        m === "hibrido" ? "blue" : "",
      );
    })
    .join(
      "",
    )}</div><section class="card"><div class="card-head"><div><h2>Matriz de confusión</h2><p>Filas: categoría real · columnas: categoría predicha</p></div><div class="actions">${button("JSON", "export-experiment-json", "download", false)}${button("PDF", "export-experiment-pdf", "download", false)}</div></div><div class="card-body"><div class="tabs">${["reglas", "llm", "hibrido"].map((m, i) => `<button class="${i === 0 ? "active" : ""}" data-method="${m}">${esc(label(m))}</button>`).join("")}</div><div id="confusion"></div><hr><p class="muted" style="font-size:11px;line-height:1.8">${esc(r.advertencia)}</p><p class="muted" style="font-size:10px;margin-top:12px">${date(r.fecha_utc)} · Modelo: ${esc(r.modelo_configurado)} · ${r.correos} correos</p></div></section></div>`;
}
function wireResults(r) {
  if (!r) return;
  const draw = (method) => {
    const m = r.metricas[method];
    $("#confusion").innerHTML =
      m.estado === "no_ejecutado"
        ? empty(
            "LLM no ejecutado",
            "Selecciona la comparación con Ollama para obtener estas mediciones.",
            "spark",
          )
        : `<div class="table-wrap matrix-wrap"><table class="matrix"><thead><tr><th>Real / predicha</th>${m.columnas_predichas.map((c) => `<th>${esc(label(c))}</th>`).join("")}</tr></thead><tbody>${m.matriz_confusion.map((row, i) => `<tr><th>${esc(label(m.filas_reales[i]))}</th>${row.map((n, j) => `<td class="${n ? (i === j ? "correct" : "incorrect") : ""}">${n}</td>`).join("")}</tr>`).join("")}</tbody></table></div><div class="legend"><span>Prioridad correcta: ${(m.exactitud_prioridad * 100).toFixed(1)}%</span><span>Latencia media: ${m.latencia_ms_media?.toFixed(2) ?? "—"} ms</span><span>p95: ${m.latencia_ms_p95?.toFixed(2) ?? "—"} ms</span></div>`;
  };
  $$("[data-method]").forEach(
    (b) =>
      (b.onclick = () => {
        $$("[data-method]").forEach((x) =>
          x.classList.toggle("active", x === b),
        );
        draw(b.dataset.method);
      }),
  );
  draw("reglas");
  $("#export-experiment-json").onclick = guarded(() =>
    download("/experimento/exportar/json", "experimento_clasificacion.json"),
  );
  $("#export-experiment-pdf").onclick = guarded(() =>
    download("/experimento/exportar/pdf", "experimento_clasificacion.pdf"),
  );
}
function experimentPage(corpus, previous) {
  resultExperiment = previous;
  main.innerHTML =
    pageHead(
      "Pon a prueba el clasificador.",
      "Compara reglas, LLM e híbrido con un conjunto de correos etiquetados.",
      "",
      "LOGISMART / EXPERIMENTO",
    ) +
    `<div class="grid-2 grid-equal"><section class="card card-pad"><span class="eyebrow">01 / REVISA EL CONJUNTO</span><h2>La referencia empieza contigo.</h2><p class="muted" style="font-size:12px;margin:11px 0 22px">Cada etiqueta debe ser leída y confirmada por una persona antes de la evaluación final.</p><div class="progress-label"><span>Etiquetas revisadas</span><strong id="corpus-count">${corpus.revisados} / ${corpus.registros.length}</strong></div><progress id="corpus-progress" max="${corpus.registros.length}" value="${corpus.revisados}"></progress><div class="actions" style="margin-top:22px">${button("Revisar correos", "review-corpus", "edit")}${button("Exportar", "export-corpus", "download", false)}</div><details style="margin-top:18px"><summary class="text-link">Importar otro conjunto JSON</summary><p class="muted" style="font-size:11px;margin:10px 0">Conserva el esquema del archivo exportado. Se sustituye únicamente la copia local de revisión.</p><input type="file" id="import-corpus" accept=".json,application/json" aria-label="Importar conjunto JSON"></details></section><section class="card card-pad"><span class="eyebrow">02 / EJECUTA LA COMPARACIÓN</span><h2>Resultados medidos, sin suposiciones.</h2><p class="muted" style="font-size:12px;margin:11px 0 20px">Con Ollama se medirán los tres métodos. Si no responde, quedarán registrados el fallo y el respaldo utilizado.</p><label class="switch-label"><span><strong>Incluir Ollama local</strong><small>${esc(meta.config.modelo)} · puede tardar varios minutos</small></span><input id="experiment-llm" type="checkbox" ${meta.config.usar_llm ? "checked" : ""}></label><div class="actions" style="margin-top:22px">${button("Ejecutar comparación", "run-experiment", "flask")}</div></section></div><div id="experiment-results">${experimentResults(previous)}</div>`;
  wireResults(previous);
  $("#review-corpus").onclick = guarded(async () =>
    reviewCorpus(await api("/corpus")),
  );
  $("#export-corpus").onclick = guarded(() =>
    download("/corpus/exportar", "correos_revisados.json"),
  );
  $("#run-experiment").onclick = guarded(async () => {
    const include = $("#experiment-llm").checked;
    if (
      await confirmAction(
        "Ejecutar experimento",
        include
          ? "Se consultará el modelo local con cada correo y se guardarán las evaluaciones. Puede tardar varios minutos."
          : "Se medirán las reglas y su respaldo. No se producirán métricas del LLM.",
        "Comenzar",
      )
    ) {
      const r = await job("/experimento", { solo_reglas: !include });
      resultExperiment = r;
      if (current === "experimento") {
        $("#experiment-results").innerHTML = experimentResults(r);
        wireResults(r);
      }
      toast(
        "Experimento terminado. Los resultados están disponibles para exportar.",
      );
    }
  });
  $("#import-corpus").onchange = guarded(async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 1_800_000)
      throw new Error("El archivo excede el tamaño permitido (1.8 MB).");
    const data = JSON.parse(await file.text());
    if (
      await confirmAction(
        "Importar conjunto",
        "Se sustituirá tu copia local de correos revisados. Exporta primero si quieres conservarla.",
        "Importar",
      )
    ) {
      await api("/corpus/importar", "POST", {
        registros: data,
        confirmar: true,
      });
      await navigate("experimento");
      toast("Conjunto importado.");
    }
  });
}
function reviewCorpus(initial) {
  // Se conserva una revisión por correo; navegar nunca confirma etiquetas por sí solo.
  let corpus = initial,
    index = 0;
  const draw = () => {
    const r = corpus.registros[index];
    modal(
      "Revisión manual de etiquetas",
      `<form id="review-form"><div class="progress-label"><span>${esc(r.id)} · ${esc(r.registro)}</span><strong>Correo ${index + 1} de ${corpus.registros.length}</strong></div><progress max="${corpus.registros.length}" value="${index + 1}"></progress><h3 style="margin-top:23px">${esc(r.asunto)}</h3><p class="muted" style="font-size:11px;margin-top:6px">${esc(r.remitente)}</p><div class="review-body">${esc(r.cuerpo)}</div><div class="form-grid">${field("categoria_esperada", "Categoría esperada", "select", r.categoria_esperada, { options: meta.categorias })}${field("prioridad_esperada", "Prioridad esperada", "select", r.prioridad_esperada, { options: meta.prioridades })}${field("revisado_humano", "He leído el correo y confirmé personalmente ambas etiquetas", "checkbox", r.revisado_humano, { full: true })}</div><div class="form-error" role="alert"></div><div class="form-footer">${button("Anterior", "review-prev", "arrow", false)}<button class="button primary" type="submit">${icon("check")}${index < corpus.registros.length - 1 ? "Guardar y siguiente" : "Guardar revisión"}</button></div><p class="muted" style="font-size:10px;margin-top:13px">Revisor: ${esc(meta.config.operador)} · Al guardar se conserva también una etiqueta sin confirmar.</p></form>`,
    );
    $("#review-prev").disabled = index === 0;
    const save = async (data) => {
      corpus = await api("/corpus/revisar", "POST", {
        ...data,
        id: r.id,
        revision: corpus.revision,
      });
      if ($("#corpus-count")) {
        $("#corpus-count").textContent =
          `${corpus.revisados} / ${corpus.registros.length}`;
        $("#corpus-progress").value = corpus.revisados;
      }
    };
    $("#review-prev").onclick = guarded(async () => {
      await save(formData($("#review-form")));
      index--;
      draw();
    });
    wireForm($("#review-form"), async (data) => {
      await save(data);
      if (index < corpus.registros.length - 1) {
        index++;
        draw();
      } else {
        $("#dialog").close();
        toast("Conjunto guardado. Etiquetas confirmadas: " + corpus.revisados);
      }
    });
  };
  draw();
}

async function navigate(target) {
  if (!names.includes(target)) target = "panel";
  if (target !== current) {
    query = "";
    status = "";
    page = 1;
  }
  current = target;
  if (location.hash !== "#" + target)
    history.replaceState(null, "", "#" + target);
  const id = ++epoch;
  main.setAttribute("aria-busy", "true");
  $$(".sidebar [data-page]").forEach((a) => {
    a.classList.toggle("active", a.dataset.page === target);
    if (a.dataset.page === target) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  $("#section-name").textContent = label(target);
  main.innerHTML =
    '<div class="page-loading"><span class="spinner"></span><p>Cargando ' +
    esc(label(target).toLowerCase()) +
    "…</p></div>";
  try {
    meta = await api("/estado");
    let data;
    if (target === "panel") data = await api("/panel?" + params());
    else if (crud.includes(target))
      data = (await api("/registros/" + target)).registros;
    else if (target === "asistente")
      data = (await api("/asistente/historial")).registros;
    else if (target === "experimento")
      data = await Promise.all([api("/corpus"), api("/experimento")]);
    if (id !== epoch) return;
    $("#connection").textContent = meta.modo.includes("DEMOSTRACIÓN")
      ? "Demostración local"
      : "MongoDB configurado";
    $("#connection").classList.toggle(
      "demo",
      meta.modo.includes("DEMOSTRACIÓN"),
    );
    if (target === "panel") dashboard(data);
    else if (crud.includes(target)) crudPage(target, data);
    else if (target === "tablas") truthPage();
    else if (target === "asistente") assistantPage(data);
    else if (target === "configuracion") configPage();
    else if (target === "reportes") reportsPage();
    else if (target === "experimento")
      experimentPage(data[0], data[1].resultado);
    icons(main);
  } catch (error) {
    if (id === epoch) showError(error);
  } finally {
    if (id === epoch) main.setAttribute("aria-busy", "false");
  }
}
$("#refresh").onclick = () => navigate(current);
window.addEventListener("hashchange", () => navigate(location.hash.slice(1)));
await navigate(location.hash.slice(1) || "panel");
const pending = meta?.trabajo_activo || sessionStorage.getItem("trabajo");
if (pending) {
  try {
    await pollJob(pending);
    toast("La operación terminó. Consulta los registros actualizados.");
    await navigate(current);
  } catch (e) {
    toast(e.message, true);
  }
}
