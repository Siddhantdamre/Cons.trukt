import { evaluateTrench, reportSummary } from "./engine.mjs";

const STORAGE_KEY = "cons-trukt-trench-preplan-v1";
const form = document.querySelector("#trench-form");
const resultShell = document.querySelector("#result-shell");
const emptyState = document.querySelector("#empty-state");
const canvas = document.querySelector("#trench-canvas");
let currentResult = null;

function formPayload() {
  const data = new FormData(form);
  return {
    project: data.get("project"),
    location: data.get("location"),
    depthFt: data.get("depth"),
    bottomWidthFt: data.get("bottomWidth"),
    reportedSoil: data.get("soil"),
    competentPerson: data.get("competentPerson"),
    fissured: data.has("fissured"),
    vibration: data.has("vibration"),
    previouslyDisturbed: data.has("previouslyDisturbed"),
    waterSeepage: data.has("waterSeepage"),
    submerged: data.has("submerged"),
    layeredDipping: data.has("layeredDipping"),
    adjacentStructure: data.has("adjacentStructure"),
    surcharge: data.has("surcharge"),
    hazardousAtmosphere: data.has("hazardousAtmosphere"),
    competentPersonConfirmed: data.has("competentPersonConfirmed"),
    checks: {
      utilities: data.has("check-utilities"),
      spoil: data.has("check-spoil"),
      egress: data.has("check-egress"),
      inspection: data.has("check-inspection"),
      weather: data.has("check-weather"),
    },
  };
}

function saveDraft(payload) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

function restoreDraft() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return;
  try {
    const payload = JSON.parse(raw);
    const values = {
      project: payload.project,
      location: payload.location,
      depth: payload.depthFt,
      bottomWidth: payload.bottomWidthFt,
      soil: payload.reportedSoil,
      competentPerson: payload.competentPerson,
    };
    for (const [name, value] of Object.entries(values)) {
      const input = form.elements.namedItem(name);
      if (input && value !== undefined && value !== null) input.value = value;
    }
    const booleans = [
      "fissured", "vibration", "previouslyDisturbed", "waterSeepage", "submerged",
      "layeredDipping", "adjacentStructure", "surcharge", "hazardousAtmosphere",
      "competentPersonConfirmed",
    ];
    for (const name of booleans) {
      const input = form.elements.namedItem(name);
      if (input) input.checked = Boolean(payload[name]);
    }
    for (const key of ["utilities", "spoil", "egress", "inspection", "weather"]) {
      const input = form.elements.namedItem(`check-${key}`);
      if (input) input.checked = Boolean(payload.checks?.[key]);
    }
  } catch {
    localStorage.removeItem(STORAGE_KEY);
  }
}

function text(id, value) {
  document.querySelector(`#${id}`).textContent = value;
}

function drawTrench(result) {
  const context = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  context.clearRect(0, 0, width, height);

  context.fillStyle = "#dbeaf2";
  context.fillRect(0, 0, width, height);
  context.fillStyle = "#8f7452";
  context.fillRect(0, 62, width, height - 62);

  const bottomY = 245;
  const topY = 78;
  const centerX = width / 2;
  const maxDisplayedWidth = Math.max(result.topWidthFt, result.bottomWidthFt, 12);
  const scale = Math.min(22, (width - 120) / maxDisplayedWidth);
  const bottomHalf = (result.bottomWidthFt * scale) / 2;
  const topHalf = (result.topWidthFt * scale) / 2;

  context.beginPath();
  context.moveTo(centerX - topHalf, topY);
  context.lineTo(centerX - bottomHalf, bottomY);
  context.lineTo(centerX + bottomHalf, bottomY);
  context.lineTo(centerX + topHalf, topY);
  context.closePath();
  context.fillStyle = "#f7f8f5";
  context.fill();
  context.strokeStyle = "#263c32";
  context.lineWidth = 3;
  context.stroke();

  context.strokeStyle = "#255e8a";
  context.lineWidth = 1.5;
  context.setLineDash([6, 5]);
  context.beginPath();
  context.moveTo(centerX, topY);
  context.lineTo(centerX, bottomY);
  context.stroke();
  context.setLineDash([]);

  context.fillStyle = "#17201d";
  context.font = "700 14px Inter, sans-serif";
  context.textAlign = "center";
  context.fillText(`${result.topWidthFt} ft top width`, centerX, 35);
  context.fillText(`${result.bottomWidthFt} ft bottom`, centerX, 273);

  context.save();
  context.translate(centerX + 17, (topY + bottomY) / 2);
  context.rotate(-Math.PI / 2);
  context.fillText(`${result.depthFt} ft depth`, 0, 0);
  context.restore();

  context.textAlign = "left";
  context.fillStyle = "#ffffff";
  context.font = "700 13px Inter, sans-serif";
  const slopeLabel = result.rpeRequired
    ? "RPE design required"
    : `${result.slopeRatio}:1 H:V`;
  context.fillText(slopeLabel, 18, 88);
  context.font = "500 12px Inter, sans-serif";
  context.fillText(`${result.effectiveSoil} planning envelope`, 18, 106);
}

function render(result) {
  currentResult = result;
  emptyState.classList.add("hidden");
  resultShell.classList.remove("hidden");

  text("report-title", result.project || "Excavation pre-plan");
  text(
    "report-subtitle",
    [result.location, result.competentPerson && `Competent person: ${result.competentPerson}`]
      .filter(Boolean)
      .join(" | ") || "Project details not entered",
  );

  const status = document.querySelector("#status");
  const isReady = result.disposition === "ready-for-review";
  status.textContent = isReady ? "Ready for review" : "Hold before entry";
  status.classList.toggle("ready", isReady);

  text("metric-soil", result.effectiveSoil);
  text("metric-slope", result.rpeRequired ? "RPE design" : `${result.slopeRatio}:1 H:V`);
  text("metric-width", result.rpeRequired ? "By design" : `${result.topWidthFt} ft`);
  text("metric-authority", result.rpeRequired ? "Registered PE" : "Competent person");

  const decision = document.querySelector("#decision");
  decision.classList.toggle("ready", isReady);
  decision.replaceChildren();
  const heading = document.createElement("strong");
  heading.textContent = result.system.headline;
  const detail = document.createElement("p");
  detail.textContent = result.system.detail;
  decision.append(heading, detail);

  const warnings = [...result.warnings];
  for (const item of result.incompleteChecks) {
    warnings.push(`Incomplete pre-entry confirmation: ${item.label}.`);
  }
  if (warnings.length === 0) {
    warnings.push("No additional hold points were generated from the entered conditions.");
  }
  document.querySelector("#warnings").replaceChildren(
    ...warnings.map((warning) => {
      const li = document.createElement("li");
      li.textContent = warning;
      return li;
    }),
  );

  document.querySelector("#report-checks").replaceChildren(
    ...result.checks.filter((item) => item.required).map((item) => {
      const li = document.createElement("li");
      const mark = document.createElement("span");
      mark.className = `mark${item.checked ? " done" : ""}`;
      mark.textContent = item.checked ? "OK" : "HOLD";
      const label = document.createElement("span");
      label.textContent = item.label;
      li.append(mark, label);
      return li;
    }),
  );

  document.querySelector("#citations").replaceChildren(
    ...result.citations.map((citation) => {
      const li = document.createElement("li");
      const link = document.createElement("a");
      link.href = citation.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = citation.clause;
      const note = document.createElement("small");
      note.textContent = citation.note;
      link.append(note);
      li.append(link);
      return li;
    }),
  );

  drawTrench(result);
  resultShell.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  try {
    const payload = formPayload();
    saveDraft(payload);
    render(evaluateTrench(payload));
  } catch (error) {
    window.alert(error instanceof Error ? error.message : "Could not evaluate this trench.");
  }
});

document.querySelector("#reset-button").addEventListener("click", () => {
  localStorage.removeItem(STORAGE_KEY);
  form.reset();
  document.querySelector("#depth").value = "8";
  document.querySelector("#bottom-width").value = "3";
  document.querySelector("#soil").value = "Type A";
  document.querySelector('[name="vibration"]').checked = true;
  currentResult = null;
  resultShell.classList.add("hidden");
  emptyState.classList.remove("hidden");
});

document.querySelector("#copy-button").addEventListener("click", async () => {
  if (!currentResult) return;
  await navigator.clipboard.writeText(reportSummary(currentResult));
  const button = document.querySelector("#copy-button");
  const original = button.textContent;
  button.textContent = "Copied";
  setTimeout(() => { button.textContent = original; }, 1200);
});

document.querySelector("#print-button").addEventListener("click", () => window.print());

document.querySelector("#download-button").addEventListener("click", () => {
  if (!currentResult) return;
  const blob = new Blob([JSON.stringify(currentResult, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  const slug = (currentResult.project || "excavation-preplan")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  anchor.href = url;
  anchor.download = `${slug || "excavation-preplan"}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
});

restoreDraft();
