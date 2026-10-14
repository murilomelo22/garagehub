/* Aguarda a prévia antes de inicializar controles com o estado salvo. */
(() => {
  const loader=document.currentScript;
  (async()=>{
    await window.GaragePreviewReady;
    if (!document.getElementById("viewer-form")) return;
    await import(new URL(loader.dataset.chartSrc,document.baseURI).href);
    await import(new URL(loader.dataset.viewerSrc,document.baseURI).href);
  })().catch(()=>{document.getElementById("viewer-feedback").textContent="Não foi possível preparar o estúdio. Atualize a página para tentar novamente.";});
})();
