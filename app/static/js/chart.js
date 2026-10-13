/* O histórico em tabela permanece disponível se a CDN não responder. */
const chartCanvas = document.getElementById("power-chart");
if (chartCanvas) {
  if (typeof Chart === "undefined") {
    chartCanvas.hidden = true;
    document.querySelector(".chart-fallback").hidden = false;
  } else {
    const history = JSON.parse(
      document.getElementById("power-data").textContent,
    );
    new Chart(chartCanvas, {
      type: "line",
      data: {
        labels: history.labels.map((day) => day.split("-").reverse().join("/")),
        datasets: [
          {
            label: "Potência (cv)",
            data: history.power,
            borderColor: "#f45136",
            backgroundColor: "#f4513612",
            fill: true,
            tension: 0.25,
            pointRadius: 4,
            pointBackgroundColor: "#f45136",
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: "#838592", font: { size: 10 } },
          },
          y: {
            grid: { color: "#2b2d35" },
            ticks: { color: "#838592", font: { size: 10 } },
            beginAtZero: true,
          },
        },
      },
    });
  }
}
