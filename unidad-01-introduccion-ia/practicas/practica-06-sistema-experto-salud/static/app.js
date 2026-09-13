"use strict";
const formulario = document.querySelector("#formulario");
const boton = document.querySelector("#evaluar");
const error = document.querySelector("#error");
const resultado = document.querySelector("#resultado");
let reporte = "";
let solicitud = 0;
let edicion = 0;

function mostrar(datos) {
  resultado.hidden = false;
  document.querySelector("#espera").hidden = true;
  document.querySelector("#nota-edicion").hidden = true;
  const titulo = document.querySelector("#diagnostico");
  titulo.textContent = datos.titulo;
  titulo.className = datos.clase || "neutral";
  const mensajes = document.querySelector("#mensajes");
  mensajes.replaceChildren();
  for (const texto of datos.mensajes || []) {
    const p = document.createElement("p"); p.textContent = texto; mensajes.append(p);
  }
  const tablas = document.querySelector("#tablas"); tablas.replaceChildren();
  for (const contenido of datos.tablas || []) {
    const bloque = document.createElement("section");
    const nombre = document.createElement("h4"); nombre.textContent = contenido.titulo; bloque.append(nombre);
    const envoltura = document.createElement("div"); envoltura.className = "tabla";
    const tabla = document.createElement("table");
    const cabecera = document.createElement("thead"); const fila = document.createElement("tr");
    for (const etiqueta of contenido.encabezados) {
      const celda = document.createElement("th"); celda.scope = "col"; celda.textContent = etiqueta; fila.append(celda);
    }
    cabecera.append(fila); tabla.append(cabecera);
    const cuerpo = document.createElement("tbody");
    for (const valores of contenido.filas) {
      const fila = document.createElement("tr");
      for (const valor of valores) {
        const celda = document.createElement("td"); celda.textContent = valor; fila.append(celda);
      }
      cuerpo.append(fila);
    }
    tabla.append(cuerpo); envoltura.append(tabla); bloque.append(envoltura); tablas.append(bloque);
  }
  reporte = datos.reporte || "";
  document.querySelector("#descargar").hidden = !reporte;
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const actual = ++solicitud;
  const edicionEnviada = edicion;
  boton.disabled = true; formulario.setAttribute("aria-busy", "true"); error.hidden = true;
  try {
    const respuesta = await fetch(formulario.action, { method: "POST", body: new FormData(formulario), credentials: "same-origin" });
    const datos = await respuesta.json();
    if (actual !== solicitud) return;
    if (!respuesta.ok || !datos.ok) throw new Error(datos.mensaje || "No se pudo evaluar el formulario.");
    mostrar(datos.resultado);
    document.querySelector("#nota-edicion").hidden = edicion === edicionEnviada;
  } catch (fallo) {
    if (actual !== solicitud) return;
    error.textContent = fallo instanceof TypeError ? "No se pudo contactar con Python. Comprueba la terminal del servidor." : fallo.message;
    error.hidden = false;
  } finally {
    if (actual === solicitud) { boton.disabled = false; formulario.setAttribute("aria-busy", "false"); }
  }
});
formulario.addEventListener("input", () => {
  edicion++;
  if (!resultado.hidden) document.querySelector("#nota-edicion").hidden = false;
});
formulario.addEventListener("reset", () => {
  solicitud++; boton.disabled = false; formulario.setAttribute("aria-busy", "false");
  resultado.hidden = true; document.querySelector("#espera").hidden = false; error.hidden = true; reporte = "";
});
document.querySelector("#descargar").addEventListener("click", () => {
  const url = URL.createObjectURL(new Blob([reporte], {type: "text/plain;charset=utf-8"}));
  const enlace = document.createElement("a"); enlace.href = url; enlace.download = "reporte_diagnostico.txt"; enlace.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
if (document.querySelector("main").dataset.numero === "1") formulario.requestSubmit();
