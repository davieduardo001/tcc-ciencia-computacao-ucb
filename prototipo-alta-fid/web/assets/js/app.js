/* Movecity — protótipo (sem backend).
   - Conjunto de ícones SVG (estilo Lucide) injetados em [data-i]
   - Mapa vetorial desenhado em SVG (sem PNG) com marcadores
   - Shell (sidebar + topbar) e interações de demonstração
   Funciona via file:// (sem fetch). */

/* ============================ ÍCONES (Lucide) ============================ */
const ICONS = {
  mail: '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
  lock: '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  eye: '<path d="M2.06 12.35a1 1 0 0 1 0-.7 10.75 10.75 0 0 1 19.88 0 1 1 0 0 1 0 .7 10.75 10.75 0 0 1-19.88 0"/><circle cx="12" cy="12" r="3"/>',
  "eye-off": '<path d="M10.73 5.08a10.74 10.74 0 0 1 11.2 6.57 1 1 0 0 1 0 .7 10.75 10.75 0 0 1-1.44 2.49"/><path d="M14.08 14.16a3 3 0 0 1-4.24-4.24"/><path d="M17.48 17.5a10.75 10.75 0 0 1-15.42-5.15 1 1 0 0 1 0-.7 10.75 10.75 0 0 1 4.45-5.14"/><path d="m2 2 20 20"/>',
  user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  bus: '<path d="M8 6v6"/><path d="M15 6v6"/><path d="M2 12h19.6"/><path d="M18 18h3s.5-1.7.8-2.8c.1-.4.2-.8.2-1.2 0-.4-.1-.8-.2-1.2l-1.4-5C20.1 6.8 19.1 6 18 6H4a2 2 0 0 0-2 2v10h3"/><circle cx="7" cy="18" r="2"/><path d="M9 18h5"/><circle cx="16" cy="18" r="2"/>',
  pin: '<path d="M20 10c0 4.99-5.54 10.19-7.4 11.8a1 1 0 0 1-1.2 0C9.54 20.19 4 14.99 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
  search: '<path d="m21 21-4.34-4.34"/><circle cx="11" cy="11" r="8"/>',
  bell: '<path d="M10.27 21a2 2 0 0 0 3.46 0"/><path d="M3.26 15.33A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.67C19.41 13.96 18 12.5 18 8A6 6 0 0 0 6 8c0 4.5-1.41 5.96-2.74 7.33"/>',
  settings: '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
  star: '<path d="M11.52 2.3a.53.53 0 0 1 .95 0l2.31 4.68a2.12 2.12 0 0 0 1.6 1.16l5.16.76a.53.53 0 0 1 .3.9l-3.74 3.64a2.12 2.12 0 0 0-.61 1.88l.88 5.14a.53.53 0 0 1-.77.56l-4.62-2.43a2.12 2.12 0 0 0-1.97 0L6.4 21.01a.53.53 0 0 1-.77-.56l.88-5.14a2.12 2.12 0 0 0-.61-1.88L2.16 9.8a.53.53 0 0 1 .3-.9l5.16-.76a2.12 2.12 0 0 0 1.6-1.16z"/>',
  navigation: '<path d="m16.24 7.76-1.8 5.41a2 2 0 0 1-1.27 1.27L7.76 16.24l1.8-5.41a2 2 0 0 1 1.27-1.27z"/><circle cx="12" cy="12" r="10"/>',
  map: '<path d="M14.1 5.55a2 2 0 0 0 1.8 0l3.65-1.83A1 1 0 0 1 21 4.62v12.76a1 1 0 0 1-.55.9l-4.55 2.27a2 2 0 0 1-1.8 0l-4.2-2.1a2 2 0 0 0-1.8 0l-3.65 1.83A1 1 0 0 1 3 19.38V6.62a1 1 0 0 1 .55-.9l4.55-2.27a2 2 0 0 1 1.8 0z"/><path d="M15 5.76v15"/><path d="M9 3.24v15"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  "check-circle": '<path d="M21.8 10A10 10 0 1 1 17 3.34"/><path d="m9 11 3 3L22 4"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  chevron: '<path d="m9 18 6-6-6-6"/>',
  "arrow-left": '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
  "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  shield: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
  "shield-check": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
  home: '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .71-1.53l7-6a2 2 0 0 1 2.58 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  cap: '<path d="M21.42 10.92a1 1 0 0 0-.02-1.84L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.83l8.57 3.91a2 2 0 0 0 1.66 0z"/><path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>',
  wifi: '<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.86a10 10 0 0 1 14 0"/><path d="M8.5 16.43a5 5 0 0 1 7 0"/>',
  accessible: '<circle cx="16" cy="4" r="1"/><path d="m18 19 1-7-6 1"/><path d="m5 8 3-3 5.5 3-2.36 3.5"/><path d="M4.24 14.5a5 5 0 0 0 6.88 6"/><path d="M13.76 17.5a5 5 0 0 0-3.12-6.88"/>',
  ban: '<circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/>',
  route: '<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>',
  "octagon-alert": '<path d="M2.59 16.73A2 2 0 0 1 2 15.31V8.69a2 2 0 0 1 .59-1.42l4.69-4.69A2 2 0 0 1 8.69 2h6.62a2 2 0 0 1 1.42.59l4.69 4.69A2 2 0 0 1 22 8.69v6.62a2 2 0 0 1-.59 1.42l-4.69 4.69a2 2 0 0 1-1.42.59H8.69a2 2 0 0 1-1.42-.59z"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
  share: '<path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" x2="12" y1="2" y2="15"/>',
  crosshair: '<circle cx="12" cy="12" r="10"/><line x1="22" x2="18" y1="12" y2="12"/><line x1="6" x2="2" y1="12" y2="12"/><line x1="12" x2="12" y1="6" y2="2"/><line x1="12" x2="12" y1="22" y2="18"/>',
  layers: '<path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
  plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
  zap: '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>',
  send: '<path d="M14.54 21.69a.5.5 0 0 0 .94-.02l6.5-19a.5.5 0 0 0-.64-.64l-19 6.5a.5.5 0 0 0-.02.94l7.93 3.18a2 2 0 0 1 1.11 1.11z"/><path d="m21.85 2.15-10.94 10.94"/>',
  mailcheck: '<path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/><path d="m16 19 2 2 4-4"/>',
  logout: '<path d="m16 17 5-5-5-5"/><path d="M21 12H9"/><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>',
  file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
  heart: '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
  repeat: '<path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/>',
  walk: '<circle cx="13" cy="4" r="2"/><path d="m14.5 21-1.5-9-3.5 3v5"/><path d="m9.5 9 2-4 3 3 3 1"/><path d="M14 21v-3l-2-3"/>',
  flag: '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/>',
  edit: '<path d="M21.17 6.81a1 1 0 0 0-3.98-3.98L3.84 16.17a2 2 0 0 0-.5.83l-1.32 4.35a.5.5 0 0 0 .62.62l4.35-1.32a2 2 0 0 0 .83-.5z"/><path d="m15 5 4 4"/>',
  bulb: '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
  seat: '<path d="M19 9V6a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v3"/><path d="M3 16a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/><path d="M5 18v2"/><path d="M19 18v2"/>',
  refresh: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
  camera: '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/>',
  moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
  calendar: '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
  google: 'GOOGLE',
};

function svgFor(name, fill) {
  if (name === "google") {
    return '<svg viewBox="0 0 24 24" width="100%" height="100%" aria-hidden="true">' +
      '<path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.76h3.57c2.08-1.92 3.27-4.74 3.27-8.09z"/>' +
      '<path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.76c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23z"/>' +
      '<path fill="#FBBC05" d="M5.84 14.09a6.6 6.6 0 0 1 0-4.18V7.07H2.18a11 11 0 0 0 0 9.86z"/>' +
      '<path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1A11 11 0 0 0 2.18 7.07l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38z"/></svg>';
  }
  const inner = ICONS[name] || ICONS.info;
  const filled = fill ? ' fill="currentColor" stroke="none"' : ' fill="none"';
  return '<svg viewBox="0 0 24 24" width="100%" height="100%"' + filled +
    ' stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    inner + '</svg>';
}

function setIcon(el, name) {
  el.dataset.i = name;
  el.innerHTML = svgFor(name, el.hasAttribute("data-fill"));
}

function hydrateIcons(root) {
  (root || document).querySelectorAll("[data-i]").forEach(el => {
    if (!el.firstElementChild) el.innerHTML = svgFor(el.dataset.i, el.hasAttribute("data-fill"));
  });
}

/* ============================ MAPA VETORIAL ============================ */
function roadGroup(segs, width, color, opacity) {
  return `<g stroke="${color}" stroke-width="${width}" stroke-linecap="round" fill="none" opacity="${opacity||1}">` +
    segs.map(s => `<line x1="${s[0]}" y1="${s[1]}" x2="${s[2]}" y2="${s[3]}"/>`).join("") + "</g>";
}

function buildMaps() {
  document.querySelectorAll(".map-canvas").forEach(canvas => {
    const variant = canvas.dataset.variant || "default";

    const majors = [
      [0,180,1200,180],[0,300,1200,300],[0,440,1200,440],[0,520,1200,520],[0,640,1200,640],
      [300,0,300,800],[540,0,540,800],[600,0,600,800],[720,0,720,800],[840,0,840,800],[960,0,960,800]
    ];
    const diagonals = [[-50,820,1180,160],[1240,820,160,-20]];
    const minors = [
      [0,110,1200,110],[0,380,1200,380],[0,580,1200,580],[0,720,1200,720],
      [150,0,150,800],[420,0,420,800],[670,0,670,800],[900,0,900,800],[1080,0,1080,800]
    ];

    let extra = "";
    if (variant === "line") {
      extra = `<polyline points="540,90 540,300 600,440 600,720" fill="none" stroke="#1aa0ad" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" opacity=".95"/>` +
        [[540,300],[600,440]].map(p=>`<circle cx="${p[0]}" cy="${p[1]}" r="9" fill="#fff" stroke="#1aa0ad" stroke-width="4"/>`).join("");
    } else if (variant === "route") {
      extra = `<path d="M300,250 L540,300 L600,440 L840,560" fill="none" stroke="#1aa0ad" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>` +
        `<path d="M300,250 L540,300 L600,440 L840,560" fill="none" stroke="#fff" stroke-width="3" stroke-dasharray="2 12" stroke-linecap="round"/>`;
    }

    const svg =
      `<svg class="map-svg" viewBox="0 0 1200 800" preserveAspectRatio="none">
        <rect width="1200" height="800" fill="#e7eef0"/>
        <ellipse cx="930" cy="240" rx="170" ry="120" fill="#d6e8d8"/>
        <ellipse cx="180" cy="610" rx="150" ry="110" fill="#d6e8d8"/>
        <rect x="430" y="350" width="180" height="130" rx="18" fill="#dde8e9"/>
        ${roadGroup(diagonals, 30, '#d9e3e5')}
        ${roadGroup(majors, 22, '#d9e3e5')}
        ${roadGroup(diagonals, 20, '#ffffff')}
        ${roadGroup(majors, 13, '#ffffff')}
        ${roadGroup(minors, 5, '#ffffff', .9)}
        ${extra}
      </svg>`;
    canvas.insertAdjacentHTML("afterbegin", svg);
  });
}

/* ============================ SHELL ============================ */
const NAV = [
  { id: "mapa",        href: "mapa.html",          ic: "map",        label: "Mapa Interativo" },
  { id: "linhas",      href: "buscar-linha.html",  ic: "bus",        label: "Linhas de Ônibus" },
  { id: "rotas",       href: "calcular-rota.html", ic: "navigation", label: "Rotas" },
  { id: "favoritos",   href: "favoritos.html",     ic: "star",       label: "Rotas Salvas" },
  { id: "ocorrencias", href: "ocorrencias.html",   ic: "alert",      label: "Ocorrências" },
  { id: "alertas",     href: "alertas.html",       ic: "bell",       label: "Alertas" },
  { id: "perfil",      href: "perfil.html",        ic: "user",       label: "Perfil" },
];

function buildShell() {
  const body = document.body;
  if (!body.classList.contains("app-shell")) return;
  const active = body.dataset.active || "";

  const side = document.createElement("aside");
  side.className = "sidebar";
  side.innerHTML = `
    <div class="brand">
      <div class="mark">M</div>
      <div><b>Movecity</b><small>Mobilidade DF</small></div>
    </div>
    <nav class="nav">
      ${NAV.map(n => `<a href="${n.href}" class="${n.id===active?'active':''}">
        <span class="ico ico-sm" data-i="${n.ic}"></span><span>${n.label}</span></a>`).join("")}
    </nav>
    <div class="spacer"></div>
    <a href="calcular-rota.html" class="btn btn-primary btn-block new-trip"><span class="ico ico-sm" data-i="plus"></span> Nova Viagem</a>
    <div class="user">
      <div class="av">AM</div>
      <div><b style="font-size:13px">Admin Movecity</b><small>Conta demo</small></div>
    </div>`;

  const top = document.createElement("header");
  top.className = "topbar";
  top.innerHTML = `
    <div class="search">
      <span class="lead ico ico-sm" data-i="search"></span>
      <input class="input" placeholder="Para onde vamos? Busque linha, parada ou destino">
    </div>
    <div class="actions">
      <a class="icon-btn" href="alertas.html" title="Alertas"><span class="ico ico-sm" data-i="bell"></span><span class="badge-count">3</span></a>
      <a class="icon-btn" href="preferencias.html" title="Preferências"><span class="ico ico-sm" data-i="settings"></span></a>
      <a class="icon-btn" href="perfil.html" title="Perfil"><span class="ico ico-sm" data-i="user"></span></a>
    </div>`;

  body.prepend(top);
  body.prepend(side);
}

/* ============================ INTERAÇÕES ============================ */
function bindPasswordToggles() {
  document.querySelectorAll("[data-toggle-pass]").forEach(btn => {
    btn.addEventListener("click", () => {
      const inp = document.getElementById(btn.dataset.togglePass);
      if (!inp) return;
      const hidden = inp.type === "password";
      inp.type = hidden ? "text" : "password";
      setIcon(btn, hidden ? "eye-off" : "eye");
    });
  });
}

function bindTabs() {
  document.querySelectorAll("[data-tabs]").forEach(group => {
    const btns = group.querySelectorAll("button");
    btns.forEach(b => b.addEventListener("click", () => {
      btns.forEach(x => x.classList.remove("active"));
      b.classList.add("active");
      const target = b.dataset.tab;
      group.closest("[data-tabs-scope]")?.querySelectorAll("[data-panel]")
        .forEach(p => p.style.display = p.dataset.panel === target ? "" : "none");
    }));
  });
}

function bindChips() {
  document.querySelectorAll(".chip").forEach(c =>
    c.addEventListener("click", () => c.classList.toggle("on")));
}

function bindModals() {
  document.querySelectorAll("[data-open]").forEach(t =>
    t.addEventListener("click", e => { e.preventDefault(); document.getElementById(t.dataset.open)?.classList.add("open"); }));
  document.querySelectorAll("[data-close]").forEach(t =>
    t.addEventListener("click", () => t.closest(".modal-back")?.classList.remove("open")));
  document.querySelectorAll(".modal-back").forEach(m =>
    m.addEventListener("click", e => { if (e.target === m) m.classList.remove("open"); }));
}

function bindConfirm() {
  document.querySelectorAll("[data-confirm]").forEach(btn =>
    btn.addEventListener("click", () => {
      const counter = btn.closest(".occ")?.querySelector("[data-count]");
      if (counter) counter.textContent = (parseInt(counter.textContent) || 0) + 1;
      btn.innerHTML = '<span class="ico ico-sm" data-i="check"></span> Confirmado';
      hydrateIcons(btn);
      btn.disabled = true; btn.style.opacity = ".6";
    }));
}

function bindDemoForms() {
  document.querySelectorAll("form[data-demo]").forEach(f =>
    f.addEventListener("submit", e => { e.preventDefault(); if (f.dataset.demo) window.location.href = f.dataset.demo; }));
}

document.addEventListener("DOMContentLoaded", () => {
  buildShell();
  buildMaps();
  hydrateIcons();
  bindPasswordToggles();
  bindTabs();
  bindChips();
  bindModals();
  bindConfirm();
  bindDemoForms();
});
