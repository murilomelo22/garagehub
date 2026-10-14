/* Modelo conceitual: perfil extrudado com para-lamas abertos e rodas no eixo lateral. */
(async () => {
if (!document.getElementById("viewer-form")) return;
const container = document.getElementById("car-viewer");
const form = document.getElementById("viewer-form");
const message = document.getElementById("viewer-message");
const feedback = document.getElementById("viewer-feedback");
let initial = JSON.parse(
  document.getElementById("viewer-config").textContent,
);
const defaults = JSON.parse(document.getElementById("viewer-defaults").textContent);
const homeLocal = document.body.dataset.homeDemo === "true" && document.body.dataset.mode !== "preview";
if (homeLocal) {
  try {const saved=JSON.parse(localStorage.getItem("garagehub:studio-home:v0.2"));if(saved && /^#[\da-f]{6}$/i.test(saved.paint_color) && Number.isFinite(saved.wheel_size) && saved.wheel_size>=.8 && saved.wheel_size<=1.3) initial={...initial,...saved};} catch { /* Mantém os controles padrão se o armazenamento estiver indisponível. */ }
  for (const [name,value] of Object.entries(initial)) form.elements[name].value=name==="spoiler"?(value?"yes":"no"):value;
}
const wheelCaption=()=>{document.getElementById("wheel-size-value").value=window.GarageHub.number(Number(form.elements.wheel_size.value))+"×";};
form.addEventListener("input",wheelCaption);wheelCaption();
document.getElementById("reset-viewer")?.addEventListener("click", () => {
  for (const [name, value] of Object.entries(defaults)) {
    form.elements[name].value = name === "spoiler" ? (value ? "yes" : "no") : value;
  }
  form.dispatchEvent(new Event("input", { bubbles: true }));
  feedback.textContent = "Controles redefinidos. Salve para manter esta configuração.";
});

// O salvamento também funciona quando WebGL não está disponível.
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = document.getElementById("save-viewer");
  button.disabled = true;
  feedback.textContent = "Salvando…";
  try {
    if (document.body.dataset.mode === "preview" || homeLocal) {
      const config = Object.fromEntries(new FormData(form));
      config.wheel_size = Number(config.wheel_size);
      config.spoiler = config.spoiler === "yes";
      if (homeLocal) localStorage.setItem("garagehub:studio-home:v0.2",JSON.stringify(config));
      else window.GaragePreview.saveViewer(config);
      feedback.textContent = "Configuração salva somente neste navegador.";
      return;
    }
    const response = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { Accept: "application/json" },
    });
    if (!response.headers.get("content-type")?.includes("application/json"))
      throw new Error(
        "Sua sessão expirou. Atualize a página e tente novamente.",
      );
    const result = await response.json();
    if (!response.ok) throw new Error(result.message);
    feedback.textContent = result.message;
  } catch (error) {
    feedback.textContent =
      error.message || "Não foi possível salvar. Tente novamente.";
  } finally {
    button.disabled = false;
  }
});

// O motor 3D só é baixado ao ativar o modelo ou experimentar um controle.
await new Promise(resolve=>{
  const activate=()=>{message.textContent="Preparando o modelo 3D…";resolve();};
  document.getElementById("activate-viewer").addEventListener("click",activate,{once:true});
  form.addEventListener("input",activate,{once:true});
  document.getElementById("activate-viewer").disabled=false;
});
try {
  const THREE = await import("three");
  const { OrbitControls } = await import(
    "three/addons/controls/OrbitControls.js"
  );
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#121318");
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
  camera.position.set(6.5, 3.4, 6.7);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.domElement.setAttribute("role","img");renderer.domElement.setAttribute("aria-label","Carro conceitual 3D. Use os botões de giro e aproximação ou arraste para explorar.");
  container.prepend(renderer.domElement);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.minDistance = 5;
  controls.maxDistance = 17;
  controls.maxPolarAngle = Math.PI / 2.12;
  controls.target.set(0, 0.9, 0);
  controls.enablePan = false;
  scene.add(new THREE.HemisphereLight(0xcbd8ff, 0x39313b, 2.8));
  const light = new THREE.DirectionalLight(0xffffff, 4.2);
  light.position.set(4, 8, 5);
  light.castShadow = true;
  light.shadow.mapSize.set(1024, 1024);
  scene.add(light);
  const accent = new THREE.PointLight(0x517dbd, 38);
  accent.position.set(-4, 2.8, -3);
  scene.add(accent);

  const paint = new THREE.MeshStandardMaterial({
    color: initial.paint_color,
    metalness: 0.65,
    roughness: 0.32,
  });
  const rims = new THREE.MeshStandardMaterial({
    color: initial.wheel_color,
    metalness: 0.85,
    roughness: 0.27,
  });
  const rubber = new THREE.MeshStandardMaterial({
    color: 0x0c0d10,
    roughness: 0.85,
  });
  const glass = new THREE.MeshStandardMaterial({
    color: 0x243243,
    metalness: 0.55,
    roughness: 0.15,
  });
  const dark = new THREE.MeshStandardMaterial({
    color: 0x171920,
    roughness: 0.5,
  });
  const lamps = new THREE.MeshStandardMaterial({
    color: 0xffe5b7,
    emissive: 0xffcc88,
    emissiveIntensity: 0.6,
  });
  const rearLamps = new THREE.MeshStandardMaterial({
    color: 0xb52922,
    emissive: 0xff2922,
    emissiveIntensity: 0.5,
  });
  const body = new THREE.Group();
  scene.add(body);
  function box(parent, size, position, material) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
    mesh.position.set(...position);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    parent.add(mesh);
    return mesh;
  }
  // Perfil lateral: 4,4 m de comprimento, 2,7 m entre eixos e arcos de 0,46 m.
  const silhouette = new THREE.Shape();
  silhouette.moveTo(-2.2,.16);silhouette.lineTo(-2.2,.55);silhouette.lineTo(-1.92,.68);
  silhouette.lineTo(-1.18,.73);silhouette.lineTo(.65,.73);silhouette.lineTo(1.9,.62);silhouette.lineTo(2.2,.48);silhouette.lineTo(2.2,.16);
  silhouette.lineTo(1.81,.10);
  silhouette.absarc(1.35,.10,.46,0,Math.PI,false);
  silhouette.lineTo(-.89,.10);silhouette.absarc(-1.35,.10,.46,0,Math.PI,false);
  silhouette.lineTo(-2.2,.16);
  const shellGeometry=new THREE.ExtrudeGeometry(silhouette,{depth:1.82,bevelEnabled:false,curveSegments:32});
  shellGeometry.translate(0,0,-.91);
  const shell=new THREE.Mesh(shellGeometry,paint);shell.castShadow=true;shell.receiveShadow=true;body.add(shell);
  // Cabine afunilada: vidros acompanham as linhas do teto e do capô.
  const cabin=new THREE.Shape();cabin.moveTo(-1.17,.75);cabin.lineTo(-.70,1.18);cabin.quadraticCurveTo(-.57,1.25,-.38,1.25);cabin.lineTo(.22,1.25);cabin.lineTo(.89,.75);cabin.closePath();
  const cabinGeometry=new THREE.ExtrudeGeometry(cabin,{depth:1.48,bevelEnabled:false,curveSegments:16});cabinGeometry.translate(0,0,-.74);
  const canopy=new THREE.Mesh(cabinGeometry,glass);canopy.castShadow=true;body.add(canopy);
  box(body,[.66,.055,1.5],[-.10,1.25,0],paint);
  for (const side of [-1,1]) {
    const pillar=box(body,[.06,.47,.035],[-.12,.98,side*.757],paint);
    pillar.rotation.z=-.06;
    box(body,[.26,.10,.18],[.74,.83,side*.96],paint);
    box(body,[.13,.03,.025],[.04,.62,side*.927],rims);
    box(body,[1.24,.07,.07],[0,.12,side*.90],dark);
    box(body,[.07,.13,.38],[2.19,.47,side*.55],lamps);
    box(body,[.065,.13,.42],[-2.20,.49,side*.55],rearLamps);
  }
  box(body,[.05,.13,.65],[2.21,.26,0],dark);
  const spoiler=new THREE.Group();body.add(spoiler);
  box(spoiler,[.28,.075,1.98],[-1.91,.95,0],paint);
  for(const side of [-1,1]) box(spoiler,[.065,.25,.065],[-1.91,.80,side*.65],dark);
  const wheels=[],rimFaces=[];
  for(const x of [-1.35,1.35]) for(const side of [-1,1]) {
    const wheel=new THREE.Group();wheel.position.set(x,.37,side*.90);scene.add(wheel);
    const tire=new THREE.Mesh(new THREE.CylinderGeometry(.37,.37,.24,48),rubber);
    tire.rotation.x=Math.PI/2;tire.castShadow=true;wheel.add(tire);
    // Cilindro girado para z: sua face externa é perpendicular ao eixo lateral.
    const face=new THREE.Group();face.position.z=side*.125;wheel.add(face);
    const rim=new THREE.Mesh(new THREE.CylinderGeometry(.26,.26,.025,40),rims);rim.rotation.x=Math.PI/2;face.add(rim);
    const inset=new THREE.Mesh(new THREE.CylinderGeometry(.21,.21,.027,40),dark);inset.rotation.x=Math.PI/2;inset.position.z=side*.003;face.add(inset);
    for(let i=0;i<5;i++) {
      const angle=i*Math.PI*2/5;
      const spoke=box(face,[.045,.20,.018],[Math.sin(angle)*.11,Math.cos(angle)*.11,side*.022],rims);spoke.rotation.z=-angle;
    }
    const hub=new THREE.Mesh(new THREE.CylinderGeometry(.056,.056,.05,24),rims);hub.rotation.x=Math.PI/2;hub.position.z=side*.02;face.add(hub);
    wheels.push(wheel);rimFaces.push(face);
  }
  const stage = new THREE.Mesh(
    new THREE.CylinderGeometry(3.1, 3.1, 0.12, 64),
    new THREE.MeshStandardMaterial({ color: 0x22232a, roughness: 0.7 }),
  );
  stage.position.y = -0.07;
  stage.receiveShadow = true;
  scene.add(stage);
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(3.06, 0.017, 8, 64),
    new THREE.MeshBasicMaterial({ color: 0x244f91 }),
  );
  ring.rotation.x = Math.PI / 2;
  ring.position.y = 0.002;
  scene.add(ring);

  function update() {
    paint.color.set(form.elements.paint_color.value);
    rims.color.set(form.elements.wheel_color.value);
    const size = Number(form.elements.wheel_size.value);
    document.getElementById("wheel-size-value").value = window.GarageHub.number(size) + "×";
    const tireScale=1+(size-1)*.25;
    wheels.forEach(wheel=>{wheel.scale.setScalar(tireScale);wheel.position.y=.37*tireScale;});
    rimFaces.forEach(face=>{face.scale.x=size;face.scale.y=size;});
    body.position.y=.37*tireScale-.10+(form.elements.suspension.value==="lowered"?0:.08);
    spoiler.visible = form.elements.spoiler.value === "yes";
  }
  form.addEventListener("input", update);
  update();
  const capture = document.getElementById("capture-viewer");
  capture.disabled = false;
  capture.addEventListener("click", () => {
    renderer.render(scene, camera);
    renderer.domElement.toBlob(blob => {
      if (!blob) { feedback.textContent = "Não foi possível gerar a imagem. Tente novamente."; return; }
      const link = document.createElement("a"), url = URL.createObjectURL(blob);
      link.href = url;
      link.download = "garagehub-modelo-conceitual.png";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      feedback.textContent = "Imagem PNG exportada: modelo conceitual, sem marcas reais.";
    }, "image/png");
  });
  const resize = new ResizeObserver(() => {
    const { width, height } = container.getBoundingClientRect();
    camera.aspect = width / height;
    // Ajusta a distância à proporção do contêiner, com margem em todas as larguras.
    const verticalFov=camera.fov*Math.PI/180,horizontalFov=2*Math.atan(Math.tan(verticalFov/2)*camera.aspect);
    const distance=Math.max(6.3,3.05/Math.sin(Math.min(verticalFov,horizontalFov)/2));
    const direction=new THREE.Vector3().subVectors(camera.position,controls.target).normalize();
    camera.position.copy(controls.target).addScaledVector(direction,distance);
    controls.minDistance=distance*.85;controls.maxDistance=distance*1.8;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  });
  resize.observe(container);
  let visible = true;
  new IntersectionObserver((entries) => {
    visible = entries[0].isIntersecting;
  }).observe(container);
  let lastFrame=0;
  renderer.setAnimationLoop(now => {
    if (visible && !document.hidden && now-lastFrame>32) {
      lastFrame=now;
      controls.update();
      renderer.render(scene, camera);
    }
  });
  renderer.domElement.addEventListener("webglcontextlost", (event) => {
    event.preventDefault();
    message.hidden = false;
    message.textContent =
      "O 3D foi interrompido. Atualize a página para tentar novamente.";
  });
  document.querySelector(".viewer-tools").hidden=false;
  document.querySelectorAll("[data-view-control]").forEach(button=>button.addEventListener("click",()=>{
    const vector=camera.position.clone().sub(controls.target),action=button.dataset.viewControl;
    if(action==="left"||action==="right")vector.applyAxisAngle(new THREE.Vector3(0,1,0),action==="left"?-.18:.18);
    else vector.multiplyScalar(action==="zoom-in"?.92:1.08);
    vector.clampLength(controls.minDistance,controls.maxDistance);camera.position.copy(controls.target).add(vector);controls.update();
  }));
  message.hidden = true;
  container.dataset.ready = "true";
} catch (error) {
  message.textContent =
    "O visualizador não está disponível neste navegador. As opções continuam disponíveis para salvar.";
  container.dataset.ready = "false";
  console.warn("Garage Studio indisponível:", error.message);
}

})();
