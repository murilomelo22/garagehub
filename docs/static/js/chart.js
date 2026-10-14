/* Leitura acessível da evolução sem biblioteca externa ou requisição adicional. */
(() => {
  const target = document.getElementById("power-chart"), selector = document.getElementById("chart-metric");
  if (!target || !selector) return;
  const f = window.GarageHub, e = f.escape;
  const metrics = { power: ["Potência", "cv"], torque: ["Torque", "Nm"], zero_to_hundred: ["0–100 km/h", "s"], consumption: ["Consumo", "km/l"] };
  let chartWidth=0;
  let history = JSON.parse(document.getElementById("power-data").textContent);
  function render() {
    const metric = selector.value, [label, unit] = metrics[metric];
    const points = (history[metric] || []).map((value,index) => ({value,index})).filter(p => p.value != null);
    const summary = document.getElementById("metric-change");
    if (points.length>1) {
      const first=points[0], last=points.at(-1), delta=last.value-first.value;
      const month=new Intl.DateTimeFormat("pt-BR",{month:"long",timeZone:"America/Sao_Paulo"}).format(new Date(history.labels[first.index]+"T12:00:00-03:00"));
      summary.textContent=`${delta>0?"+":""}${f.number(delta)} ${unit} desde ${month}`;
    } else summary.textContent=points.length?"Registre outra medição para comparar a evolução.":"Nenhuma medição disponível para esta métrica.";
    if (!points.length) { target.innerHTML='<p class="muted">A primeira medição dará início ao gráfico.</p>'; return; }
    const width=Math.max(280,target.clientWidth), height=width<400?220:260, left=55, right=42, top=22, bottom=54;
    chartWidth=target.clientWidth;target.style.aspectRatio=`${width} / ${height}`;
    const values=points.map(p=>p.value), lo=Math.min(...values), hi=Math.max(...values), pad=Math.max((hi-lo)*.25,Math.abs(hi)*.03,.05);
    const min=lo-pad, max=hi+pad, x=i=>left+(width-left-right)*(history.labels.length===1?.5:i/(history.labels.length-1));
    const y=v=>height-bottom-(v-min)/(max-min)*(height-top-bottom);
    const lines=Array.from({length:4},(_,i)=>{const v=min+(max-min)*i/3;return `<line x1="${left}" x2="${width-right}" y1="${y(v)}" y2="${y(v)}" stroke="#2b2d35"/><text x="${left-10}" y="${y(v)+4}" text-anchor="end">${e(f.number(v,1))}</text>`;}).join("");
    const labels=[...new Set([0,Math.floor((history.labels.length-1)/2),history.labels.length-1])].map(i=>`<text x="${x(i)}" y="${height-28}" text-anchor="middle">${e(f.date(history.labels[i]))}</text>`).join("");
    const path=points.map((p,i)=>`${i?'L':'M'}${x(p.index)},${y(p.value)}`).join(" ");
    target.innerHTML=`<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${e(label)} em ${unit}, de ${e(f.date(history.labels[0]))} a ${e(f.date(history.labels.at(-1)))}"><g fill="#b4bdcb" font-family="system-ui,sans-serif" font-size="12">${lines}${labels}<text x="${left}" y="14">${e(unit)}</text><text x="${width/2}" y="${height-5}" text-anchor="middle">Data da medição</text></g><path d="${path} L${x(points.at(-1).index)},${height-bottom} L${x(points[0].index)},${height-bottom}Z" fill="#244f912a"/><path d="${path}" fill="none" stroke="#92baf0" stroke-width="3"/>${points.map(p=>`<circle cx="${x(p.index)}" cy="${y(p.value)}" r="5" fill="#92baf0"/>`).join("")}</svg><div class="chart-points">${points.map(p=>`<button type="button" class="chart-point" style="left:${x(p.index)/width*100}%;top:${y(p.value)/height*100}%" aria-label="${e(f.date(history.labels[p.index]))}: ${e(f.number(p.value))} ${unit}" data-chart-tip="${e(f.date(history.labels[p.index]))} · ${e(f.number(p.value))} ${unit}"></button>`).join("")}</div><output class="chart-tooltip" hidden></output>`;
    const tip=target.querySelector(".chart-tooltip");
    target.querySelectorAll(".chart-point").forEach(button=>{
      const show=()=>{tip.textContent=button.dataset.chartTip;tip.hidden=false;};
      button.addEventListener("pointerenter",show);button.addEventListener("focus",show);button.addEventListener("click",show);
      button.addEventListener("pointerleave",()=>{if(document.activeElement!==button)tip.hidden=true;});
      button.addEventListener("blur",()=>{tip.hidden=true;});
      button.addEventListener("keydown",event=>{if(event.key==="Escape")tip.hidden=true;});
    });
    target.dataset.ready="true";target.dataset.metric=metric;
  }
  selector.addEventListener("change",render);
  window.GarageCharts={refresh:data=>{history=data;render();}};render();
  new ResizeObserver(()=>{if(Math.abs(target.clientWidth-chartWidth)>1)render();}).observe(target);
})();
