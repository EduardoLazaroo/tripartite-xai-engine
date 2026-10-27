/**
 * Logica da interface web de visualizacao de resultados.
 * 
 * Este arquivo gerencia:
 * - Carregamento do relatorio (report_manifest.json)
 * - Renderizacao do resumo geral (cards de metricas)
 * - Preenchimento do seletor de imagens
 * - Renderizacao de metricas por imagem (tabela)
 * - Renderizacao de graficos (Chart.js)
 * - Renderizacao da galeria de imagens e Grad-CAMs
 */

// Referencias aos elementos DOM
const summaryCards = document.getElementById('summary-cards');
const imageSelect = document.getElementById('image-select');
const metricsTable = document.getElementById('metrics-table');
const imageGallery = document.getElementById('image-gallery');
const confidenceChartEl = document.getElementById('confidence-chart');
const gradcamChartEl = document.getElementById('gradcam-chart');

// Estado global
let reportData = null;
let confidenceChart = null;
let gradcamChart = null;

/**
 * Carrega o relatorio do disco e inicializa a interface.
 */
async function loadReport() {
  const response = await fetch('report_manifest.json');
  reportData = await response.json();
  renderSummary(reportData);
  populateImageSelect(reportData);
  renderImage(reportData, 0);
}

/**
 * Formata numero com casas decimais.
 */
function formatNumber(value, digits = 2) {
  return value.toFixed(digits);
}

/**
 * Renderiza cards de resumo do experimento.
 */
function renderSummary(report) {
  summaryCards.innerHTML = '';
  const cards = [
    { label: 'Imagens', value: report.benchmark.num_images },
    { label: 'Variantes', value: report.benchmark.num_variants },
    { label: 'Storage (MB)', value: formatNumber(report.benchmark.storage_mb_delta) },
    { label: 'Tempo media recuperacao (ms)', value: formatNumber(report.benchmark.avg_retrieval_ms) },
  ];
  cards.forEach(card => {
    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `<strong>${card.value}</strong><p>${card.label}</p>`;
    summaryCards.appendChild(div);
  });
}

/**
 * Preenche o dropdown de selecao de imagens.
 */
function populateImageSelect(report) {
  imageSelect.innerHTML = '';
  report.results.forEach((result, index) => {
    const option = document.createElement('option');
    option.value = index;
    option.textContent = result.image;
    imageSelect.appendChild(option);
  });
  imageSelect.addEventListener('change', () => renderImage(report, Number(imageSelect.value)));
}

/**
 * Renderiza todas as informacoes da imagem selecionada.
 */
function renderImage(report, index) {
  const result = report.results[index];
  renderMetricsTable(result);
  renderChart(result);
  renderGallery(result);
}

/**
 * Renderiza tabela de metricas da imagem.
 */
function renderMetricsTable(result) {
  const html = [`<table>`, `<thead><tr><th>Campo</th><th>Valor</th></tr></thead>`, `<tbody>`];
  html.push(`<tr><td>Imagem</td><td>${result.image}</td></tr>`);
  html.push(`<tr><td>Label baseline</td><td>${result.baseline_label}</td></tr>`);
  html.push(`<tr><td>Confianca baseline</td><td>${formatNumber(result.baseline_confidence, 4)}</td></tr>`);
  html.push(`<tr><td>Persistencia (ms)</td><td>${result.timing_ms.persistence}</td></tr>`);
  html.push(`<tr><td>Recuperacao (ms)</td><td>${result.timing_ms.retrieval}</td></tr>`);
  html.push(`</tbody></table>`);
  metricsTable.innerHTML = html.join('');
}

/**
 * Renderiza graficos de delta de confianca e overlap Grad-CAM.
 */
function renderChart(result) {
  const labels = result.comparisons.map(c => c.noise_type);
  const confidenceDelta = result.comparisons.map(c => c.confidence_delta);
  const gradcamOverlap = result.comparisons.map(c => c.gradcam_overlap);

  // Grafico de delta de confianca
  if (confidenceChart) {
    confidenceChart.destroy();
  }
  confidenceChart = new Chart(confidenceChartEl, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Delta de confianca', data: confidenceDelta, backgroundColor: '#3b82f6' },
      ],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });

  // Grafico de overlap Grad-CAM
  if (gradcamChart) {
    gradcamChart.destroy();
  }
  gradcamChart = new Chart(gradcamChartEl, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Overlap Grad-CAM', data: gradcamOverlap, backgroundColor: '#f59e0b' },
      ],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

/**
 * Renderiza galeria de imagens e Grad-CAMs.
 */
function renderGallery(result) {
  imageGallery.innerHTML = '';
  const cards = [
    { title: 'Baseline', uri: result.baseline_image_local },
    { title: 'Baseline Grad-CAM', uri: result.baseline_gradcam_local },
  ];
  result.variants.forEach(variant => {
    cards.push({ title: `${variant.noise_type} imagem`, uri: variant.image_local });
    cards.push({ title: `${variant.noise_type} Grad-CAM`, uri: variant.gradcam_local });
  });

  cards.forEach(card => {
    const div = document.createElement('div');
    div.className = 'image-card';
    div.innerHTML = `
      <img src="./assets/${card.uri}" alt="${card.title}" />
      <div class="caption"><strong>${card.title}</strong></div>
    `;
    imageGallery.appendChild(div);
  });
}

// Inicializacao: carrega o relatorio ao abrir a pagina
loadReport().catch(error => {
  console.error('Erro ao carregar relatorio:', error);
  document.body.insertAdjacentHTML('beforeend', `<p style="color:red;">Erro ao carregar relatorio: ${error.message}</p>`);
});
