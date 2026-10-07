/* =============================================================================
   VISION, VERSION E (mock, 8 Oct 2026): "Every farmer a biomanufacturer."

   Version D's script, for the valley laid out to a far horizon
   (build/vision-student-e.py, assets/img/home/vision-student-e/,
   home-vision-e-data.js as window.__vlbData.e). Same story, same light:
   one daylight picture, a night multiplied over it, each reactor letting its
   own field through, the sun coming up as the camera pulls back. What is new:
   the far fields beyond her painting carry glow-only reactors (D.far) that
   come on last, from her back row out to the skyline; each field's pool is
   foreshortened by its own depth (d[11]); the sun, the ridge line and the
   reactor's place come from the data. The sky, the sun and her reactor
   drawing are version B's files.
   ========================================================================== */

(function () {
  "use strict";

  var sec = document.querySelector(".vlb[data-vle]");
  var D = (window.__vlbData || {}).e;
  if (!sec || !D) return;

  var DIR = sec.getAttribute("data-img");
  var AW = D.aw, AH = D.ah, FOCAL = D.focal;
  var GREEN = "53,224,138";                          // --sig-green
  var SUN = D.sunC;                     // her sun on the artboard: centre, radius
  var SUN_DROP = D.sunDrop;                                // how far under her ridge it starts
  var HORIZON = D.horizon;                                 // the far ridges' crest
  var FLOOR = 0.2;                                   // the light that reaches a field's far corner
  var NIGHT = [24, 33, 48], DAWN_L = [122, 140, 160], DAWN_R = [186, 170, 140];   // what the picture is multiplied by
  var REACTOR = D.reactor;
  var SKY = D.sky, SUN_RECT = D.sun;

  var run = sec.querySelector(".vlb-run");
  var stage = sec.querySelector(".vlb-stage");
  var art = sec.querySelector(".vlb-art");
  var words = sec.querySelector(".vlb-sky");
  var line = sec.querySelector(".vlb-line"), gloss = sec.querySelector(".vlb-gloss");
  var mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  // mock only: ?vlb=0.4&only=d holds the camera at that point, for screenshots
  var qs = new URLSearchParams(location.search);
  var FORCE = qs.get("only") === "e" ? parseFloat(qs.get("vlb")) : NaN;

  var RECT = { "sky-night": SKY, "sky-dawn": SKY, sun: SUN_RECT, land: D.land, close: D.close, reactor: REACTOR };
  var imgs = [].slice.call(sec.querySelectorAll(".vlb-layer"));
  var L = {};
  imgs.forEach(function (el) { L[el.getAttribute("data-layer")] = el; });

  /* ---- the farms ---- */
  var maxD = 0;
  var farms = D.dots.map(function (d, i) {
    var dx = d[0] - FOCAL[0], dy = (d[1] - FOCAL[1]) * 1.6, dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > maxD) maxD = dist;
    return { x: d[0], y: d[1], ax: d[3], ay: d[4], w: d[5], h: d[6], px: d[7], py: d[8], reach: d[9], rh: d[10],
             sq: d[11] || 0.5, pool: true, alpha: 1,
             dist: dist, hero: i === D.hero, ph: Math.random() * 6.283, sp: 0.7 + Math.random() * 0.6, a: 0 };
  });
  farms.forEach(function (f) { f.at = f.hero ? -1 : 0.05 + 0.72 * Math.pow(f.dist / maxD, 0.85); });
  // the far fields: a reactor's glow and nothing else, lit last, her back row first and the skyline last
  D.far.forEach(function (d) {
    var depth = (d[1] - D.plain) / (D.backRow - D.plain);        // 1 at her back row, 0 at the horizon
    farms.push({ x: d[0], y: d[1], rh: d[2], alpha: d[3], pool: false, hero: false, dist: 0,
                 at: 0.6 + 0.3 * Math.pow(1 - depth, 0.8), ph: Math.random() * 6.283, sp: 0.7 + Math.random() * 0.6, a: 0 });
  });

  /* ---- what the script adds ---- */
  function el(tag, cls) { var e = document.createElement(tag); e.className = cls; if (tag === "canvas") e.setAttribute("aria-hidden", "true"); return e; }
  var lm = el("canvas", "vld-light"), lg = lm.getContext("2d");       // multiplied onto the picture
  var cv = el("canvas", "vlb-glows"), g = cv.getContext("2d");
  var halo = el("div", "vlb-halo"), vig = el("div", "vlb-vig"), grain = el("div", "vlb-grain");

  function radial(stops) {
    var c = document.createElement("canvas"); c.width = c.height = 128;
    var s = c.getContext("2d"), gr = s.createRadialGradient(64, 64, 0, 64, 64, 64);
    stops.forEach(function (st) { gr.addColorStop(st[0], st[1]); });
    s.fillStyle = gr; s.fillRect(0, 0, 128, 128);
    return c;
  }
  var sprite = radial([[0, "rgba(255,255,255,1)"], [0.12, "rgba(235,255,240,1)"], [0.26, "rgba(" + GREEN + ",.9)"],
                       [0.55, "rgba(" + GREEN + ",.3)"], [1, "rgba(" + GREEN + ",0)"]]);
  var flare = radial([[0, "rgba(255,244,214,.9)"], [0.18, "rgba(255,226,170,.5)"], [0.5, "rgba(255,206,140,.16)"], [1, "rgba(255,200,130,0)"]]);
  var lamp = radial([[0, "rgba(255,214,150,.85)"], [0.35, "rgba(250,190,120,.32)"], [1, "rgba(246,180,110,0)"]]);

  (function () {       // paper grain, so her brushwork keeps its tooth
    var c = document.createElement("canvas"); c.width = c.height = 128;
    var x = c.getContext("2d"), im = x.createImageData(128, 128), d = im.data;
    for (var i = 0; i < d.length; i += 4) {
      var v = Math.random();
      d[i] = d[i + 1] = d[i + 2] = v > 0.5 ? 255 : 0;
      d[i + 3] = Math.abs(v - 0.5) * 40;
    }
    x.putImageData(im, 0, 0);
    grain.style.backgroundImage = "url(" + c.toDataURL() + ")";
  })();

  /* ---- the pools: each field's shape, filled with light that falls off ----
     A pool is drawn onto the night as "how much of the picture shows here":
     nearly all of it at the reactor (a little green), FLOOR of the way at the
     field's far corner. k is the picture's scale in the sheet. */
  function lightUp(x, cx, cy, reach, k, rx, ry, rw, rh, sq) {
    var R = 0.62 * reach * 2.3 * k, t, gr;
    x.save();
    x.beginPath(); x.rect(rx, ry, rw, rh); x.clip();
    x.translate(cx, cy); x.scale(1, sq || 0.5);             // the ground is foreshortened, more so farther away
    x.globalCompositeOperation = "source-atop";             // colour: bright by the reactor, dimmer away
    gr = x.createRadialGradient(0, 0, 0, 0, 0, R);
    for (t = 0; t <= 1.0001; t += 0.125) {
      var b = 0.66 + 0.34 * Math.exp(-5.29 * t * t);
      gr.addColorStop(Math.min(t, 1), "rgb(" + Math.round(196 * b) + "," + Math.round(255 * b) + "," + Math.round(218 * b) + ")");
    }
    x.fillStyle = gr; x.fillRect(-6000, -6000, 12000, 12000);
    x.globalCompositeOperation = "destination-in";          // and how far it reaches
    gr = x.createRadialGradient(0, 0, 0, 0, 0, R);
    for (t = 0; t <= 1.0001; t += 0.125) gr.addColorStop(Math.min(t, 1), "rgba(0,0,0," + (FLOOR + (1 - FLOOR) * Math.exp(-5.29 * t * t)).toFixed(3) + ")");
    x.fillStyle = gr; x.fillRect(-6000, -6000, 12000, 12000);
    x.restore();
  }
  var atlas = null, heroPool = null, landMask = null, ready = false;
  function load(name, done) {
    var im = new Image(); im.decoding = "async";
    im.onload = function () { try { done(im); } catch (err) { fail(); } checkReady(); };
    im.onerror = fail;
    return function () { im.src = DIR + "/" + name; };
  }
  var loaders = [
    load("masks.webp", function (im) {
      var c = document.createElement("canvas"); c.width = im.naturalWidth; c.height = im.naturalHeight;
      var x = c.getContext("2d"); x.drawImage(im, 0, 0);
      farms.forEach(function (f) { if (f.pool) lightUp(x, f.ax + Math.min(f.x, AW - 1) - f.px, f.ay + f.y - f.py, f.reach, 1, f.ax, f.ay, f.w, f.h, f.sq); });
      atlas = c;
    }),
    load("hero-mask.webp", function (im) {                  // the first field again at 5x, for the opening frame
      var c = document.createElement("canvas"); c.width = im.naturalWidth; c.height = im.naturalHeight;
      var x = c.getContext("2d"), k = c.width / D.close[2], f = farms[D.hero];
      x.drawImage(im, 0, 0);
      lightUp(x, (f.x - D.close[0]) * k, (f.y - D.close[1]) * k, f.reach, k, 0, 0, c.width, c.height, f.sq);
      heroPool = c;
    }),
    load("land-mask.webp", function (im) { landMask = im; })
  ];
  function checkReady() {
    if (ready || !atlas || !heroPool || !landMask) return;
    ready = true; shown = -2;
    sec.classList.add("is-ready");
    request();
  }

  function clamp01(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
  function ease(t) { t = clamp01(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function smooth(t) { t = clamp01(t); return t * t * (3 - 2 * t); }
  function mix(a, b, t) { return "rgb(" + Math.round(a[0] + (b[0] - a[0]) * t) + "," + Math.round(a[1] + (b[1] - a[1]) * t) + "," + Math.round(a[2] + (b[2] - a[2]) * t) + ")"; }
  function place(e, r) { e.style.left = r[0] + "px"; e.style.top = r[1] + "px"; e.style.width = r[2] + "px"; e.style.height = r[3] + "px"; }

  /* ---- layout: the first and last frames for this stage ---- */
  var M = {}, still = false, dpr = 1;
  function layout() {
    var sw = stage.clientWidth, sh = stage.clientHeight;
    if (!sw || !sh) return false;
    M.sw = sw; M.sh = sh; M.phone = sw < sh;
    // last frame: the valley covers the stage; a tall screen sees part of its
    // width, moved right until her sun is in the frame
    var s1 = Math.max(sw / AW, sh / AH), win = sw / s1;
    var x0 = (AW - win) / 2, sunRight = SUN[0] + SUN[2] + 44;
    if (x0 + win < sunRight) x0 = sunRight - win;
    x0 = Math.max(Math.min(x0, FOCAL[0] - 60, AW - win), 0);
    var wordsEnd = words.offsetTop + words.offsetHeight;
    var ty = Math.min(0, Math.max(sh - AH * s1, wordsEnd + 20 - HORIZON * s1));
    M.s1 = s1; M.f1x = (FOCAL[0] - x0) * s1; M.f1y = ty + FOCAL[1] * s1;
    M.s0 = Math.max(sw / (M.phone ? D.closeW * 170 / 330 : D.closeW), s1 * 3);
    M.f0x = sw * 0.5; M.f0y = sh * (M.phone ? 0.52 : 0.56);
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    [cv, lm].forEach(function (c) { c.width = Math.round(sw * dpr); c.height = Math.round(sh * dpr); });
    art.style.width = AW + "px"; art.style.height = AH + "px";
    imgs.forEach(function (e) { place(e, RECT[e.getAttribute("data-layer")]); });
    place(halo, [FOCAL[0] - 24, FOCAL[1] - 18, 48, 36]);
    return true;
  }

  /* ---- one frame at progress p (0 close at night, 1 the valley at first light) ---- */
  var shown = -1;
  function frame(p, now) {
    var e = smooth((p - 0.02) / 0.86);               // the camera: it answers the first touch of the scroll
    var s = M.s0 * Math.pow(M.s1 / M.s0, e);
    var fx = M.f0x + (M.f1x - M.f0x) * e, fy = M.f0y + (M.f1y - M.f0y) * e;
    var tx = fx - FOCAL[0] * s, ty = fy - FOCAL[1] * s;
    art.style.transform = "translate3d(" + tx.toFixed(2) + "px," + ty.toFixed(2) + "px,0) scale(" + s.toFixed(5) + ")";

    // first light comes up while the camera pulls back
    var dawn = smooth((p - 0.12) / 0.7), sun = smooth((p - 0.2) / 0.72);
    L["sky-dawn"].style.opacity = dawn.toFixed(3);
    L.sun.style.transform = "translate3d(0," + ((1 - sun) * SUN_DROP).toFixed(2) + "px,0)";
    var closeA = clamp01((s / M.s1 - 2) / 2);
    L.close.style.opacity = closeA.toFixed(3);
    var rxA = clamp01((REACTOR[3] * s - 34) / 30);   // her reactor is large enough to read
    halo.style.opacity = (rxA * (1 - 0.6 * dawn)).toFixed(3);

    var va = 1 - smooth(e / 0.3);
    vig.style.opacity = va.toFixed(3);
    if (va > 0) vig.style.background = "radial-gradient(circle at " + fx.toFixed(0) + "px " + fy.toFixed(0) + "px, rgb(4 8 10 / 0) " + (0.09 * M.sw).toFixed(0) + "px, rgb(4 8 10 / .5) " + (0.22 * M.sw + 40).toFixed(0) + "px, rgb(4 8 10 / .88) " + (0.44 * M.sw + 120).toFixed(0) + "px)";

    for (var i = 0; i < farms.length; i++) farms[i].a = farms[i].hero ? 1 : clamp01((e - farms[i].at) / 0.07);

    var a1 = smooth((p - 0.72) / 0.14), a2 = smooth((p - 0.8) / 0.14);
    line.style.opacity = a1.toFixed(3); line.style.transform = "translateY(" + ((1 - a1) * 14).toFixed(1) + "px)";
    gloss.style.opacity = a2.toFixed(3); gloss.style.transform = "translateY(" + ((1 - a2) * 10).toFixed(1) + "px)";
    sec.classList.toggle("is-lit", p > 0.94);

    if (ready) light(s, tx, ty, dawn, sun, closeA);
    glows(s, tx, ty, rxA, dawn, sun, now);
    G = [s, tx, ty, rxA, dawn, sun];
    shown = p;
  }

  /* the light: night, the pools, first light; cut to the land */
  function light(s, tx, ty, dawn, sun, closeA) {
    lg.setTransform(dpr, 0, 0, dpr, 0, 0);
    lg.globalCompositeOperation = "source-over"; lg.globalAlpha = 1;
    lg.clearRect(0, 0, M.sw, M.sh);
    // first light reaches the sun's side of the valley first
    var gr = lg.createLinearGradient(tx, 0, tx + AW * s, 0);
    gr.addColorStop(0, mix(NIGHT, DAWN_L, dawn * (0.7 + 0.3 * sun)));
    gr.addColorStop(0.55, mix(NIGHT, DAWN_L, dawn));
    gr.addColorStop(1, mix(NIGHT, DAWN_R, Math.min(1, dawn * (1 + 0.25 * sun))));
    lg.fillStyle = gr; lg.fillRect(0, 0, M.sw, M.sh);
    var strength = 1 - 0.22 * dawn;
    for (var i = 0; i < farms.length; i++) {
      var f = farms[i], a = smooth(f.a) * strength;
      if (!f.pool || a <= 0.004) continue;
      if (f.hero && closeA > 0) {                           // sharp while the camera is close
        lg.globalAlpha = a * closeA;
        lg.drawImage(heroPool, tx + D.close[0] * s, ty + D.close[1] * s, D.close[2] * s, D.close[3] * s);
        a *= 1 - closeA;
        if (a <= 0.004) continue;
      }
      var x = tx + f.px * s, y = ty + f.py * s, w = f.w * s, h = f.h * s;
      if (x > M.sw || y > M.sh || x + w < 0 || y + h < 0) continue;
      lg.globalAlpha = a;
      lg.drawImage(atlas, f.ax, f.ay, f.w, f.h, x, y, w, h);
    }
    lg.globalAlpha = 1;
    lg.globalCompositeOperation = "destination-in";
    lg.drawImage(landMask, tx + D.land[0] * s, ty + D.land[1] * s, D.land[2] * s, D.land[3] * s);
    lg.globalCompositeOperation = "source-over";
  }

  /* the glows: the reactors, the windows, the sun's flare, and a few egrets at dawn */
  var glowAt = 0;
  var BIRDS = [[0, 0], [-34, 9], [-30, -12], [-66, 4], [-70, 22], [-104, -6]];
  function glows(s, tx, ty, rxA, dawn, sun, now) {
    glowAt = now;
    var t = now / 1000, i;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.globalCompositeOperation = "source-over"; g.globalAlpha = 1;
    g.clearRect(0, 0, M.sw, M.sh);
    g.globalCompositeOperation = "lighter";
    if (sun > 0.01) {
      var fr = 330 * s, sx = tx + SUN[0] * s, sy = ty + (SUN[1] + (1 - sun) * SUN_DROP * 0.6) * s;
      g.globalAlpha = 0.42 * sun * sun;
      g.drawImage(flare, sx - fr, sy - fr, 2 * fr, 2 * fr);
      // warm haze where the valley meets the mountains
      g.globalAlpha = 0.2 * dawn;
      g.drawImage(flare, tx + 300 * s, ty + (D.plain - 150) * s, (AW - 300) * s * 1.3, 300 * s);
    }
    // the houses' windows, until day
    var wa = ready ? 1 - 0.9 * dawn : 0;
    if (wa > 0.02) {
      for (i = 0; i < D.windows.length; i++) {
        var w = D.windows[i], wx = tx + w[0] * s, wy = ty + w[1] * s, ww = w[2] * s, wh = w[3] * s;
        if (wx > M.sw || wy > M.sh || wx + ww < 0 || wy + wh < 0) continue;
        g.globalAlpha = wa; g.fillStyle = "rgb(246,207,148)";
        g.fillRect(wx, wy, ww, wh);
        var lr = Math.max(ww, wh) * 2.6;
        g.globalAlpha = wa * 0.6;
        g.drawImage(lamp, wx + ww / 2 - lr, wy + wh / 2 - lr, 2 * lr, 2 * lr);
      }
    }
    for (i = 0; i < farms.length; i++) {
      var f = farms[i];
      if (f.a <= 0) continue;
      var big = f.hero ? rxA : 0;                           // her large drawing glows by itself
      if (big >= 1) continue;
      var x = tx + f.x * s, y = ty + f.y * s;
      var R = Math.max(0.62 * f.rh * s, f.pool ? 4.2 : 1.6) * (still ? 1 : 1 + 0.09 * Math.sin(t * f.sp + f.ph));
      if (f.a < 1) R *= 1 + 0.9 * Math.sin(Math.PI * f.a);  // comes on with a flare
      if (x + R < 0 || x - R > M.sw || y + R < 0 || y - R > M.sh) continue;
      g.globalAlpha = (1 - big) * f.a * f.alpha * (1 - 0.1 * dawn);
      g.drawImage(sprite, x - R, y - R, 2 * R, 2 * R);
    }
    // egrets leave the paddies as day comes
    if (!still && dawn > 0.55) {
      g.globalCompositeOperation = "source-over";
      g.globalAlpha = (dawn - 0.55) / 0.45 * 0.9;
      g.strokeStyle = "rgb(244,246,240)"; g.lineCap = "round"; g.lineWidth = Math.max(1.1, 1.6 * s);
      var bx = 150 + ((t * 22) % 1750), by = D.plain - 58 - 22 * Math.sin(bx / 420);   // low, in front of the mountains
      for (i = 0; i < BIRDS.length; i++) {
        var px = tx + (bx + BIRDS[i][0]) * s, py = ty + (by + BIRDS[i][1]) * s;
        var flap = Math.sin(t * 5.2 + i * 1.3) * 3.4 * s, span = 7.5 * s;
        g.beginPath(); g.moveTo(px - span, py - flap); g.quadraticCurveTo(px - span * 0.4, py - flap * 0.2 - 1.2 * s, px, py);
        g.quadraticCurveTo(px + span * 0.4, py - flap * 0.2 - 1.2 * s, px + span, py - flap); g.stroke();
      }
    }
    g.globalAlpha = 1;
    g.globalCompositeOperation = "source-over";
  }

  /* ---- the loop ---- */
  var p = -1, target = 0, last = 0, queued = false, dead = false, dirty = true, TAU = 170;
  function readTarget() {
    var r = run.getBoundingClientRect(), vh = window.innerHeight;
    var navTop = parseFloat(getComputedStyle(stage).top) || 0;
    var travel = r.height - M.sh;
    target = still ? 1 : travel > 0 ? clamp01((navTop - r.top) / travel) : 1;
    if (FORCE === FORCE) { target = FORCE; p = FORCE; }
    return r.bottom > -40 && r.top < vh + 40;
  }
  function tick(now) {
    queued = false;
    if (dead) return;
    try {
      if (dirty) { if (!layout()) return; dirty = false; shown = -2; }
      var on = readTarget();
      var dt = last ? Math.min(64, now - last) : 16;
      last = now;
      if (!on || p < 0 || still) p = target;
      else {
        p += (target - p) * (1 - Math.exp(-dt / TAU));
        if (Math.abs(target - p) < 0.0004) p = target;
      }
      if (shown !== p) frame(p, now);
      else if (on && !still && now - glowAt > 33) glowsOnly(now);
      if (p !== target || (on && !still && !document.hidden)) request();
      else last = 0;
    } catch (err) { fail(); }
  }
  // between scrolls only the glows move: the picture and its light stand
  var G = null;
  function glowsOnly(now) { if (G) glows(G[0], G[1], G[2], G[3], G[4], G[5], now); }
  function request() { if (!queued && !dead) { queued = true; requestAnimationFrame(tick); } }

  // anything wrong: take the additions out, and the CSS's last frame stays
  function fail() {
    if (dead) return;
    dead = true;
    sec.classList.remove("is-live", "is-lit", "is-still", "is-ready");
    [lm, halo, cv, grain, vig].forEach(function (e) { if (e.parentNode) e.parentNode.removeChild(e); });
    art.removeAttribute("style");
    imgs.forEach(function (e) { e.style.cssText = e.getAttribute("data-static") || ""; });
    [line, gloss].forEach(function (e) { if (e) e.removeAttribute("style"); });
  }

  function setMode() {
    still = mq.matches;
    sec.classList.add("is-live");
    sec.classList.toggle("is-still", still);
    dirty = true; p = -1; last = 0;
    request();
  }

  try {
    if (!("mixBlendMode" in lm.style)) return;              // no multiply: leave the CSS's first light
    imgs.forEach(function (e) { e.setAttribute("data-static", e.style.cssText); });
    L.close.insertAdjacentElement("afterend", halo);        // under her reactor
    art.insertAdjacentElement("afterend", lm);
    lm.insertAdjacentElement("afterend", vig);
    vig.insertAdjacentElement("afterend", cv);
    cv.insertAdjacentElement("afterend", grain);
    setMode();
  } catch (err) { fail(); return; }

  window.addEventListener("scroll", request, { passive: true });
  window.addEventListener("resize", function () { dirty = true; request(); });
  if (window.ResizeObserver) new ResizeObserver(function () { dirty = true; request(); }).observe(stage);
  document.addEventListener("visibilitychange", request);
  if (mq.addEventListener) mq.addEventListener("change", setMode);

  function eager() {
    imgs.forEach(function (e) { e.loading = "eager"; });
    loaders.forEach(function (go) { go(); });
  }
  if ("IntersectionObserver" in window) {
    var near = new IntersectionObserver(function (es) {
      if (es.some(function (x) { return x.isIntersecting; })) { near.disconnect(); eager(); }
    }, { rootMargin: "200% 0px" });
    near.observe(sec);
  } else eager();
})();
