/* A prévia usa somente dados fictícios e alterações locais, sem enviar fotos ou textos. */
window.GaragePreviewReady = (async () => {
  if (document.body.dataset.mode !== "preview") return;
  const response = await fetch(document.querySelector('meta[name="demo-data-url"]').content);
  if (!response.ok) throw new Error("Não foi possível carregar a demonstração.");
  const seed = await response.json();
  const storageKey = "garagehub:preview:v0.2";
  const f = window.GarageHub, e = f.escape;
  const clone = value => structuredClone(value);
  const normalize = value => String(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const fresh = () => {
    const value = clone(seed), shift = Date.now() - Date.parse(seed.exportedAt);
    value.posts.forEach(post => {
      post.createdAt = new Date(Date.parse(post.createdAt) + shift).toISOString();
      post.comments.forEach(comment => { comment.createdAt = new Date(Date.parse(comment.createdAt) + shift).toISOString(); });
    });
    value.visitor = false;
    return value;
  };
  let state;
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey));
    state = saved?.version === 2 && Array.isArray(saved.cars) && Array.isArray(saved.posts) && Array.isArray(saved.users) && Array.isArray(saved.following) ? saved : fresh();
  } catch { state = fresh(); }
  // A atualização incorpora a comunidade nova sem perder projetos e publicações locais da V0.1.
  if (!localStorage.getItem(storageKey)) {
    try {
      const previous = JSON.parse(localStorage.getItem("garagehub:preview:v0.1"));
      if (previous?.version===1 && Array.isArray(previous.cars) && Array.isArray(previous.posts) && Array.isArray(previous.users)) {
        state.cars=[...previous.cars,...state.cars.filter(car=>Number(car.id)>9)];
        state.posts=[...previous.posts,...state.posts.filter(post=>Number(post.id)>6)];
        state.users=state.users.map(owner=>{const old=previous.users.find(u=>u.id===owner.id);return old?{...owner,city:old.city,bio:old.bio}:owner;});
        state.following=previous.following;state.friendships=previous.friendships;state.visitor=previous.visitor;
        localStorage.setItem(storageKey,JSON.stringify(state));
      }
    } catch { /* Sem armazenamento, os links e o conteúdo renderizado continuam disponíveis. */ }
  }
  const user = () => state.users.find(item => item.id === state.demoUserId);
  const getCar = id => state.cars.find(item => String(item.id) === String(id));
  // O exemplo público da home sobrevive à exclusão de carros na garagem do visitante.
  const currentCar = () => {
    if (document.body.dataset.homeDemo === "true") {
      const example=seed.cars.find(car=>car.id===1);
      return {...example,viewerConfig:state.homeViewerConfig||getCar(example.id)?.viewerConfig||example.viewerConfig};
    }
    return getCar(document.body.dataset.carId);
  };
  const uid = () => "local-" + crypto.randomUUID();
  const profileUrl = owner => `perfil-${encodeURIComponent(owner.username)}.html`;
  const carUrl = car => String(car.id).startsWith("local-") ? `carro.html?id=${encodeURIComponent(car.id)}` : `carro-${car.id}.html`;
  const safeImage = value => /^(?:uploads\/|static\/img\/|data:image\/(?:jpeg|png|webp);base64,)/.test(value || "") ? value : "static/img/car.svg";
  let toastTimer, trigger;
  function toast(message) {
    let element = document.querySelector(".local-toast");
    if (!element) { element = document.createElement("div"); element.className = "local-toast"; element.setAttribute("role", "status"); document.body.append(element); }
    element.textContent = message; element.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(() => { element.hidden = true; }, 6000);
  }
  function commit(change) {
    // Grava primeiro; uma falha de quota não deixa a interface fingir que salvou.
    const draft = clone(state); change(draft);
    try { localStorage.setItem(storageKey, JSON.stringify(draft)); }
    catch { throw new Error("O navegador não conseguiu salvar. Libere espaço ou permita o armazenamento local e tente novamente."); }
    state = draft;
  }
  const avatar = owner => `<span class="avatar">${e(owner.username.slice(0, 2).toUpperCase())}</span>`;
  const account = owner => `<a class="account" href="${profileUrl(owner)}">${avatar(owner)}<span><strong>${e(owner.username)}</strong><small>${e(owner.city)}</small></span></a>`;
  const time = timestamp => `<time datetime="${e(timestamp)}" data-relative-time>${e(f.relative(timestamp))}</time>`;
  const history = car => {
    const stats = [...car.stats].sort((a, b) => a.date.localeCompare(b.date) || String(a.id).localeCompare(String(b.id)));
    const value = { labels: stats.map(item => item.date) };
    ["power", "torque", "zero_to_hundred", "top_speed", "consumption"].forEach(metric => { value[metric] = stats.map(item => item[metric] ?? null); });
    return value;
  };
  const carCard = car => {
    const stats = [...car.stats].sort((a, b) => a.date.localeCompare(b.date)).at(-1);
    return `<a class="car-card panel" href="${carUrl(car)}"><div class="car-cover"><img src="${e(safeImage(car.photo))}" alt="${e(car.brand + " " + car.model)}" loading="lazy"><span class="tag">${e(car.year)}</span></div><div class="car-info"><span class="eyebrow">${e(car.brand)}</span><h3>${e(car.model)}</h3><p>${e(car.engine || "Motor não informado")} · ${e(car.transmission || "Câmbio não informado")}</p><div class="car-footer"><span>${stats ? f.number(stats.power) + " cv" : "Novo projeto"}</span><span class="orange">Ver projeto →</span></div></div></a>`;
  };
  function renderGarages() {
    const suggestions = document.querySelector(".suggestions");
    if (suggestions) {
      const owners = state.users.filter(owner => owner.id !== user().id && !state.following.includes(owner.id));
      suggestions.innerHTML = '<h3>Conexões na pista</h3><p class="muted">Conheça outras garagens.</p>' + (owners.slice(0,3).map(owner => `<div class="suggestion">${account(owner)}<button class="icon-button orange" data-follow="${owner.id}" aria-label="Seguir ${e(owner.username)}">＋</button></div>`).join("") || '<p class="muted">Você já acompanha todos por aqui.</p>') + '<a class="aside-link" href="amigos.html">Explorar comunidade →</a>';
    }
    document.querySelectorAll(".car-grid[data-owner-id]").forEach(grid => {
      const cars = state.cars.filter(car => String(car.userId) === grid.dataset.ownerId);
      grid.innerHTML = cars.length ? cars.map(carCard).join("") : '<section class="panel empty-state"><h2>Um projeto está a caminho.</h2><p>Adicione um veículo para começar.</p><button class="btn btn-primary" data-preview-open="car">Adicionar veículo</button></section>';
      const count = document.querySelector(".page-heading .count-badge");
      if (count) count.textContent = cars.length;
      const caption = document.querySelector(".section-heading > .muted");
      if (caption) caption.textContent = `${cars.length} veículos na garagem`;
    });
    const counts = document.querySelectorAll(".mini-stats strong");
    if (counts.length) { counts[0].textContent = state.cars.filter(car => car.userId === user().id).length; counts[1].textContent = state.following.length; }
    const mini = document.querySelector(".mini-garage");
    if (mini) {
      mini.querySelectorAll(".mini-car").forEach(element => element.remove());
      mini.querySelector(".aside-link").insertAdjacentHTML("beforebegin", state.cars.filter(car => car.userId === user().id).slice(-2).map(car => `<a class="mini-car" href="${carUrl(car)}"><img src="${e(safeImage(car.photo))}" alt="${e(car.brand + " " + car.model)}"><span><strong>${e(car.brand + " " + car.model)}</strong><small>${car.year} · ${e(car.color)}</small></span></a>`).join(""));
    }
  }
  function renderDetail() {
    if (!document.querySelector("#viewer-form")) return;
    const localId = new URLSearchParams(location.search).get("id");
    if (location.pathname.endsWith("/carro.html") && localId) document.body.dataset.carId = localId;
    const car = currentCar();
    if (!car) {
      document.getElementById("main").innerHTML = '<section class="panel empty-state"><h1>Este projeto não está neste navegador.</h1><p>Os projetos criados na demonstração ficam somente no dispositivo usado para salvá-los.</p><a class="btn btn-primary" href="garagem.html">Voltar à garagem</a></section>';
      document.querySelectorAll('script[src*="chart.js"],script[src*="viewer.js"]').forEach(element => element.remove());
      return;
    }
    if (document.body.dataset.homeDemo === "true") {
      const data=history(car);document.getElementById("power-data").textContent=JSON.stringify(data);window.GarageCharts?.refresh(data);
      applyViewer(car);return;
    }
    document.title = `${car.brand} ${car.model} ${car.year} de @${state.users.find(u=>u.id===car.userId).username} · GarageHub`;
    document.querySelector("[data-car-model]").textContent = car.model;
    document.querySelector("[data-car-spec]").textContent = [car.engine, car.transmission, car.color].filter(Boolean).join(" · ");
    document.querySelector("[data-car-description]").textContent = car.description || "Um novo capítulo na garagem.";
    const image = document.getElementById("gallery-main"); image.src = safeImage(car.photo); image.alt = `${car.brand} ${car.model}`;
    document.querySelectorAll("[data-gallery-src]").forEach(button => { button.dataset.gallerySrc = safeImage(car.photo); button.querySelector("img").src = safeImage(car.photo); });
    const stats = [...car.stats].sort((a, b) => a.date.localeCompare(b.date));
    const latest = stats.at(-1);
    document.querySelectorAll("[data-stat]").forEach(element => { element.querySelector("[data-value]").textContent = f.number(latest?.[element.dataset.stat]); });
    const caption = document.querySelector(".stats-grid").previousElementSibling.querySelector(".muted");
    if (caption) caption.textContent = latest ? `Última medição: ${f.date(latest.date)}` : "Nenhuma medição registrada";
    const tbody = document.querySelector(".history tbody");
    if (tbody) tbody.innerHTML = stats.map(item => `<tr><td>${f.date(item.date)}</td>${["power", "torque", "zero_to_hundred", "top_speed", "consumption"].map(metric => `<td>${f.number(item[metric])}</td>`).join("")}</tr>`).join("") || '<tr><td colspan="6">Nenhuma medição registrada.</td></tr>';
    document.querySelector("[data-modifications]").innerHTML = [...car.modifications].sort((a, b) => b.date.localeCompare(a.date)).map(mod => `<div class="modification"><span class="feature-icon small" aria-hidden="true">↗</span><div><strong>${e(mod.name)}</strong><small>${e(mod.category)} · ${f.date(mod.date)}</small></div><span class="mod-price">${f.money(mod.value)}</span></div>`).join("") || '<p class="muted">Original por enquanto. Cada mudança tem sua história.</p>';
    document.querySelector(".modifications-panel .count-badge").textContent = car.modifications.length;
    const data = history(car); document.getElementById("power-data").textContent = JSON.stringify(data);
    window.GarageCharts?.refresh(data);
    applyViewer(car);
  }
  function applyViewer(car) {
    const config = car.viewerConfig, defaults = car.defaults;
    document.getElementById("viewer-config").textContent = JSON.stringify(config);
    document.getElementById("viewer-defaults").textContent = JSON.stringify(defaults);
    const form = document.getElementById("viewer-form");
    for (const [name, value] of Object.entries(config)) form.elements[name].value = name === "spoiler" ? (value ? "yes" : "no") : value;
    form.dispatchEvent(new Event("input", { bubbles: true }));
  }
  function renderFeed() {
    const container = document.querySelector("[data-feed-posts]");
    if (!container) return;
    const form = document.querySelector("[data-feed-filter]");
    const mode = form.elements.filter.value, brand = form.elements.brand.value;
    const feedParams = new URLSearchParams();
    if (mode === "following") feedParams.set("filter", mode);
    if (brand) feedParams.set("brand", brand);
    historyReplace(feedParams);
    const posts = [...state.posts].filter(post => {
      const follows = post.userId === user().id || state.following.includes(post.userId);
      const matches = !brand || state.cars.some(car => car.userId === post.userId && car.brand === brand);
      return matches && (mode === "all" || follows);
    }).sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt));
    container.innerHTML = posts.map(post => {
      const owner = state.users.find(item => item.id === post.userId), liked = post.likes.includes(user().id);
      return `<article class="panel post" id="post-${e(post.id)}"><div class="post-header">${account(owner)}${time(post.createdAt)}</div>${post.text ? `<p class="post-text preserve-lines">${e(post.text)}</p>` : ""}${post.photo ? `<img class="post-photo" src="${e(safeImage(post.photo))}" alt="Foto publicada por ${e(owner.username)}" loading="lazy">` : ""}<div class="post-actions"><button class="reaction ${liked ? "liked" : ""}" data-like="${e(post.id)}" aria-pressed="${liked}" aria-label="${liked ? "Descurtir" : "Curtir"} post">♡ <span>${post.likes.length}</span> curtidas</button><button class="reaction" data-comment-focus="${e(post.id)}">◌ ${post.comments.length} comentários</button>${post.userId === user().id ? `<button class="text-button muted push-right" data-delete-post="${e(post.id)}">Excluir</button>` : ""}</div><div class="comments">${post.comments.map(comment => {
        const author = state.users.find(item => item.id === comment.userId);
        return `<div class="comment"><a href="${profileUrl(author)}">${avatar(author)}</a><div><a class="comment-author" href="${profileUrl(author)}">${e(author.username)}</a><p class="preserve-lines">${e(comment.text)}</p>${time(comment.createdAt)}</div></div>`;
      }).join("")}<form class="comment-form" data-comment="${e(post.id)}"><input id="comment-${e(post.id)}" name="text" maxlength="500" aria-label="Comentar no post de ${e(owner.username)}" placeholder="Deixe um comentário…" required><button class="icon-button" aria-label="Enviar comentário">→</button></form></div></article>`;
    }).join("") || '<section class="panel empty-state"><h2>Nenhuma publicação por aqui ainda.</h2><p>Experimente outra marca, veja Todos ou siga novas garagens.</p><a class="btn btn-secondary" href="amigos.html">Encontrar pessoas</a></section>';
    document.querySelectorAll(".pagination").forEach(element => element.remove());
    f.refreshTimes(); renderGarages();
  }
  const followButton = owner => `<button class="btn ${state.following.includes(owner.id) ? "btn-secondary" : "btn-primary"} btn-small" data-follow="${owner.id}" aria-pressed="${state.following.includes(owner.id)}">${state.following.includes(owner.id) ? "Seguindo" : "Seguir"}</button>`;
  function friendshipButton(owner) {
    const status = state.friendships[owner.id];
    return `<button class="btn btn-quiet btn-small" data-friend="${owner.id}">${status === "accepted" ? "Amigos · remover" : status === "pending" ? "Pedido enviado · cancelar" : "Adicionar amigo"}</button>`;
  }
  function renderFriends() {
    const grid = document.querySelector(".people-grid");
    if (!grid) return;
    const q = document.querySelector(".community-search [name=q]").value;
    const filters = document.querySelector("[data-friends-filter]");
    const city = filters.elements.city.value, brand = filters.elements.brand.value, order=filters.elements.order.value;
    const friendParams = new URLSearchParams();
    if (q) friendParams.set("q", q);
    if (city) friendParams.set("city", city);
    if (brand) friendParams.set("brand", brand);
    if (order!=="recent") friendParams.set("order",order);
    historyReplace(friendParams);
    const owners = state.users.filter(owner => owner.id !== user().id).filter(owner => {
      const cars = state.cars.filter(car => car.userId === owner.id);
      const searchable = normalize([owner.username, owner.city, ...cars.map(car => car.brand + " " + car.model)].join(" "));
      return (!q || searchable.includes(normalize(q))) && (!city || owner.city === city) && (!brand || cars.some(car => car.brand === brand));
    });
    const carsCount=owner=>state.cars.filter(car=>car.userId===owner.id).length;
    const likesCount=owner=>state.posts.filter(post=>post.userId===owner.id).reduce((sum,post)=>sum+post.likes.length,0);
    owners.sort((a,b)=>(order==="cars"?carsCount(b)-carsCount(a):order==="likes"?likesCount(b)-likesCount(a):Date.parse(b.createdAt)-Date.parse(a.createdAt))||a.username.localeCompare(b.username,"pt-BR"));
    grid.innerHTML = owners.map(owner => `<article class="panel person-card"><a href="${profileUrl(owner)}">${avatar(owner)}<h3>${e(owner.username)}</h3></a><p class="muted">${e(owner.city)}</p><p class="person-bio">${e(owner.bio)}</p><span class="tag">${state.cars.filter(car => car.userId === owner.id).length} veículos</span><div class="person-actions">${followButton(owner)}${friendshipButton(owner)}</div></article>`).join("") || '<section class="panel empty-state"><h3>Nenhuma garagem encontrada.</h3><p>Tente outro nome, cidade ou modelo. Há sempre um projeto para descobrir.</p><button class="btn btn-secondary" data-clear-filters>Limpar filtros</button></section>';
    const friends = document.querySelector(".friends-list");
    friends.innerHTML = state.users.filter(owner => owner.id !== user().id && state.friendships[owner.id] === "accepted").map(owner => `<div class="friend-row">${account(owner)}${friendshipButton(owner)}</div>`).join("") || '<p class="muted">Conheça a comunidade e faça novas conexões.</p>';
    document.querySelector("[data-pending-requests]").innerHTML = state.users.filter(owner => state.friendships[owner.id] === "pending").map(owner => `<div class="friend-row">${account(owner)}${friendshipButton(owner)}</div>`).join("") || '<p class="muted">Nenhum pedido pendente.</p>';
  }
  function renderProfile() {
    const heading = document.querySelector(".profile-heading"); if (!heading) return;
    const match = decodeURIComponent(location.pathname).match(/perfil-(.+)\.html$/);
    const owner = state.users.find(item => item.username === match?.[1]); if (!owner) return;
    document.querySelector(".profile-about > p").textContent = owner.bio;
    heading.querySelector(".profile-identity p").textContent = owner.city + " · Perfil de exemplo";
    const counts = document.querySelectorAll(".profile-counts strong");
    counts[0].textContent = state.cars.filter(car => car.userId === owner.id).length;
    counts[1].textContent = owner.followers + (state.following.includes(owner.id) ? 1 : 0);
    if (owner.id !== user().id) heading.querySelector(".actions").innerHTML = followButton(owner) + friendshipButton(owner);
  }
  function historyReplace(params) {
    window.history.replaceState(null, "", location.pathname + (params.size ? "?" + params.toString() : ""));
  }
  function refreshFilterOptions() {
    const brands = [...new Set(state.cars.map(car => car.brand))].sort();
    document.querySelectorAll('select[name="brand"]').forEach(select => {
      const selected=select.value; select.innerHTML='<option value="">Todas as marcas</option>'+brands.map(brand => `<option value="${e(brand)}">${e(brand)}</option>`).join(""); select.value=brands.includes(selected)?selected:"";
    });
  }
  function render() { refreshFilterOptions(); renderGarages(); renderFeed(); renderFriends(); renderProfile(); f.refreshTimes(); }

  // O diálogo nativo mantém foco, Escape e navegação por teclado no formulário.
  const modal = document.createElement("dialog"); modal.className = "preview-modal";
  modal.setAttribute("aria-labelledby", "modal-title"); modal.setAttribute("aria-describedby", "modal-note");
  document.body.append(modal);
  modal.addEventListener("close", () => { if (trigger?.isConnected) trigger.focus(); });
  modal.addEventListener("click", event => { if (event.target === modal && !event.target.closest("form")) {
    const rect = modal.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) modal.close();
  } });
  const field = (name, label, value = "", attrs = "") => `<label>${e(label)}<input name="${name}" value="${e(value)}" ${attrs}></label>`;
  function openModal(kind, id, element) {
    trigger = element;
    const car = kind === "car" ? null : getCar(id) || (document.querySelector("#viewer-form") ? currentCar() : null);
    let title, content;
    if (kind === "car" || kind === "edit") {
      title = kind === "edit" ? "Editar carro" : "Adicionar veículo";
      const c = kind === "edit" ? car : null;
      content = `<div class="form-grid">${field("brand", "Marca *", c?.brand, 'maxlength="50" required')}${field("model", "Modelo *", c?.model, 'maxlength="80" required')}${field("year", "Ano *", c?.year || new Date().getFullYear(), `type="number" min="1886" max="${new Date().getFullYear()+1}" required`)}${field("color", "Cor *", c?.color || "Azul", 'maxlength="40" required')}${field("engine", "Motor", c?.engine, 'maxlength="80"')}${field("transmission", "Câmbio", c?.transmission, 'maxlength="50"')}${field("paint_color", "Pintura no 3D", c?.viewerConfig.paint_color || "#244f91", 'type="color"')}<label>Suspensão<select name="suspension"><option value="original">Original</option><option value="lowered" ${c?.viewerConfig.suspension === "lowered" ? "selected" : ""}>Rebaixada</option></select></label>${field("wheel_size", "Tamanho das rodas (×)", c?.viewerConfig.wheel_size || 1, 'type="number" min="0.8" max="1.3" step="0.05" required')}</div><label>Descrição<textarea name="description" maxlength="2000" rows="3">${e(c?.description)}</textarea></label><label>Foto do projeto<input name="photo" type="file" accept="image/jpeg,image/png,image/webp"><small>Até 6 MB. A imagem é reduzida para caber no navegador.</small></label>`;
    } else if (kind === "evolution" || kind === "modification") {
      if (!car) { toast("Escolha um carro na garagem para registrar a evolução."); location.href = "garagem.html"; return; }
      title = kind === "evolution" ? "Registrar evolução" : "Nova modificação";
      const latest = [...car.stats].sort((a,b) => a.date.localeCompare(b.date)).at(-1);
      content = field("date", "Data *", f.day(new Date()), `type="date" min="1900-01-01" max="${f.day(new Date())}" required`);
      if (kind === "evolution") content += `<div class="form-grid">${[["power","Potência (cv) *",1,10000],["torque","Torque (Nm)",1,20000],["zero_to_hundred","0–100 km/h (s)",.1,120],["top_speed","Velocidade máxima (km/h)",1,1000],["consumption","Consumo (km/l)",.1,100]].map(([name,label,min,max]) => field(name,label,latest?.[name] ?? "",`type="number" min="${min}" max="${max}" step="any" ${name === "power" ? "required" : ""}`)).join("")}</div><p class="local-note">Informe os números medidos no seu projeto.</p>`;
      else content += field("name","Nome *","",'maxlength="100" required') + field("category","Categoria *","Motor",'maxlength="50" required') + field("value","Valor (R$) *","",'inputmode="decimal" placeholder="2.500,00" required');
      content += `<button type="button" class="btn btn-quiet" data-switch-modal="${kind === "evolution" ? "modification" : "evolution"}">${kind === "evolution" ? "Adicionar modificação" : "Registrar medição"}</button>`;
    } else {
      title = "Editar perfil de exemplo";
      content = field("city","Cidade",user().city,'maxlength="80"') + `<label>Sobre você<textarea name="bio" maxlength="500" rows="4">${e(user().bio)}</textarea></label>`;
    }
    modal.innerHTML = `<div class="modal-heading"><div><span class="eyebrow">SEU PRÓXIMO CAPÍTULO</span><h2 id="modal-title">${title}</h2></div><button type="button" class="icon-button" data-close-modal aria-label="Fechar formulário">×</button></div><p id="modal-note" class="local-note">Demonstração: os dados ficam apenas neste navegador.</p><form class="form-stack" novalidate data-modal-kind="${kind}" data-modal-car="${e(car?.id || "")}">${content}<p id="modal-validation" class="form-error" role="alert" hidden></p><div class="actions"><button class="btn btn-primary">Salvar ${kind === "evolution" ? "medição" : kind === "modification" ? "modificação" : kind === "profile" ? "perfil" : "veículo"}</button><button type="button" class="btn btn-quiet" data-close-modal>Cancelar</button></div></form>`;
    if (!modal.open) modal.showModal();
    modal.querySelector("input,textarea")?.focus();
  }
  modal.addEventListener("input",event=>{event.target.removeAttribute("aria-invalid");event.target.removeAttribute("aria-describedby");});
  async function photoData(file) {
    if (!file || !file.size) return null;
    if (!/^image\/(jpeg|png|webp)$/.test(file.type) || file.size > 6 * 1024 * 1024) throw new Error("Escolha uma foto JPG, PNG ou WebP de até 6 MB.");
    const url = URL.createObjectURL(file);
    try {
      const image = new Image(); image.src = url; await image.decode();
      if (image.width*image.height>25000000) throw new Error("Escolha uma foto com até 25 megapixels.");
      const scale = Math.min(1, 1200 / Math.max(image.width, image.height));
      const canvas = document.createElement("canvas"); canvas.width = Math.round(image.width * scale); canvas.height = Math.round(image.height * scale);
      canvas.getContext("2d").drawImage(image, 0, 0, canvas.width, canvas.height);
      const data = canvas.toDataURL("image/jpeg", .78);
      if (data.length > 800000) throw new Error("Essa foto ainda é grande para a prévia. Escolha outra imagem.");
      return data;
    } catch (error) { throw new Error(error.message || "Não foi possível ler essa imagem."); }
    finally { URL.revokeObjectURL(url); }
  }
  async function saveModal(form) {
    const data = new FormData(form), kind = form.dataset.modalKind, car = getCar(form.dataset.modalCar);
    const text = name => String(data.get(name) || "").trim();
    const button = form.querySelector('[type="submit"],.btn-primary'); button.disabled = true;
    try {
      const invalid=[...form.elements].find(input=>input.willValidate && !input.checkValidity());
      if (invalid) {
        invalid.setAttribute("aria-invalid","true");invalid.setAttribute("aria-describedby","modal-validation");invalid.focus();
        const name=invalid.closest("label")?.childNodes[0].textContent.trim()||"Este campo";
        throw new Error(`${name}: ${invalid.validity.valueMissing?"preencha este campo.":invalid.validity.rangeUnderflow||invalid.validity.rangeOverflow?`use um valor entre ${invalid.min} e ${invalid.max}.`:invalid.validity.stepMismatch?"confira o intervalo permitido.":"confira o valor informado."}`);
      }
      if (kind === "car" || kind === "edit") {
        if (!text("brand") || !text("model") || !text("color")) throw new Error("Preencha marca, modelo e cor.");
        const photo = await photoData(data.get("photo")), id = car?.id || uid();
        const config = { paint_color: text("paint_color"), wheel_color: car?.viewerConfig.wheel_color || "#bfc4cc", wheel_size: Number(text("wheel_size")), suspension: text("suspension"), spoiler: car?.viewerConfig.spoiler || false };
        commit(draft => {
          const changes = { brand:text("brand"), model:text("model"), color:text("color"), year:Number(text("year")), engine:text("engine"), transmission:text("transmission"), description:text("description"), viewerConfig:config, defaults:clone(config) };
          if (kind === "edit" && car) Object.assign(draft.cars.find(item => item.id === car.id), changes, photo ? { photo } : {});
          else draft.cars.push({ id, userId:draft.demoUserId, stats:[], modifications:[], photo:photo || "static/img/car.svg", ...changes });
        });
        modal.close();
        if (document.querySelector("#viewer-form")) { location.reload(); return; }
        render(); toast("Veículo salvo neste navegador. Veja o projeto na garagem.");
      } else if (kind === "evolution" || kind === "modification") {
        if (!car) throw new Error("O carro não foi encontrado neste navegador.");
        const date = text("date");
        if (date < "1900-01-01" || date > f.day(new Date())) throw new Error("Escolha uma data entre 1900 e hoje.");
        const item = { id:uid(), date };
        if (kind === "evolution") {
          for (const [key,min,max] of [["power",1,10000],["torque",1,20000],["zero_to_hundred",.1,120],["top_speed",1,1000],["consumption",.1,100]]) {
            item[key] = text(key) ? Number(text(key).replace(",",".")) : null;
            if ((key === "power" && item[key] == null) || (item[key] != null && (!Number.isFinite(item[key]) || item[key] < min || item[key] > max))) throw new Error("Confira os valores da medição.");
          }
        } else {
          const raw = text("value").replace(/^R\$\s*/,"");
          const value = Number(raw.includes(",") ? raw.replace(/\./g,"").replace(",",".") : raw);
          if (!text("name") || !text("category") || !raw || !Number.isFinite(value) || value < 0 || value > 9999999999.99) throw new Error("Preencha a modificação e um valor válido em reais.");
          Object.assign(item,{name:text("name"),category:text("category"),value:Math.round(value*100)/100});
        }
        commit(draft => draft.cars.find(value => value.id === car.id)[kind === "evolution" ? "stats" : "modifications"].push(item));
        modal.close(); renderDetail(); renderGarages(); toast("Evolução salva somente neste navegador.");
      } else {
        commit(draft => Object.assign(draft.users.find(owner => owner.id === draft.demoUserId), { city:text("city"),bio:text("bio") }));
        modal.close(); render(); toast("Perfil de exemplo atualizado neste navegador.");
      }
    } catch (error) { const alert = form.querySelector(".form-error"); alert.textContent = error.message; alert.hidden = false; }
    finally { button.disabled = false; }
  }
  function toggleFollow(id) {
    if (id === user().id) return;
    commit(draft => { draft.following = draft.following.includes(id) ? draft.following.filter(value => value !== id) : [...draft.following,id]; });
    render(); toast(state.following.includes(id) ? "Você está seguindo esta garagem na demonstração." : "Você deixou de seguir esta garagem.");
  }
  function toggleFriend(id) {
    commit(draft => { if (draft.friendships[id]) delete draft.friendships[id]; else draft.friendships[id] = "pending"; });
    render(); toast(state.friendships[id] ? "Pedido de exemplo enviado neste navegador." : "Amizade ou pedido de exemplo removido.");
  }
  document.addEventListener("click", event => {
    const button = event.target.closest("a,button"); if (!button) return;
    try {
      if (button.hasAttribute("data-close-modal")) { event.preventDefault(); modal.close(); }
      else if (button.dataset.switchModal) { event.preventDefault(); openModal(button.dataset.switchModal, modal.querySelector("form").dataset.modalCar, trigger); }
      else if (button.dataset.previewOpen) { event.preventDefault(); openModal(button.dataset.previewOpen, document.querySelector("#viewer-form") ? document.body.dataset.carId : button.dataset.previewId, button); }
      else if (button.hasAttribute("data-restore-demo")) {
        event.preventDefault(); if (!confirm("Restaurar a demonstração? Os projetos, fotos e alterações locais serão apagados deste navegador.")) return;
        const restored=fresh();restored.visitor=true;localStorage.setItem(storageKey,JSON.stringify(restored));localStorage.removeItem("garagehub:preview:v0.1");state=restored;location.reload();
      }
      else if (button.hasAttribute("data-enter-visitor")) { event.preventDefault(); commit(draft => { draft.visitor=true; }); location.href="feed.html"; }
      else if (button.dataset.like) {
        event.preventDefault(); const id=button.dataset.like;
        commit(draft => { const post=draft.posts.find(item => String(item.id)===id); post.likes = post.likes.includes(draft.demoUserId) ? post.likes.filter(value => value!==draft.demoUserId) : [...post.likes,draft.demoUserId]; });
        renderFeed(); document.querySelector(`[data-like="${CSS.escape(id)}"]`)?.focus({preventScroll:true});
      } else if (button.dataset.commentFocus) { event.preventDefault(); document.getElementById("comment-"+button.dataset.commentFocus)?.focus(); }
      else if (button.dataset.follow) { event.preventDefault(); toggleFollow(Number(button.dataset.follow)); }
      else if (button.dataset.friend) { event.preventDefault(); toggleFriend(Number(button.dataset.friend)); }
      else if (button.dataset.deletePost) {
        event.preventDefault(); if (!confirm("Excluir esta publicação de exemplo e seus comentários?")) return;
        commit(draft => { draft.posts=draft.posts.filter(item => String(item.id)!==button.dataset.deletePost); }); renderFeed(); toast("Publicação removida deste navegador.");
      } else if (button.hasAttribute("data-clear-filters")) {
        document.querySelector(".community-search [name=q]").value="";
        document.querySelector("[data-friends-filter]").reset(); renderFriends();
      }
    } catch(error) { toast(error.message); }
  });
  document.addEventListener("submit", async event => {
    const form=event.target;
    if (form.id === "viewer-form") return;
    event.preventDefault(); event.stopImmediatePropagation();
    try {
      if (form.dataset.modalKind) { await saveModal(form); return; }
      if (form.dataset.comment) {
        const text=form.elements.text.value.trim(), id=form.dataset.comment;
        if (!text || text.length>500) throw new Error("Escreva um comentário de até 500 caracteres.");
        commit(draft => draft.posts.find(post => String(post.id)===id).comments.push({id:uid(),userId:draft.demoUserId,text,createdAt:new Date().toISOString()}));
        renderFeed(); document.getElementById("comment-"+id)?.focus({preventScroll:true}); return;
      }
      if (form.matches(".composer")) {
        const button=form.querySelector(".btn-primary"); button.disabled=true;
        try {
          const text=form.elements.text.value.trim(), photo=await photoData(form.elements.photo.files[0]);
          if ((!text && !photo) || text.length>2000) throw new Error("Escreva uma novidade de até 2.000 caracteres ou escolha uma foto.");
          commit(draft => draft.posts.push({id:uid(),userId:draft.demoUserId,text,photo,createdAt:new Date().toISOString(),likes:[],comments:[]}));
          form.reset(); document.querySelector(".composer-preview").hidden=true;
          form.querySelector("[data-photo-name]").textContent=""; renderFeed(); toast("Publicação salva somente neste navegador.");
        } finally { button.disabled=false; }
        return;
      }
      if (form.matches("[data-feed-filter]")) { renderFeed(); return; }
      if (form.matches("[data-friends-filter]")) { renderFriends(); return; }
      if (form.querySelector("[name=q]")) {
        const q=form.querySelector("[name=q]").value;
        if (document.querySelector(".people-grid")) { document.querySelector(".community-search [name=q]").value=q; renderFriends(); }
        else location.href="amigos.html?q="+encodeURIComponent(q);
        return;
      }
      const action=form.dataset.previewAction || "";
      const follow=action.match(/^\/usuarios\/(\d+)\/seguir$/), friend=action.match(/^\/usuarios\/(\d+)\/amizade\/([^/]+)$/);
      if (follow) { toggleFollow(Number(follow[1])); return; }
      if (friend) { toggleFriend(Number(friend[1])); return; }
      if (action==="/auth/logout") { commit(draft => { draft.visitor=false; }); location.href="index.html"; return; }
      if (/^\/garagem\/\d+\/excluir$/.test(action)) {
        if (!confirm("Excluir este veículo apenas da demonstração neste navegador?")) return;
        commit(draft => { draft.cars=draft.cars.filter(car => String(car.id)!==document.body.dataset.carId); }); location.href="garagem.html"; return;
      }
      toast("Entre como visitante para explorar a demonstração.");
    } catch(error) { toast(error.message); }
  }, true);
  refreshFilterOptions();
  const params=new URLSearchParams(location.search);
  document.querySelectorAll('[name="q"]').forEach(input => { input.value=params.get("q") || ""; });
  const feedFilter=document.querySelector("[data-feed-filter]");
  if (feedFilter) { feedFilter.elements.filter.value=params.get("filter")==="following" ? "following" : "all"; feedFilter.elements.brand.value=params.get("brand") || ""; }
  const friendFilter=document.querySelector("[data-friends-filter]");
  if (friendFilter) { friendFilter.elements.city.value=params.get("city") || ""; friendFilter.elements.brand.value=params.get("brand") || ""; friendFilter.elements.order.value=["recent","cars","likes"].includes(params.get("order"))?params.get("order"):"recent"; }
  window.GaragePreview = {
    saveViewer(config) {
      const car=currentCar(); if (!car) throw new Error("O projeto não foi encontrado neste navegador.");
      if (!/^#[\da-f]{6}$/i.test(config.paint_color) || !/^#[\da-f]{6}$/i.test(config.wheel_color) || !Number.isFinite(config.wheel_size) || config.wheel_size<.8 || config.wheel_size>1.3 || !["original","lowered"].includes(config.suspension)) throw new Error("Confira a configuração do modelo 3D.");
      commit(draft => {
        if (document.body.dataset.homeDemo === "true") draft.homeViewerConfig=config;
        else draft.cars.find(item => item.id===car.id).viewerConfig=config;
      });
    }
  };
  renderDetail(); render();
  if (!location.pathname.endsWith("/index.html") && !location.pathname.endsWith("/acesso.html") && document.body.dataset.homeDemo!=="true") {
    try { commit(draft=>{draft.visitor=true;}); } catch(error) {toast(error.message);}
  }
  if (state.visitor) {
    document.querySelector(".preview-banner strong").textContent="VISITANTE · "+user().username;
    document.querySelector("[data-visitor-status]").hidden=false;
  }
})().catch(error=>{
  const banner=document.querySelector(".preview-banner span");if(banner)banner.textContent="A demonstração não carregou. Atualize a página para testar os formulários.";
  console.warn("Demonstração indisponível:",error.message);
});
