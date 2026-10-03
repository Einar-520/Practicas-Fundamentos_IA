/** Pruebas de navegación y formularios reales. Requiere servidores_web.py activo. */
import { createRequire } from "node:module";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import assert from "node:assert/strict";
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_PACKAGE || "playwright");
const output = resolve(process.env.CAPTURAS || "tests/capturas");
await mkdir(output, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  ...(process.env.CHROMIUM_EJECUTABLE
    ? { executablePath: process.env.CHROMIUM_EJECUTABLE }
    : {}),
  args: ["--no-sandbox"],
});
const page = await browser.newPage({
  viewport: { width: 1440, height: 1020 },
  locale: "es-MX",
});
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const reports = [];
async function check(name, fn) {
  await fn();
  reports.push(name);
  console.log("OK", name);
}
async function section(name) {
  await page.getByRole("link", { name, exact: true }).click();
  await page.waitForFunction(
    (expected) =>
      document
        .querySelector('.sidebar a[aria-current="page"]')
        ?.textContent.trim() === expected &&
      document.querySelector("main").getAttribute("aria-busy") === "false",
    name,
  );
  assert.equal(await page.getByText("No se pudo cargar esta vista").count(), 0);
}
async function shot(name) {
  await page.screenshot({
    path: resolve(output, name + ".png"),
    fullPage: true,
    animations: "disabled",
  });
}
try {
  await page.goto("http://127.0.0.1:9162");
  await page
    .getByRole("heading", { name: "Tu operación, en perspectiva." })
    .waitFor();
  await check("Panel y gráficas con datos de demostración", async () => {
    assert.equal(
      await page
        .locator(".metric-value")
        .allTextContents()
        .then((v) => v.join(",")),
      "4,4,3,0",
    );
    await shot("01_panel");
  });
  await check("CRUD de camiones y texto sin ejecución de HTML", async () => {
    await section("Camiones");
    await page
      .getByRole("button", { name: "Nuevo camión", exact: true })
      .click();
    await page.getByLabel("Identificador", { exact: true }).fill("CAM-222");
    await page.getByLabel("Placa", { exact: true }).fill("XYZ-222-D");
    await page
      .getByLabel("Empresa", { exact: true })
      .fill("<img src=x onerror=window.inyeccion=1>");
    await page.getByLabel("Autorización previa", { exact: true }).check();
    await page.getByLabel("Conductor certificado", { exact: true }).check();
    await page.getByLabel("Folio del certificado").fill("CERT-222");
    await page.getByLabel("Certificación vigente hasta").fill("2035-01-01");
    await page
      .getByRole("button", { name: "Guardar registro", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Editar CAM-222", exact: true })
      .waitFor();
    assert.equal(await page.evaluate(() => window.inyeccion), undefined);
    await page
      .getByRole("button", { name: "Editar CAM-222", exact: true })
      .click();
    await page
      .getByLabel("Empresa", { exact: true })
      .fill("Transportes de prueba");
    await page
      .getByRole("button", { name: "Guardar registro", exact: true })
      .click();
    await page
      .getByRole("cell", { name: "Transportes de prueba", exact: true })
      .waitFor();
    await page
      .getByRole("searchbox", { name: "Buscar registros" })
      .fill("CAM-222");
    assert.equal(await page.locator("tbody tr").count(), 1);
  });
  await check("Captura de acceso con búsqueda y semáforo", async () => {
    await section("Control de acceso");
    await page
      .getByRole("button", { name: "Nuevo acceso", exact: true })
      .click();
    await page.getByLabel("Placa", { exact: true }).fill("XYZ-222-D");
    await page
      .getByRole("button", { name: "Buscar placa y cargar P / S", exact: true })
      .click();
    await page.waitForFunction(
      () => document.querySelector("#f-camion_id").value === "CAM-222",
    );
    await page.locator("#f-R").check();
    await page.locator("#f-H").check();
    await page
      .locator("#access-preview .decision")
      .filter({ hasText: "Inspección" })
      .waitFor();
    await shot("02_acceso");
    await page
      .getByRole("button", { name: "Guardar registro", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Ver detalle de CAM-222", exact: true })
      .waitFor();
  });
  await check("Clasificación y revisión humana de incidente", async () => {
    await section("Incidentes");
    await page
      .getByRole("button", { name: "Clasificar correo", exact: true })
      .click();
    await page.getByLabel("Asunto del correo").fill("Fuga de prueba web");
    await page
      .getByLabel("Contenido del correo")
      .fill("Fuga de químico inflamable del CAM-222 en andén 3.");
    await page
      .getByRole("button", { name: "Clasificar y guardar", exact: true })
      .click();
    await page.getByRole("heading", { name: "Detalle de incidente" }).waitFor();
    await page
      .getByRole("button", { name: "Cerrar diálogo", exact: true })
      .click();
    const row = page
      .locator("tbody tr")
      .filter({ hasText: "Fuga de prueba web" });
    await row
      .getByRole("button", { name: "Editar incidente", exact: true })
      .click();
    await page.getByLabel("Estado del incidente").selectOption("cerrado");
    await page.getByLabel("Pendiente de revisión humana").uncheck();
    await page
      .getByLabel("Motivo de la corrección")
      .fill("Revisado por operador durante la prueba.");
    await page
      .getByRole("button", { name: "Guardar registro", exact: true })
      .click();
    await page.locator("#table-filter").selectOption("cerrado");
    await page.getByRole("cell", { name: "Cerrado", exact: true }).waitFor();
    assert.equal(await page.locator("tbody tr").count(), 1);
  });
  await check("Simulador y reglas adicionales", async () => {
    await section("Tablas de verdad");
    await page
      .locator("#truth-result .decision")
      .filter({ hasText: "Autorizado" })
      .waitFor();
    await page.locator("#f-T").check();
    await page
      .locator("#truth-result .decision")
      .filter({ hasText: "Retenido" })
      .waitFor();
    assert.equal(await page.locator(".truth-table tbody tr").count(), 16);
    await shot("03_reglas");
  });
  await check("Asistente con fuentes recuperadas", async () => {
    await section("Asistente con fuentes");
    await page
      .getByLabel("Pregunta al asistente")
      .fill("¿Por qué CAM-102 fue a inspección?");
    await page
      .getByRole("button", { name: "Enviar pregunta", exact: true })
      .click();
    await page.locator(".source-pill").first().waitFor();
    assert.match(
      await page.locator(".source-pill").first().textContent(),
      /accesos:/,
    );
  });
  await check("Riesgos y evaluación con revisión individual", async () => {
    await section("Riesgos éticos");
    assert.equal(await page.locator(".risk-row").count(), 6);
    await shot("04_riesgos");
    await section("Experimento");
    await page
      .getByRole("button", { name: "Revisar correos", exact: true })
      .click();
    await page
      .getByLabel("He leído el correo y confirmé personalmente ambas etiquetas")
      .check();
    await page
      .getByRole("button", { name: "Guardar y siguiente", exact: true })
      .click();
    await page.getByText("Correo 2 de 30", { exact: true }).waitFor();
    await page
      .getByRole("button", { name: "Cerrar diálogo", exact: true })
      .click();
    assert.equal(await page.locator("#corpus-count").textContent(), "1 / 30");
    await page
      .getByRole("button", { name: "Ejecutar comparación", exact: true })
      .click();
    await page.getByRole("button", { name: "Comenzar", exact: true }).click();
    await page.getByRole("heading", { name: "Matriz de confusión" }).waitFor();
    assert.match(
      await page.locator("#experiment-results").textContent(),
      /73.3%/,
    );
  });
  await check("Reportes y configuración", async () => {
    await section("Reportes");
    const pendingDownload = page.waitForEvent("download");
    await page
      .getByRole("button", { name: "Descargar reporte", exact: true })
      .click();
    const downloaded = await pendingDownload;
    assert.equal(downloaded.suggestedFilename(), "LogiSmart_accesos.pdf");
    await section("Configuración");
    await page.getByLabel("Nombre del operador").fill("Revisor web");
    await page
      .getByRole("button", { name: "Guardar configuración", exact: true })
      .click();
    await page.getByText("Preferencias guardadas.", { exact: true }).waitFor();
    await section("Evaluaciones LLM");
  });
  await check("Baja desde la tabla y confirmación", async () => {
    await section("Camiones");
    await page
      .getByRole("button", { name: "Dar de baja CAM-222", exact: true })
      .click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Dar de baja", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Editar CAM-222", exact: true })
      .waitFor({ state: "detached" });
    assert.equal(
      await page
        .getByRole("button", { name: "Editar CAM-222", exact: true })
        .count(),
      0,
    );
  });
  await check("Tutor web con chat resumen y exportación", async () => {
    await page.goto("http://127.0.0.1:9161");
    await page
      .getByRole("heading", { name: "Vamos a entender SQL." })
      .waitFor();
    await shot("05_tutor");
    await page
      .getByLabel("Pregunta para el tutor de SQL")
      .fill(
        "¿Cómo consulto los títulos? <img src=x onerror=window.inyeccion=1>",
      );
    await page
      .getByRole("button", { name: "Enviar pregunta", exact: true })
      .click();
    await page.locator(".bubble code").waitFor();
    assert.equal(await page.evaluate(() => window.inyeccion), undefined);
    await page
      .getByRole("button", { name: "Resumir mi historial", exact: true })
      .click();
    await page
      .locator("#summary")
      .filter({ hasText: "Practicamos SELECT" })
      .waitFor();
    await shot("06_tutor_conversacion");
    const pending = page.waitForEvent("download");
    await page
      .getByRole("button", { name: "Exportar conversación", exact: true })
      .click();
    assert.equal(
      (await pending).suggestedFilename(),
      "historial_tutor_sql.json",
    );
  });
  await check("Diseño móvil sin desbordamiento horizontal", async () => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("http://127.0.0.1:9162");
    await page
      .getByRole("heading", { name: "Tu operación, en perspectiva." })
      .waitFor();
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      true,
    );
    await shot("07_movil");
    await page
      .getByRole("button", { name: "Abrir navegación", exact: true })
      .click();
    await section("Camiones");
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      true,
    );
    await page.goto("http://127.0.0.1:9161");
    await page.getByLabel("Pregunta para el tutor de SQL").waitFor();
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      true,
    );
  });
  assert.deepEqual(errors, []);
  console.log(
    JSON.stringify(
      {
        flujos_aprobados: reports.length,
        errores_javascript: errors,
        capturas: output,
      },
      null,
      2,
    ),
  );
} finally {
  await browser.close();
}
