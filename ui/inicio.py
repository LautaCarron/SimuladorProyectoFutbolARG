"""Pantalla de inicio de Proyecto AFA ("Elegí un modo": Simulador o Manager Falopa) para cuando la app corre con Streamlit
(Streamlit Community Cloud o `streamlit run` en la PC).

En la web estática (stlite) la intro vive en index.html; acá es la misma pantalla, hecha en HTML y
dibujada encima de todo. El botón "Entrar" del HTML aprieta un botón oculto de Streamlit (con un
script chico), así se pasa al simulador sin recargar la página ni perder la sesión.
"""

import json

import streamlit as st

# Sol de Mayo geométrico: 16 rayos alternando largo (mismo dibujo que la intro de index.html)
_RAYOS = "".join(f'<polygon points="-3.2,-21 0,-{36 if k % 2 else 47} 3.2,-21" transform="rotate({k * 22.5})"/>'
                 for k in range(16))
_SOL_LLENO = f'<svg viewBox="-50 -50 100 100" aria-hidden="true"><g fill="currentColor">{_RAYOS}<circle r="16.5"/></g></svg>'
_SOL_LINEA = (f'<svg viewBox="-50 -50 100 100" aria-hidden="true"><g fill="none" stroke="currentColor" '
              f'stroke-width=".16" stroke-linejoin="round">{_RAYOS}<circle r="17"/><circle r="12.5"/></g></svg>')
_FLECHA = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M2 8h11M9 4l4 4-4 4"/></svg>'
_CANDADO = ('<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="2" y="5.5" '
            'width="8" height="5.5" rx="1"/><path d="M4 5.5V4a2 2 0 0 1 4 0v1.5"/></svg>')

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,300..900&display=swap');
/* Mientras está la intro, lo de Streamlit queda escondido detrás */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
.st-key-afa_entrar, .st-key-afa_ir_manager { position: absolute !important; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); opacity: 0; pointer-events: none; }

#afa-intro {
  --tiza: #F4F2EC; --tinta: #0F1B2D; --tinta-2: #4A5566; --tinta-3: #8A919C;
  --regla: rgba(15, 27, 45, .14); --celeste: #74ACDF; --celeste-hondo: #2F6DB0; --sol: #E3A21A;
  --luz: rgba(255, 255, 255, .95); --franja: rgba(116, 172, 223, .10); --rayado: rgba(15, 27, 45, .05);
  --sol-op: .55; --ease-out: cubic-bezier(.16, 1, .3, 1); --ease-io: cubic-bezier(.65, 0, .35, 1);
  --margen: max(clamp(20px, 5vw, 64px), calc((100vw - 1320px) / 2 + clamp(20px, 5vw, 64px)));
  position: fixed; inset: 0; z-index: 999990; overflow-y: auto; overflow-x: hidden;
  background: var(--tiza); color: var(--tinta); color-scheme: light;
  font-family: "Archivo", system-ui, sans-serif; -webkit-font-smoothing: antialiased;
  display: grid; grid-template-rows: auto 1fr auto; grid-template-columns: minmax(0, 1fr);
  transition: opacity .42s var(--ease-io), translate .42s var(--ease-io);
}
#afa-intro * { box-sizing: border-box; }
#afa-intro button { font: inherit; color: inherit; }
@media (prefers-color-scheme: dark) {
  :root:not([data-tema="claro"]) #afa-intro {
    --tiza: #0E141C; --tinta: #E8E6DF; --tinta-2: #A7AEB9; --tinta-3: #6F7885; --regla: rgba(232, 230, 223, .14);
    --celeste-hondo: #8CC0EE; --luz: rgba(116, 172, 223, .10); --franja: rgba(116, 172, 223, .07);
    --rayado: rgba(232, 230, 223, .05); --sol-op: .3; color-scheme: dark;
  }
}
:root[data-tema="oscuro"] #afa-intro {
  --tiza: #0E141C; --tinta: #E8E6DF; --tinta-2: #A7AEB9; --tinta-3: #6F7885; --regla: rgba(232, 230, 223, .14);
  --celeste-hondo: #8CC0EE; --luz: rgba(116, 172, 223, .10); --franja: rgba(116, 172, 223, .07);
  --rayado: rgba(232, 230, 223, .05); --sol-op: .3; color-scheme: dark;
}
#afa-intro.saliendo { opacity: 0; translate: 0 -12px; pointer-events: none; }

#afa-intro .fondo { position: fixed; inset: 0; pointer-events: none; overflow: hidden; }
#afa-intro .fondo .luz { position: absolute; inset: -20% -10% auto -10%; height: 90%;
  background: radial-gradient(60% 60% at 30% 0%, var(--luz), transparent 70%); }
#afa-intro .fondo .franjas { position: absolute; top: 0; bottom: 0; right: 0; width: 26vw;
  background: repeating-linear-gradient(90deg, var(--franja) 0 5.2vw, transparent 5.2vw 10.4vw);
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 40%); mask-image: linear-gradient(90deg, transparent, #000 40%);
  opacity: 0; animation: afa-aparecer 1.6s .2s var(--ease-io) forwards; }
#afa-intro .fondo .sol-gigante { position: absolute; width: min(78vw, 860px); aspect-ratio: 1; left: max(-14vw, -200px);
  top: 52%; translate: 0 -50%; color: var(--celeste); opacity: 0; animation: afa-tenue 2.2s .1s var(--ease-io) forwards; }
#afa-intro .fondo .sol-gigante svg { width: 100%; height: 100%; }

#afa-intro .barra { position: relative; display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 22px var(--margen); font-size: 13px; letter-spacing: .02em; }
#afa-intro .marca { display: flex; align-items: center; gap: 10px; font-weight: 800; font-stretch: 112%;
  text-transform: uppercase; letter-spacing: .06em; font-size: 13px; }
#afa-intro .marca .sol { display: inline-flex; width: 26px; height: 26px; color: var(--sol); }
#afa-intro [data-sol] svg { width: 100%; height: 100%; display: block; }
#afa-intro .meta { color: var(--tinta-2); display: flex; align-items: center; gap: 18px; font-stretch: 85%;
  text-transform: uppercase; letter-spacing: .12em; font-size: 11px; font-weight: 600; }
#afa-intro .meta b { color: var(--tinta); font-weight: 700; }

#afa-intro .escena { position: relative; align-self: center; width: 100%; margin: 0; padding: 12px var(--margen) 40px;
  display: grid; grid-template-columns: minmax(0, .92fr) minmax(0, 1.08fr); gap: clamp(28px, 5vw, 80px); align-items: end; }
#afa-intro .kicker { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 0 0 18px; padding: 0; list-style: none;
  font-stretch: 80%; font-weight: 600; text-transform: uppercase; letter-spacing: .16em; font-size: 12px; color: var(--tinta-2); }
#afa-intro .kicker li { margin: 0; opacity: 0; translate: 0 6px; animation: afa-subir .7s var(--ease-out) forwards; }
#afa-intro .kicker li + li::before { content: ""; display: inline-block; width: 4px; height: 4px; border-radius: 50%;
  background: var(--celeste-hondo); margin-right: 14px; vertical-align: middle; translate: 0 -2px; }
#afa-intro .kicker li:nth-child(1) { animation-delay: 1.15s; } #afa-intro .kicker li:nth-child(2) { animation-delay: 1.25s; }
#afa-intro .kicker li:nth-child(3) { animation-delay: 1.35s; } #afa-intro .kicker li:nth-child(4) { animation-delay: 1.45s; }
#afa-intro h1.titulo { margin: 0; padding: 0; line-height: .82; font-weight: 900; color: var(--tinta); font-family: inherit; }
#afa-intro .titulo .proyecto { display: block; font-size: clamp(15px, 1.6vw, 20px); font-stretch: 125%; font-weight: 700;
  letter-spacing: .5em; margin-bottom: clamp(10px, 1.6vw, 18px); padding-left: .12em;
  opacity: 0; animation: afa-tracking 1.1s .15s var(--ease-out) forwards; }
#afa-intro .titulo .afa { display: flex; font-size: clamp(112px, 21vw, 290px); font-stretch: 125%; letter-spacing: -.02em; }
#afa-intro .titulo .afa .m { display: inline-block; overflow: hidden; padding: .02em .01em .07em; margin-bottom: -.07em; }
#afa-intro .titulo .afa .m span { display: inline-block; translate: 0 105%; animation: afa-letra 1s var(--ease-out) forwards; }
#afa-intro .titulo .afa .m:nth-child(1) span { animation-delay: .35s; }
#afa-intro .titulo .afa .m:nth-child(2) span { animation-delay: .45s; }
#afa-intro .titulo .afa .m:nth-child(3) span { animation-delay: .55s; }
#afa-intro .firma { display: flex; align-items: center; gap: 14px; margin-top: clamp(16px, 2vw, 26px); }
#afa-intro .firma .cinta { width: clamp(120px, 16vw, 200px); height: 8px; display: grid; grid-template-columns: 1fr 1fr 1fr;
  transform-origin: left; scale: 0 1; animation: afa-dibujar .9s .95s var(--ease-out) forwards; box-shadow: inset 0 0 0 1px var(--regla); }
#afa-intro .firma .cinta i:nth-child(odd) { background: var(--celeste); }
#afa-intro .firma .cinta i:nth-child(2) { background: #fff; }
#afa-intro .firma small { white-space: nowrap; font-stretch: 80%; text-transform: uppercase; letter-spacing: .16em; font-size: 11px;
  font-weight: 600; color: var(--tinta-3); opacity: 0; animation: afa-aparecer .8s 1.5s forwards; }

#afa-intro .modos { margin: 0; padding: 0; list-style: none; border-top: 1.5px solid var(--tinta); }
#afa-intro .modos-titulo { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px;
  font-stretch: 80%; text-transform: uppercase; letter-spacing: .16em; font-size: 11px; font-weight: 700; color: var(--tinta-2);
  opacity: 0; animation: afa-aparecer .6s 1.55s forwards; }
#afa-intro .modo { position: relative; margin: 0; border-bottom: 1px solid var(--regla); opacity: 0; translate: 0 14px;
  animation: afa-subir .8s var(--ease-out) forwards; }
#afa-intro .modo:nth-child(1) { animation-delay: 1.6s; } #afa-intro .modo:nth-child(2) { animation-delay: 1.72s; }
#afa-intro .modo-btn { width: 100%; display: grid; grid-template-columns: 64px minmax(0, 1fr) auto; gap: 18px; align-items: center;
  padding: 22px 18px 22px 4px; background: none; border: 0; border-radius: 0; text-align: left; cursor: pointer;
  transition: padding .35s var(--ease-out); position: relative; isolation: isolate; }
#afa-intro .modo-btn::before { content: ""; position: absolute; inset: 0; z-index: -1; background: var(--tinta);
  transform-origin: left; scale: 0 1; transition: scale .5s var(--ease-out); }
#afa-intro .num { font-stretch: 125%; font-weight: 800; font-size: 34px; line-height: 1; color: transparent;
  -webkit-text-stroke: 1.2px var(--tinta); transition: color .35s, -webkit-text-stroke-color .35s; }
#afa-intro .modo-nombre { display: block; font-stretch: 105%; font-weight: 800; font-size: clamp(18px, 1.7vw, 23px);
  text-transform: uppercase; letter-spacing: .01em; line-height: 1.1; transition: color .35s; }
#afa-intro .modo-desc { display: block; margin-top: 6px; font-size: 15px; line-height: 1.45; color: var(--tinta-2);
  max-width: 40ch; transition: color .35s; }
#afa-intro .modo-cats { display: block; margin-top: 10px; font-stretch: 80%; font-size: 11.5px; font-weight: 600;
  letter-spacing: .12em; text-transform: uppercase; color: var(--tinta-3); transition: color .35s; }
#afa-intro .ir { display: grid; justify-items: end; gap: 8px; }
#afa-intro .accion { display: inline-flex; align-items: center; gap: 10px; font-weight: 700; font-size: 15px;
  padding: 11px 16px 11px 18px; background: var(--tinta); color: var(--tiza); transition: background-color .35s, color .35s; white-space: nowrap; }
#afa-intro .accion .ico { display: inline-flex; width: 16px; height: 16px; transition: translate .35s var(--ease-out); }
#afa-intro .estado { display: inline-flex; align-items: center; gap: 7px; font-size: 12px; color: var(--tinta-2);
  transition: color .35s; white-space: nowrap; }
#afa-intro .estado i { width: 7px; height: 7px; border-radius: 50%; background: #2E8B57; }
#afa-intro.entrando .estado i { background: var(--sol); animation: afa-latido 1.4s ease-in-out infinite; }
@media (hover: hover) {
  #afa-intro .modo:not(.bloqueado) .modo-btn:hover::before, #afa-intro .modo:not(.bloqueado) .modo-btn:focus-visible::before { scale: 1 1; }
  #afa-intro .modo:not(.bloqueado) .modo-btn:hover, #afa-intro .modo:not(.bloqueado) .modo-btn:focus-visible { padding-left: 16px; }
  #afa-intro .modo:not(.bloqueado) .modo-btn:hover .num { color: var(--celeste); -webkit-text-stroke-color: var(--celeste); }
  #afa-intro .modo:not(.bloqueado) .modo-btn:hover .modo-nombre { color: var(--tiza); }
  #afa-intro .modo:not(.bloqueado) .modo-btn:hover .modo-desc { color: color-mix(in srgb, var(--tiza) 78%, transparent); }
  #afa-intro .modo:not(.bloqueado) .modo-btn:hover .modo-cats,
  #afa-intro .modo:not(.bloqueado) .modo-btn:hover .estado { color: color-mix(in srgb, var(--tiza) 62%, transparent); }
  #afa-intro .modo:not(.bloqueado) .modo-btn:hover .accion { background: var(--celeste); color: #0F1B2D; }
  #afa-intro .modo:not(.bloqueado) .modo-btn:hover .accion .ico { translate: 4px 0; }
}
#afa-intro .modo-btn:focus-visible { outline: 2px solid var(--celeste-hondo); outline-offset: 2px; }
#afa-intro .modo-btn:active { scale: .995; }
#afa-intro .modo.bloqueado .modo-btn { cursor: not-allowed; }
#afa-intro .modo.bloqueado .modo-btn::before { display: none; }
#afa-intro .modo.bloqueado .modo-btn::after { content: ""; position: absolute; inset: 0; z-index: -1; opacity: .55;
  background: repeating-linear-gradient(-45deg, transparent 0 7px, var(--rayado) 7px 8px); }
#afa-intro .modo.bloqueado .modo-nombre, #afa-intro .modo.bloqueado .num { opacity: .55; }
#afa-intro .sello { font-stretch: 90%; font-weight: 800; font-size: 12px; letter-spacing: .18em; text-transform: uppercase;
  color: var(--celeste-hondo); border: 1.5px solid currentColor; padding: 7px 10px 6px; rotate: -4deg;
  outline: 1px solid currentColor; outline-offset: 2px; white-space: nowrap; transition: rotate .4s var(--ease-out); }
#afa-intro .modo.bloqueado .modo-btn:hover .sello { rotate: -1deg; }
#afa-intro .bloq { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--tinta-2);
  opacity: 0; translate: 0 -3px; transition: opacity .25s, translate .25s var(--ease-out); white-space: nowrap; }
#afa-intro .bloq .ico { display: inline-flex; width: 12px; height: 12px; }
#afa-intro .modo.bloqueado .modo-btn:hover .bloq, #afa-intro .modo.bloqueado.sacudir .bloq { opacity: 1; translate: 0 0; }
#afa-intro .modo.bloqueado.sacudir .sello { animation: afa-sacudir .45s var(--ease-io); }
#afa-intro .pie { position: relative; display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap;
  padding: 18px var(--margen) calc(18px + env(safe-area-inset-bottom)); font-size: 11.5px; color: var(--tinta-3);
  border-top: 1px solid var(--regla); opacity: 0; animation: afa-aparecer .8s 1.9s forwards; }

@keyframes afa-aparecer { to { opacity: 1; } }
@keyframes afa-tenue { to { opacity: var(--sol-op); } }
@keyframes afa-subir { to { opacity: 1; translate: 0 0; } }
@keyframes afa-letra { to { translate: 0 0; } }
@keyframes afa-dibujar { to { scale: 1 1; } }
@keyframes afa-tracking { from { letter-spacing: 1.1em; opacity: 0; } to { letter-spacing: .5em; opacity: 1; } }
@keyframes afa-latido { 50% { opacity: .35; } }
@keyframes afa-sacudir { 20% { rotate: -9deg; } 45% { rotate: 2deg; } 70% { rotate: -6deg; } 100% { rotate: -4deg; } }

@media (max-width: 980px) {
  #afa-intro .escena { grid-template-columns: minmax(0, 1fr); align-items: start; gap: 40px; padding-top: 4vh; }
  #afa-intro .fondo .franjas { width: 40vw; }
  #afa-intro .fondo .sol-gigante { left: -30vw; top: 24%; width: 110vw; }
}
@media (max-width: 600px) {
  #afa-intro { --margen: 20px; }
  #afa-intro .barra { padding: 16px 20px; }
  #afa-intro .meta > span:not(:first-child) { display: none; }
  #afa-intro .firma .cinta { width: 84px; }
  #afa-intro .firma small { font-size: 10px; letter-spacing: .12em; }
  #afa-intro .escena { padding: 2vh 20px 28px; gap: 30px; }
  #afa-intro .titulo .afa { font-size: 33vw; }
  #afa-intro .titulo .proyecto { letter-spacing: .42em; }
  #afa-intro .kicker { font-size: 10px; letter-spacing: .09em; gap: 4px 7px; margin-bottom: 14px; flex-wrap: nowrap; }
  #afa-intro .kicker li { white-space: nowrap; }
  #afa-intro .kicker li + li::before { margin-right: 7px; width: 3px; height: 3px; }
  #afa-intro .modo-btn { grid-template-columns: 40px minmax(0, 1fr); gap: 4px 12px; padding: 18px 0; align-items: start; }
  #afa-intro .num { font-size: 22px; padding-top: 2px; }
  #afa-intro .modo-desc { font-size: 14px; }
  #afa-intro .ir { grid-column: 1 / -1; justify-items: stretch; margin-top: 14px; }
  #afa-intro .accion { justify-content: space-between; padding: 14px 16px; font-size: 16px; }
  #afa-intro .estado { justify-content: center; }
  #afa-intro .modo.bloqueado .ir { grid-column: 2; justify-items: start; margin-top: 10px; }
  #afa-intro .fondo .sol-gigante { width: 150vw; left: -50vw; top: 20%; }
  #afa-intro .fondo .franjas { width: 45vw; }
  #afa-intro .pie { font-size: 11px; }
}
@media (max-width: 400px) {
  #afa-intro .meta > span { display: none; }
  #afa-intro .kicker { flex-wrap: wrap; row-gap: 6px; }
  #afa-intro .titulo .proyecto { letter-spacing: .36em; }
}
@media (prefers-reduced-motion: reduce) {
  #afa-intro *, #afa-intro *::before, #afa-intro *::after { animation-duration: .01ms !important;
    animation-delay: 0s !important; transition-duration: .01ms !important; }
}
</style>
"""

_HTML = f"""
<main id="afa-intro" aria-label="Proyecto AFA">
  <div class="fondo" aria-hidden="true"><div class="luz"></div><div class="franjas"></div>
    <div class="sol-gigante" data-sol="linea"></div></div>
  <header class="barra">
    <div class="marca"><span class="sol" data-sol="lleno"></span>Proyecto AFA</div>
    <div class="meta"><span>Temporada <b>2026</b></span><span>Beta pública</span></div>
  </header>
  <section class="escena">
    <div>
      <ul class="kicker" aria-label="Fútbol argentino. Simulación. Gestión. Experiencia.">
        <li>Fútbol argentino</li><li>Simulación</li><li>Gestión</li><li>Experiencia</li></ul>
      <h1 class="titulo"><span class="proyecto">PROYECTO</span>
        <span class="afa" aria-label="AFA"><span class="m"><span>A</span></span><span class="m"><span>F</span></span><span class="m"><span>A</span></span></span></h1>
      <div class="firma"><span class="cinta" aria-hidden="true"><i></i><i></i><i></i></span><small>De la Primera al Regional Amateur</small></div>
    </div>
    <nav aria-label="Modos de juego">
      <div class="modos-titulo"><span>Elegí un modo</span><span>2 modos</span></div>
      <ol class="modos">
        <li class="modo">
          <button class="modo-btn" id="afa-entrar" type="button">
            <span class="num" aria-hidden="true">01</span>
            <span><span class="modo-nombre">Simulador Fútbol Argentino</span>
              <span class="modo-desc">Simulá temporadas completas, fecha por fecha: ascensos, descensos, reducidos, promoción, desempates y copas.</span>
              <span class="modo-cats">Primera · B Nacional · Federal A · Primera B · Primera C · Promocional · Regional Amateur</span></span>
            <span class="ir"><span class="accion">Entrar <span class="ico" data-sol="flecha"></span></span>
              <span class="estado" aria-live="polite"><i></i><span>Listo para jugar</span></span></span>
          </button>
        </li>
        <li class="modo" id="afa-manager">
          <button class="modo-btn" id="afa-entrar-manager" type="button">
            <span class="num" aria-hidden="true">02</span>
            <span><span class="modo-nombre">Manager Falopa</span>
              <span class="modo-desc">Agarrá un club y llevalo temporada tras temporada: plantel, objetivos y presión de la tribuna.</span>
              <span class="modo-cats">Arrancá libre y recibí ofertas · o elegí tu equipo</span></span>
            <span class="ir"><span class="accion">Crear manager <span class="ico" data-sol="flecha"></span></span>
              <span class="estado" aria-live="polite"><i></i><span>Creá tu entrenador</span></span></span>
          </button>
        </li>
      </ol>
    </nav>
  </section>
  <footer class="pie">
    <span>Proyecto AFA es un proyecto independiente de fans. No está afiliado a la Asociación del Fútbol Argentino.</span>
    <span>Escudos: ESPN · Wikimedia · TheSportsDB</span>
  </footer>
</main>
"""

# "Entrar" y "Manager Falopa" aprietan su botón oculto de Streamlit (pasan al simulador o al manager).
# Los soles y los íconos (SVG) se dibujan desde acá porque st.html no deja pasar SVG.
_JS = """
<script>
(function () {
  const SOLES = __SOLES__;
  function dibujar() {
    document.querySelectorAll('#afa-intro [data-sol]').forEach(function (el) {
      if (!el.firstChild) el.innerHTML = SOLES[el.dataset.sol];
    });
  }
  dibujar();
  new MutationObserver(dibujar).observe(document.body, { childList: true, subtree: true });
  function boton(clave) { return document.querySelector('.st-key-' + clave + ' button'); }
  if (window.__afaIntro) return;
  window.__afaIntro = true;
  document.addEventListener('click', function (e) {
    const t = e.target.closest && e.target.closest('#afa-entrar, #afa-entrar-manager');
    if (!t) return;
    e.preventDefault();
    const esManager = t.id === 'afa-entrar-manager';
    const intro = document.getElementById('afa-intro');
    if (intro) {
      intro.classList.add('entrando');
      const est = t.querySelector('.estado span');
      if (est) est.textContent = esManager ? 'Abriendo el manager…' : 'Abriendo el simulador…';
    }
    const b = boton(esManager ? 'afa_ir_manager' : 'afa_entrar');
    if (b) b.click();
  });
})();
</script>
"""


def _entrar():
    st.session_state["afa_pantalla"] = "simulador"


def _entrar_manager():
    st.session_state["afa_pantalla"] = "manager"


def _correr_js(js):
    """Corre el script en la página de la app con un iframe de componentes que lo inyecta arriba
    (st.html con JavaScript no siempre lo ejecuta: según la versión, el sanitizador lo descarta)."""
    import streamlit.components.v1 as components
    cuerpo = js.replace("<div hidden></div>", "").replace("<script>", "").replace("</script>", "")
    components.html("<script>const s = window.parent.document.createElement('script');"
                    f"s.textContent = {json.dumps(cuerpo)};"
                    "window.parent.document.head.appendChild(s);</script>", height=0)


def mostrar_inicio():
    """Dibuja la pantalla de inicio y corta la ejecución mientras no se entre al simulador."""
    if (st.session_state.get("afa_pantalla") in ("simulador", "manager")
            or st.query_params.get("modo") in ("simulador", "manager")):
        return
    st.html(_CSS + _HTML)
    st.button("Entrar al simulador", key="afa_entrar", on_click=_entrar)
    st.button("Crear manager", key="afa_ir_manager", on_click=_entrar_manager)
    _correr_js(_JS.replace("__SOLES__", json.dumps({"lleno": _SOL_LLENO, "linea": _SOL_LINEA, "flecha": _FLECHA, "candado": _CANDADO})))
    st.stop()
