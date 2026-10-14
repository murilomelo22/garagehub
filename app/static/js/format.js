/* Datas usam Brasília; valores numéricos seguem a apresentação pt-BR. */
window.GarageHub = (() => {
  const number = value => value == null ? "—" : new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(value);
  const money = value => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
  const date = value => new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo" }).format(new Date(value.length === 10 ? value + "T12:00:00-03:00" : value));
  const day = value => new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(value));
  const relative = value => {
    const timestamp = new Date(value), now = new Date();
    const seconds = Math.max(0, (now - timestamp) / 1000);
    if (seconds < 60) return "agora";
    if (seconds < 3600) return `há ${Math.floor(seconds / 60)} min`;
    if (day(now) === day(timestamp)) return `há ${Math.floor(seconds / 3600)} h`;
    if (day(new Date(now.getTime() - 86400000)) === day(timestamp)) return "ontem";
    return date(value);
  };
  const escape = value => String(value ?? "").replace(/[&<>"']/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
  function refreshTimes() {
    document.querySelectorAll("time[data-relative-time]").forEach(element => {
      element.textContent = relative(element.dateTime);
      element.title = new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", dateStyle: "short", timeStyle: "short" }).format(new Date(element.dateTime)) + " · Brasília";
      element.setAttribute("aria-label", element.textContent + ". " + element.title);
    });
  }
  document.addEventListener("DOMContentLoaded", refreshTimes);
  setInterval(refreshTimes, 60000);
  return { number, money, date, day, relative, escape, refreshTimes };
})();
