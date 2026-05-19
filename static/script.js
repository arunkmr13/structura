mermaid.initialize({ 
  startOnLoad: false, 
  theme: 'default',
  flowchart: { curve: 'linear' }
});

const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const previewSection = document.getElementById('preview-section');
const previewImg = document.getElementById('preview-img');
const digitiseBtn = document.getElementById('digitise-btn');
const loading = document.getElementById('loading');
const resultSection = document.getElementById('result-section');
const mermaidOutput = document.getElementById('mermaid-output');
const mermaidCode = document.getElementById('mermaid-code');
const copyBtn = document.getElementById('copy-btn');

let selectedFile = null;

uploadArea.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => handleFile(e.target.files[0]));
uploadArea.addEventListener('dragover', (e) => e.preventDefault());
uploadArea.addEventListener('drop', (e) => {
  e.preventDefault();
  handleFile(e.dataTransfer.files[0]);
});

function handleFile(file) {
  if (!file) return;
  selectedFile = file;
  previewImg.src = URL.createObjectURL(file);
  previewSection.style.display = 'block';
  digitiseBtn.style.display = 'inline-block';
  resultSection.style.display = 'none';
}

async function renderMermaid(code) {
  try {
    mermaidOutput.innerHTML = '';
    mermaidOutput.removeAttribute('data-processed');
    mermaidOutput.textContent = code;
    await mermaid.run({ nodes: [mermaidOutput] });
  } catch (err) {
    // Mermaid failed to render — show a fallback message
    mermaidOutput.innerHTML = `
      <div style="padding:1rem;background:#fff8e1;border:1px solid #ffe082;border-radius:8px;font-size:0.85rem;color:#555">
        <strong>Could not render diagram visually.</strong><br>
        The Mermaid code was extracted successfully — copy it below and paste it into
        <a href="https://mermaid.live" target="_blank">mermaid.live</a> to view it.
      </div>`;
  }
}

digitiseBtn.addEventListener('click', async () => {
  if (!selectedFile) return;
  loading.style.display = 'block';
  resultSection.style.display = 'none';
  digitiseBtn.disabled = true;

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    const res = await fetch('/digitise', { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Something went wrong');

    mermaidCode.value = data.mermaid;
    await renderMermaid(data.mermaid);
    resultSection.style.display = 'block';
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    loading.style.display = 'none';
    digitiseBtn.disabled = false;
  }
});

copyBtn.addEventListener('click', () => {
  navigator.clipboard.writeText(mermaidCode.value);
  copyBtn.textContent = 'Copied!';
  setTimeout(() => copyBtn.textContent = 'Copy code', 2000);
});