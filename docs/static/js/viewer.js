/* Carro conceitual: todas as peças são geometrias primitivas do Three.js. */
const container = document.getElementById("car-viewer");
const form = document.getElementById("viewer-form");
const message = document.getElementById("viewer-message");
const feedback = document.getElementById("viewer-feedback");
const initial = JSON.parse(
  document.getElementById("viewer-config").textContent,
);

// O salvamento também funciona quando WebGL não está disponível.
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = document.getElementById("save-viewer");
  button.disabled = true;
  feedback.textContent = "Salvando…";
  try {
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

try {
  const THREE = await import("three");
  const { OrbitControls } = await import(
    "three/addons/controls/OrbitControls.js"
  );
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#121318");
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
  camera.position.set(7.5, 4.6, 7.5);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
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
  const accent = new THREE.PointLight(0xff5a3d, 38);
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
  box(body, [4.8, 0.65, 2.05], [0, 0, 0], paint);
  box(body, [4.55, 0.17, 2.1], [0, -0.31, 0], dark);
  box(body, [2.15, 0.74, 1.7], [-0.25, 0.63, 0], glass);
  box(body, [2.18, 0.1, 1.72], [-0.25, 1.04, 0], paint);
  box(body, [0.1, 0.73, 1.75], [-0.3, 0.63, 0], paint);
  box(body, [1.35, 0.12, 1.94], [1.5, 0.39, 0], paint);
  box(body, [0.1, 0.16, 0.55], [2.43, 0.12, -0.62], lamps);
  box(body, [0.1, 0.16, 0.55], [2.43, 0.12, 0.62], lamps);
  box(body, [0.1, 0.17, 0.6], [-2.43, 0.12, -0.61], rearLamps);
  box(body, [0.1, 0.17, 0.6], [-2.43, 0.12, 0.61], rearLamps);
  box(body, [0.06, 0.2, 0.85], [2.45, -0.16, 0], dark);
  for (const side of [-1, 1]) {
    box(body, [0.32, 0.16, 0.18], [0.54, 0.57, side * 1.05], paint);
    box(body, [0.15, 0.055, 0.05], [-0.06, 0.14, side * 1.05], rims);
  }
  const spoiler = new THREE.Group();
  body.add(spoiler);
  box(spoiler, [0.35, 0.12, 2.25], [-2, 0.78, 0], paint);
  for (const side of [-1, 1])
    box(spoiler, [0.12, 0.4, 0.1], [-2, 0.52, side * 0.7], dark);
  const wheels = [];
  for (const x of [-1.52, 1.52])
    for (const side of [-1, 1]) {
      const wheel = new THREE.Group();
      wheel.position.set(x, 0.52, side * 1.05);
      scene.add(wheel);
      const tire = new THREE.Mesh(
        new THREE.CylinderGeometry(0.52, 0.52, 0.28, 40),
        rubber,
      );
      tire.rotation.x = Math.PI / 2;
      tire.castShadow = true;
      wheel.add(tire);
      const rim = new THREE.Mesh(
        new THREE.CylinderGeometry(0.37, 0.37, 0.295, 32),
        rims,
      );
      rim.rotation.x = Math.PI / 2;
      wheel.add(rim);
      for (let i = 0; i < 5; i++) {
        const spoke = box(
          wheel,
          [0.06, 0.66, 0.035],
          [0, 0, side * 0.16],
          rims,
        );
        spoke.rotation.z = (i * Math.PI) / 5;
      }
      const hub = new THREE.Mesh(
        new THREE.CylinderGeometry(0.09, 0.09, 0.33, 16),
        rims,
      );
      hub.rotation.x = Math.PI / 2;
      wheel.add(hub);
      wheels.push(wheel);
    }
  const stage = new THREE.Mesh(
    new THREE.CylinderGeometry(4, 4, 0.12, 96),
    new THREE.MeshStandardMaterial({ color: 0x22232a, roughness: 0.7 }),
  );
  stage.position.y = -0.07;
  stage.receiveShadow = true;
  scene.add(stage);
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(3.95, 0.017, 8, 96),
    new THREE.MeshBasicMaterial({ color: 0x713629 }),
  );
  ring.rotation.x = Math.PI / 2;
  ring.position.y = 0.002;
  scene.add(ring);

  function update() {
    paint.color.set(form.elements.paint_color.value);
    rims.color.set(form.elements.wheel_color.value);
    const size = Number(form.elements.wheel_size.value);
    document.getElementById("wheel-size-value").value = size.toFixed(2) + "×";
    wheels.forEach((wheel) => {
      wheel.scale.setScalar(size);
      wheel.position.y = 0.52 * size;
    });
    body.position.y =
      0.52 * size +
      (form.elements.suspension.value === "lowered" ? 0.25 : 0.48);
    spoiler.visible = form.elements.spoiler.value === "yes";
  }
  form.addEventListener("input", update);
  update();
  const resize = new ResizeObserver(() => {
    const { width, height } = container.getBoundingClientRect();
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  });
  resize.observe(container);
  let visible = true;
  new IntersectionObserver((entries) => {
    visible = entries[0].isIntersecting;
  }).observe(container);
  renderer.setAnimationLoop(() => {
    if (visible && !document.hidden) {
      controls.update();
      renderer.render(scene, camera);
    }
  });
  renderer.domElement.addEventListener("webglcontextlost", (event) => {
    event.preventDefault();
    message.hidden = false;
    message.textContent =
      "O contexto 3D foi interrompido. Atualize a página para tentar novamente.";
  });
  message.hidden = true;
  container.dataset.ready = "true";
} catch (error) {
  message.textContent =
    "O 3D precisa de WebGL e acesso à CDN. As opções continuam disponíveis para salvar.";
  container.dataset.ready = "false";
  console.warn("Garage Studio indisponível:", error.message);
}
