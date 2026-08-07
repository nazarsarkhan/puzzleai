const state = { file: null, recommendation: null };
const $ = (id) => document.getElementById(id);

function show(id, visible = true) { $(id).classList.toggle("hidden", !visible); }
function error(message) { $("error").textContent = message; show("error"); }
function clearError() { show("error", false); }

$("image-input").addEventListener("change", (event) => {
  state.file = event.target.files[0];
  if (!state.file) return;
  $("file-name").textContent = state.file.name;
  $("upload-preview").src = URL.createObjectURL(state.file);
  show("upload-preview-row");
});

$("upload-form").addEventListener("submit", async (event) => {
  event.preventDefault(); clearError();
  const data = new FormData(); data.append("file", state.file);
  try {
    const response = await fetch("/api/analyze", { method: "POST", body: data });
    if (!response.ok) throw new Error((await response.json()).detail || "Analysis failed");
    state.recommendation = await response.json();
    $("analysis-preview").src = $("upload-preview").src;
    $("orientation").value = state.recommendation.orientation;
    $("columns").value = state.recommendation.columns;
    $("rows").value = state.recommendation.rows;
    $("crop-mode").value = state.recommendation.crop_mode;
    $("recommendation-source").textContent = state.recommendation.source;
    renderPieceCount();
    $("recommendation-notes").innerHTML = [...state.recommendation.reasons, ...state.recommendation.warnings].map((note) => `<li>${note}</li>`).join("");
    show("recommendation-card");
  } catch (err) { error(err.message); }
});

function renderPieceCount() { $("piece-count").textContent = `${Number($("columns").value) * Number($("rows").value)} puzzle pieces`; }
$("columns").addEventListener("input", renderPieceCount); $("rows").addEventListener("input", renderPieceCount);

$("generate-button").addEventListener("click", async () => {
  clearError(); show("job-card"); $("job-status").textContent = "Starting…"; show("download-link", false); show("completion-preview", false);
  const data = new FormData(); data.append("file", state.file); data.append("columns", $("columns").value); data.append("rows", $("rows").value); data.append("crop_mode", $("crop-mode").value);
  try {
    const response = await fetch("/api/generate", { method: "POST", body: data });
    if (!response.ok) throw new Error((await response.json()).detail || "Generation failed");
    await poll((await response.json()).id);
  } catch (err) { error(err.message); }
});

async function poll(id) {
  const response = await fetch(`/api/jobs/${id}`); const job = await response.json();
  $("job-status").textContent = job.status;
  if (job.status === "ready") {
    $("job-message").textContent = "Package validated and ready for Roblox import.";
    $("completion-preview").src = `/api/jobs/${id}/preview`; show("completion-preview");
    $("download-link").href = `/api/jobs/${id}/download`; show("download-link"); return;
  }
  if (job.status === "failed") { error(job.error || "Generation failed"); return; }
  setTimeout(() => poll(id), 700);
}
