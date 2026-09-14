"use strict";

const formulario = document.querySelector("#formulario");
const entrada = document.querySelector("#dato");
const guardar = document.querySelector("#guardar");
const actualizar = document.querySelector("#actualizar");
const aviso = document.querySelector("#aviso");
const conexion = document.querySelector("#conexion");
const estadoConsulta = document.querySelector("#consulta-estado");
let ocupado = false;
let ultimoDocumento = null;

function mostrarAviso(texto, tipo = "error") {
  aviso.textContent = texto;
  aviso.className = `aviso ${tipo}`;
  aviso.hidden = false;
}

function cambiarEstado(texto, clase) {
  conexion.textContent = texto;
  conexion.className = `estado ${clase}`;
}

function marcarOcupado(valor) {
  ocupado = valor;
  guardar.disabled = valor;
  actualizar.disabled = valor;
  formulario.setAttribute("aria-busy", String(valor));
}

function mostrarDocumento(documento) {
  ultimoDocumento = documento;
  document.querySelector("#documento").hidden = !documento;
  document.querySelector("#vacio").hidden = Boolean(documento);
  estadoConsulta.hidden = true;
  if (!documento) return;
  document.querySelector("#dato-guardado").textContent = documento.dato;
  document.querySelector("#autor").textContent = documento.nombre;
  const fecha = document.querySelector("#fecha");
  const instante = documento.actualizado_en ? new Date(documento.actualizado_en) : null;
  fecha.textContent = instante && !Number.isNaN(instante.getTime())
    ? new Intl.DateTimeFormat("es-MX", { dateStyle: "medium", timeStyle: "short" }).format(instante)
    : "Sin fecha registrada";
  if (instante && !Number.isNaN(instante.getTime())) fecha.dateTime = instante.toISOString();
  else fecha.removeAttribute("datetime");
  document.querySelector("#json").textContent = JSON.stringify({
    _id: documento.id, nombre: documento.nombre, practica: documento.practica,
    dato: documento.dato, actualizado_en: documento.actualizado_en,
  }, null, 2);
}

async function solicitar(url, opciones = {}) {
  const respuesta = await fetch(url, { credentials: "same-origin", cache: "no-store", ...opciones });
  const datos = await respuesta.json();
  if (!respuesta.ok || !datos.ok) {
    const error = new Error(datos.mensaje || "No se pudo completar la operación.");
    error.estado = respuesta.status;
    error.guardado = Boolean(datos.guardado);
    throw error;
  }
  return datos;
}

function fallo(error, esGuardado = false) {
  const mensaje = error.estado ? error.message
    : "No se pudo contactar con Python. Comprueba que la terminal del servidor siga abierta."
      + (esGuardado ? " Pulsa Actualizar antes de volver a guardar." : "");
  mostrarAviso(mensaje, error.guardado ? "atencion" : "error");
  if (error.estado === 400 || error.estado === 413) return;
  cambiarEstado("Conexión por comprobar", "desconectado");
  estadoConsulta.textContent = ultimoDocumento
    ? "Se muestra la última consulta correcta; puede haber cambios pendientes de consultar."
    : "No se pudo consultar el documento. Pulsa Actualizar para reintentar.";
  estadoConsulta.hidden = false;
  document.querySelector("#vacio").hidden = true;
}

async function consultar() {
  if (ocupado) return;
  marcarOcupado(true);
  aviso.hidden = true;
  cambiarEstado("Comprobando conexión…", "esperando");
  try {
    const datos = await solicitar(document.querySelector(".consulta").dataset.url);
    mostrarDocumento(datos.documento);
    cambiarEstado("Atlas conectado", "conectado");
  } catch (error) {
    fallo(error);
  } finally {
    marcarOcupado(false);
  }
}

entrada.addEventListener("input", () => {
  const cantidad = [...entrada.value].length;
  entrada.setCustomValidity(cantidad > 1000 ? "Escribe hasta 1000 caracteres." : "");
  document.querySelector("#contador").textContent = `${cantidad} / 1000`;
});

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  if (ocupado) return;
  if (!entrada.value.trim()) {
    entrada.setCustomValidity("Escribe un dato; no puede contener solamente espacios.");
    entrada.reportValidity();
    return;
  }
  marcarOcupado(true);
  aviso.hidden = true;
  guardar.textContent = "Guardando…";
  try {
    const datos = await solicitar(formulario.action, { method: "POST", body: new FormData(formulario) });
    mostrarDocumento(datos.documento);
    cambiarEstado("Atlas conectado", "conectado");
    mostrarAviso(datos.mensaje, "exito");
  } catch (error) {
    fallo(error, true);
  } finally {
    guardar.textContent = "Guardar en Atlas ↗";
    marcarOcupado(false);
  }
});

actualizar.addEventListener("click", consultar);
consultar();
