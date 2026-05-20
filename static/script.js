// ── Mermaid init ────────────────────────────────────────
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  flowchart: { curve: 'linear', useMaxWidth: true }
});

// ── Element refs ─────────────────────────────────────────
const dropzone       = document.getElementById('dropzone');
const fileInput      = document.getElementById('file-input');
const dzIdle         = document.getElementById('dz-idle');
const dzOver         = document.getElementById('dz-over');
const previewWrap    = document.getElementById('preview-wrap');
const previewImg     = document.getElementById('preview-img');
const fileMeta       = document.getElementById('file-meta');
const changeBtn      = document.getElementById('change-btn');
const digitiseBtn    = document.getElementById('digitise-btn');
const btnText        = document.getElementById('btn-text');
const btnArrow       = document.getElementById('btn-arrow');
const btnSpinner     = document.getElementById('btn-spinner');
const stages         = document.getElementById('stages');
const stage1         = document.getElementById('stage-1');
const stage2         = document.getElementById('stage-2');
const stage3         = document.getElementById('stage-3');
const emptyState     = document.getElementById('empty-state');
const result         = document.getElementById('result');
const metaBar        = document.getElementById('meta-bar');
const mermaidOutput  = document.getElementById('mermaid-output');
const mermaidDisplay = document.getElementById('mermaid-code-display');
const jsonDisplay    = document.getElementById('json-display');
const renderFallback = document.getElementById('render-fallback');
const copyMermaidBtn = document.getElementById('copy-mermaid-btn');
const downloadBtn    = document.getElementById('download-btn');
const retryBtn       = document.getElementById('retry-btn');
const toast          = document.getElementById('toast');

let selectedFile = null;
let lastMermaid  = '';
let toastTimer   = null;

// ── Toast ────────────────────────────────────────────────
function showToast(msg, type = 'default') {
  toast.textContent = msg;
  toast.className = `toast show${type !== 'default' ? ` toast--${type}` : ''}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.className = 'toast'; }, 2800);
}

// ── File handling ────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function handleFile(file) {
  if (!file) return;

  const allowed = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowed.includes(file.type)) {
    showToast('Only JPEG, PNG, and WebP files are supported', 'error');
    return;
  }

  if (file.size > 5 * 1024 * 1024) {
    showToast('File too large — maximum size is 5MB', 'error');
    return;
  }

  selectedFile = file;
  previewImg.src = URL.createObjectURL(file);
  fileMeta.textContent = `${file.name}  ·  ${formatBytes(file.size)}`;

  dzIdle.style.display = 'none';
  previewWrap.style.display = 'flex';
  previewWrap.style.flexDirection = 'column';
  digitiseBtn.style.display = 'flex';
  stages.style.display = 'none';

  // Reset stages
  [stage1, stage2, stage3].forEach(s => s.className = 'stage');

  // Reset result
  result.style.display = 'none';
  emptyState.style.display = 'flex';
}

// Drop zone events
dropzone.addEventListener('click', (e) => {
  if (e.target !== changeBtn && !changeBtn.contains(e.target)) {
    if (!selectedFile) fileInput.click();
  }
});

fileInput.addEventListener('change', (e) => handleFile(e.target.files[0]));
changeBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  fileInput.click();
});

dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.classList.add('over');
  dzOver.style.display = 'block';
  if (dzIdle && !selectedFile) dzIdle.style.display = 'none';
});

dropzone.addEventListener('dragleave', () => {
  dropzone.classList.remove('over');
  dzOver.style.display = 'none';
  if (!selectedFile) dzIdle.style.display = 'block';
});

dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('over');
  dzOver.style.display = 'none';
  handleFile(e.dataTransfer.files[0]);
});

// ── Stage helpers ────────────────────────────────────────
function setStage(stage, stageEl) {
  // Mark previous stages done
  if (stage >= 1) stage1.className = stage === 1 ? 'stage active' : 'stage done';
  if (stage >= 2) stage2.className = stage === 2 ? 'stage active' : stage > 2 ? 'stage done' : 'stage';
  if (stage >= 3) stage3.className = stage === 3 ? 'stage active' : stage > 3 ? 'stage done' : 'stage';
}

function allStagesDone() {
  stage1.className = 'stage done';
  stage2.className = 'stage done';
  stage3.className = 'stage done';
}

// ── Tabs ─────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('tab--active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('tab-content--active'));
    tab.classList.add('tab--active');
    document.getElementById('tab-' + tab.dataset.tab).classList.add('tab-content--active');
  });
});

// ── Meta bar ─────────────────────────────────────────────
function buildMetaBar(data) {
  const type = data.diagram_type || 'flowchart';
  const nodes = (data.nodes || []).length;
  const edges = (data.edges || []).length;
  const title = data.title;

  metaBar.innerHTML = `
    <span class="meta-chip meta-chip--type">${type}</span>
    <span class="meta-chip">${nodes} nodes</span>
    <span class="meta-chip">${edges} edges</span>
    ${title ? `<span class="meta-chip">${title}</span>` : ''}
  `;
}

// ── Mermaid render ───────────────────────────────────────
async function renderMermaid(code) {
  try {
    mermaidOutput.innerHTML = '';
    mermaidOutput.removeAttribute('data-processed');
    mermaidOutput.textContent = code;
    await mermaid.run({ nodes: [mermaidOutput] });
    renderFallback.style.display = 'none';
  } catch (err) {
    mermaidOutput.innerHTML = '';
    renderFallback.style.display = 'flex';
  }
}

// ── Digitise ─────────────────────────────────────────────
async function doDigitise() {
  if (!selectedFile) return;

  // UI: loading state
  btnText.textContent = 'Processing...';
  btnArrow.style.display = 'none';
  btnSpinner.style.display = 'block';
  digitiseBtn.disabled = true;
  stages.style.display = 'flex';
  emptyState.style.display = 'none';
  result.style.display = 'none';
  renderFallback.style.display = 'none';

  setStage(1);

  const formData = new FormData();
  formData.append('file', selectedFile);

  // Simulate stage 1 timing
  await new Promise(r => setTimeout(r, 600));
  setStage(2);

  try {
    const res = await fetch('/digitise', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Something went wrong');
    }

    setStage(3);
    await new Promise(r => setTimeout(r, 400));

    lastMermaid = data.mermaid;

    // Populate outputs
    mermaidDisplay.textContent = data.mermaid;
    jsonDisplay.textContent = JSON.stringify(data.raw, null, 2);
    buildMetaBar(data.raw);

    // Render diagram
    await renderMermaid(data.mermaid);

    allStagesDone();
    result.style.display = 'flex';

    // Reset to diagram tab
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('tab--active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('tab-content--active'));
    document.querySelector('[data-tab="diagram"]').classList.add('tab--active');
    document.getElementById('tab-diagram').classList.add('tab-content--active');

    showToast('Diagram extracted successfully', 'success');

  } catch (err) {
    [stage1, stage2, stage3].forEach(s => { if (s.classList.contains('active')) s.className = 'stage'; });
    showToast(err.message || 'Extraction failed', 'error');
    emptyState.style.display = 'flex';
  } finally {
    btnText.textContent = 'Digitise';
    btnArrow.style.display = 'block';
    btnSpinner.style.display = 'none';
    digitiseBtn.disabled = false;
  }
}

digitiseBtn.addEventListener('click', doDigitise);
retryBtn.addEventListener('click', doDigitise);

// ── Copy Mermaid ─────────────────────────────────────────
copyMermaidBtn.addEventListener('click', async () => {
  await navigator.clipboard.writeText(lastMermaid);
  showToast('Mermaid code copied', 'success');
});

// ── Download .md ─────────────────────────────────────────
downloadBtn.addEventListener('click', () => {
  const content = `\`\`\`mermaid\n${lastMermaid}\n\`\`\``;
  const blob = new Blob([content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'diagram.md';
  a.click();
  URL.revokeObjectURL(url);
  showToast('Downloaded diagram.md', 'success');
});