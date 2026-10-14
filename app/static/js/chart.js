/* Uma única instância acompanha a métrica selecionada e os dados atualizados. */
(() => {
  const canvas = document.getElementById("power-chart");
  const selector = document.getElementById("chart-metric");
  if (!selector) return;
  const format = window.GarageHub;
  const metrics = { power: ["Potência", "cv"], torque: ["Torque", "Nm"], zero_to_hundred: ["0–100 km/h", "s"], consumption: ["Consumo", "km/l"] };
  let history = JSON.parse(document.getElementById("power-data").textContent), chart;
  function render() {
    const metric = selector.value, [label, unit] = metrics[metric];
    const values = history[metric] || [];
    const valid = values.map((value, index) => ({ value, index })).filter(item => item.value != null);
    const summary = document.getElementById("metric-change");
    if (valid.length > 1) {
      const first = valid[0], last = valid.at(-1), delta = last.value - first.value;
      const month = new Intl.DateTimeFormat("pt-BR", { month: "long", timeZone: "America/Sao_Paulo" }).format(new Date(history.labels[first.index] + "T12:00:00-03:00"));
      summary.textContent = `${delta > 0 ? "+" : ""}${format.number(delta)} ${unit} desde ${month}`;
    } else summary.textContent = valid.length ? "Registre outra medição para comparar a evolução." : "Nenhuma medição disponível para esta métrica.";
    if (!canvas) return;
    canvas.setAttribute("aria-label", `Gráfico de evolução: ${label} (${unit}). Histórico em tabela abaixo.`);
    if (typeof Chart === "undefined") {
      canvas.hidden = true;
      document.querySelector(".chart-fallback").hidden = false;
      return;
    }
    const data = { labels: history.labels.map(format.date), datasets: [{ label: `${label} (${unit})`, data: values, borderColor: "#92baf0", backgroundColor: "#244f912a", fill: true, tension: .2, pointRadius: 4, pointBackgroundColor: "#92baf0", borderWidth: 2, spanGaps: false }] };
    if (chart) { chart.data = data; chart.update(); return; }
    chart = new Chart(canvas, { type: "line", data, options: {
      responsive: true, maintainAspectRatio: false, locale: "pt-BR",
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: context => `${metrics[selector.value][0]}: ${format.number(context.parsed.y)} ${metrics[selector.value][1]}` } } },
      scales: { x: { title: { display: true, text: "Data da medição", color: "#a6acb8" }, grid: { display: false }, ticks: { color: "#a6acb8", font: { size: 10 } } }, y: { grid: { color: "#2b2d35" }, ticks: { color: "#a6acb8", callback: format.number } } }
    } });
  }
  selector.addEventListener("change", render);
  window.GarageCharts = { refresh: data => { history = data; render(); } };
  render();
})();
