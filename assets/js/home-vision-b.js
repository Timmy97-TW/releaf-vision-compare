/* =============================================================================
   VISION, STUDENT VERSION (mock, 2 Oct 2026): "Every farmer a biomanufacturer."

   The student's hand-drawn valley, lit by this script. build/vision-student.py
   cuts her painting into layers (assets/img/home/vision-student/) and writes
   home-vision-b-data.js, which this file reads as window.__vlbData.

   THE STORY, IN SCROLL ORDER
   1. Night, close on one field. Her reactor stands in it, and its light shows
      that field in her own colours; everything else is dark.
   2. The camera pulls back. Each farm's reactor comes on as it enters the
      frame, and each lights its own field and no other.
   3. With the whole valley in frame, first light: her sky warms, her sun
      rises from behind her ridge, and the line lands on the sky.

   HOW IT MOVES
   One transform on the artboard (2048 x 1552 px), opacities on the dawn
   layers, one transform on the sun. Two canvases: the pools of light (inside
   the artboard, redrawn only when a farm comes on) and the glows (the size of
   the stage, a soft sprite per reactor). The scroll only sets a target; each
   frame eases towards it.

   Without script, home-vision-b.css shows the valley at first light. With
   reduced motion this script draws the last frame, pools and glows on, and
   never moves it. If anything throws, it takes its additions out.
   ========================================================================== */

(function () {
  "use strict";

  var D = window.__vlbData;
  var sec = document.getElementById("vision-b");
  if (!sec || !D) return;

  var AW = D.aw, AH = D.ah, FOCAL = D.focal, K = D.poolK;
  var GREEN = "53,224,138";                          // --sig-green
  var RAD = { 15: 11, 32: 18, 73: 27 };               // glow radius for her three dot sizes
  var SUN_DROP = 185;                                // how far under her ridge the sun starts
  var HORIZON = 770;                                 // the far ridges' crest on the artboard

  var run = sec.querySelector(".vlb-run");
  var stage = sec.querySelector(".vlb-stage");
  var art = sec.querySelector(".vlb-art");
  var words = sec.querySelector(".vlb-sky");
  var line = sec.querySelector(".vlb-line"), gloss = sec.querySelector(".vlb-gloss");
  var label = sec.querySelector(".vlb-rx");
  var mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  // mock only: ?vlb=0.4 holds the camera at that point, for screenshots
  var FORCE = parseFloat(new URLSearchParams(location.search).get("vlb"));

  var RECT = { "sky-night": D.sky, "sky-dawn": D.sky, sun: D.sun, "land-night": D.land, "land-dawn": D.land, close: D.close, reactor: D.reactor };
  var imgs = [].slice.call(sec.querySelectorAll(".vlb-layer"));
  var L = {};
  imgs.forEach(function (el) { L[el.getAttribute("data-layer")] = el; });

  /* ---- the farms ---- */
  var maxD = 0;
  var farms = D.dots.map(function (d, i) {
    var dx = d[0] - FOCAL[0], dy = (d[1] - FOCAL[1]) * 1.6, dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > maxD) maxD = dist;
    return { x: d[0], y: d[1], r: RAD[d[2]], ax: d[3], ay: d[4], w: d[5], h: d[6], px: d[7], py: d[8], reach: d[9],
             dist: dist, hero: i === D.hero, ph: Math.random() * 6.283, sp: 0.7 + Math.random() * 0.6, a: 0 };
  });
  // each comes on a moment after the camera has pulled back far enough to
  // bring it in: the nearer to the first field, the sooner
  farms.forEach(function (f) { f.at = f.hero ? -1 : 0.08 + 0.8 * Math.pow(f.dist / maxD, 0.85); });
  var POOL_Y = farms.reduce(function (m, f) { return Math.min(m, f.py); }, AH);

  /* ---- what the script adds ---- */
  var pools = document.createElement("canvas"); pools.className = "vlb-pools";
  pools.width = Math.round(AW * K); pools.height = Math.round((AH - POOL_Y) * K);
  var pg = pools.getContext("2d");
  var halo = document.createElement("div"); halo.className = "vlb-halo";      // the first reactor's own light
  var cv = document.createElement("canvas"); cv.className = "vlb-glows"; cv.setAttribute("aria-hidden", "true");
  var g = cv.getContext("2d");
  var grain = document.createElement("div"); grain.className = "vlb-grain";
  // the opening frame's dark: the first reactor's light dies away across its field
  var vig = document.createElement("div"); vig.className = "vlb-vig";

  function radial(stops) {
    var c = document.createElement("canvas"); c.width = c.height = 128;
    var s = c.getContext("2d"), gr = s.createRadialGradient(64, 64, 0, 64, 64, 64);
    stops.forEach(function (st) { gr.addColorStop(st[0], st[1]); });
    s.fillStyle = gr; s.fillRect(0, 0, 128, 128);
    return c;
  }
  // a reactor: a white-hot core in reactor green, fading out
  var sprite = radial([[0, "rgba(255,255,255,1)"], [0.1, "rgba(235,255,240,1)"], [0.22, "rgba(" + GREEN + ",.95)"],
                       [0.5, "rgba(" + GREEN + ",.34)"], [1, "rgba(" + GREEN + ",0)"]]);
  // the sun's flare over her ridge
  var flare = radial([[0, "rgba(255,244,214,.9)"], [0.18, "rgba(255,226,170,.5)"], [0.5, "rgba(255,206,140,.16)"], [1, "rgba(255,200,130,0)"]]);

  // paper grain over the picture, so her brushwork keeps its tooth on a sharp screen
  (function () {
    var c = document.createElement("canvas"); c.width = c.height = 128;
    var x = c.getContext("2d"), im = x.createImageData(128, 128), d = im.data;
    for (var i = 0; i < d.length; i += 4) {
      var v = Math.random();
      d[i] = d[i + 1] = d[i + 2] = v > 0.5 ? 255 : 0;
      d[i + 3] = Math.abs(v - 0.5) * 44;
    }
    x.putImageData(im, 0, 0);
    grain.style.backgroundImage = "url(" + c.toDataURL() + ")";
  })();

  /* ---- the pools: her field colours, fading out from each reactor ----
     pools.webp holds each field's shape and colours; the light's fall-off is
     put on here, once, as floor + (1 - floor) exp(-(d / (0.62 reach))^2). */
  var atlas = null, atlasImg = new Image();
  atlasImg.decoding = "async";
  atlasImg.onload = function () {
    try {
      var c = document.createElement("canvas"); c.width = atlasImg.naturalWidth; c.height = atlasImg.naturalHeight;
      var x = c.getContext("2d");
      x.drawImage(atlasImg, 0, 0);
      x.globalCompositeOperation = "destination-in";
      farms.forEach(function (f) {
        var R = 0.62 * f.reach * 2.3 * K;
        x.save();
        x.beginPath(); x.rect(f.ax * K, f.ay * K, f.w * K, f.h * K); x.clip();
        x.translate((f.ax + Math.min(f.x, AW - 1) - f.px) * K, (f.ay + f.y - f.py) * K);
        x.scale(1, 0.5);                                   // the ground is foreshortened
        var gr = x.createRadialGradient(0, 0, 0, 0, 0, R);
        for (var t = 0; t <= 1.0001; t += 0.1) gr.addColorStop(Math.min(t, 1), "rgba(0,0,0," + (D.floor + (1 - D.floor) * Math.exp(-5.29 * t * t)).toFixed(3) + ")");
        x.fillStyle = gr; x.fillRect(-4000, -4000, 8000, 8000);
        x.restore();
      });
      atlas = c; poolKey = ""; shown = -2; request();
    } catch (err) { /* the pools are an extra; the glows still say it */ }
  };

  function clamp01(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
  function ease(t) { t = clamp01(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function smooth(t) { t = clamp01(t); return t * t * (3 - 2 * t); }
  function place(el, r) { el.style.left = r[0] + "px"; el.style.top = r[1] + "px"; el.style.width = r[2] + "px"; el.style.height = r[3] + "px"; }

  /* ---- layout: the first and last frames for this stage ---- */
  var M = {}, still = false, dpr = 1;
  function layout() {
    var sw = stage.clientWidth, sh = stage.clientHeight;
    if (!sw || !sh) return false;
    M.sw = sw; M.sh = sh; M.phone = sw < sh;
    // last frame: the valley covers the stage. A tall screen sees part of its
    // width: centred, or moved right until her sun is in the frame.
    var s1 = Math.max(sw / AW, sh / AH), win = sw / s1;
    var x0 = (AW - win) / 2, sunRight = D.sunC[0] + D.sunC[2] + 44;
    if (x0 + win < sunRight) x0 = sunRight - win;
    x0 = Math.max(Math.min(x0, FOCAL[0] - 60, AW - win), 0);
    // its foot on the stage's foot, unless that would put the ridges behind the words
    var wordsEnd = words.offsetTop + words.offsetHeight;
    var ty = Math.min(0, Math.max(sh - AH * s1, wordsEnd + 20 - HORIZON * s1));
    M.s1 = s1; M.f1x = (FOCAL[0] - x0) * s1; M.f1y = ty + FOCAL[1] * s1;
    // first frame: about 330 px of her drawing across a wide screen, 170 on a phone
    M.s0 = Math.max(sw / (M.phone ? 170 : 330), s1 * 3);
    M.f0x = sw * 0.5; M.f0y = sh * (M.phone ? 0.52 : 0.56);
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    cv.width = Math.round(sw * dpr); cv.height = Math.round(sh * dpr);
    art.style.width = AW + "px"; art.style.height = AH + "px";
    imgs.forEach(function (el) { place(el, RECT[el.getAttribute("data-layer")]); });
    place(pools, [0, POOL_Y, AW, AH - POOL_Y]);
    place(halo, [FOCAL[0] - 34, FOCAL[1] - 26, 68, 52]);
    return true;
  }

  /* ---- one frame at progress p (0 close at night, 1 the valley at first light) ---- */
  var shown = -1, poolKey = "";
  function frame(p, now) {
    var e = ease((p - 0.04) / 0.58);                 // the camera
    var s = M.s0 * Math.pow(M.s1 / M.s0, e);
    var fx = M.f0x + (M.f1x - M.f0x) * e, fy = M.f0y + (M.f1y - M.f0y) * e;
    var tx = fx - FOCAL[0] * s, ty = fy - FOCAL[1] * s;
    art.style.transform = "translate3d(" + tx.toFixed(2) + "px," + ty.toFixed(2) + "px,0) scale(" + s.toFixed(5) + ")";

    // first light: the sky, then the land, then the sun over the ridge
    var dawn = smooth((p - 0.5) / 0.4), sun = smooth((p - 0.56) / 0.42);
    L["sky-dawn"].style.opacity = dawn.toFixed(3);
    L["land-dawn"].style.opacity = smooth((p - 0.54) / 0.38).toFixed(3);
    L.sun.style.transform = "translate3d(0," + ((1 - sun) * SUN_DROP).toFixed(2) + "px,0)";
    pools.style.opacity = (1 - 0.18 * dawn).toFixed(3);

    // the enlarged first field, only while it is sharper than the valley
    var closeA = clamp01((s / M.s1 - 2) / 2);
    L.close.style.opacity = closeA.toFixed(3);
    // her reactor, until it is too small to read; then its glow
    var rxA = clamp01((L.reactor.offsetHeight * s - 34) / 30);
    L.reactor.style.opacity = rxA.toFixed(3);
    halo.style.opacity = rxA.toFixed(3);
    var va = 1 - smooth(e / 0.3);
    vig.style.opacity = va.toFixed(3);
    if (va > 0) vig.style.background = "radial-gradient(circle at " + fx.toFixed(0) + "px " + fy.toFixed(0) + "px, rgb(4 8 10 / 0) " + (0.07 * M.sw).toFixed(0) + "px, rgb(4 8 10 / .55) " + (0.2 * M.sw + 40).toFixed(0) + "px, rgb(4 8 10 / .9) " + (0.42 * M.sw + 120).toFixed(0) + "px)";

    // the farms come on
    var key = closeA.toFixed(2);
    for (var i = 0; i < farms.length; i++) {
      var f = farms[i];
      f.a = f.hero ? 1 : clamp01((e - f.at) / 0.06);
      key += (f.a * 20 | 0);
    }
    if (atlas && key !== poolKey) {
      poolKey = key;
      pg.clearRect(0, 0, pools.width, pools.height);
      for (i = 0; i < farms.length; i++) {
        f = farms[i];
        var a = smooth(f.a) * (f.hero ? 1 - closeA : 1);   // the first field's pool is in the close-up
        if (a <= 0.004) continue;
        pg.globalAlpha = a;
        pg.drawImage(atlas, f.ax * K, f.ay * K, f.w * K, f.h * K, f.px * K, (f.py - POOL_Y) * K, f.w * K, f.h * K);
      }
      pg.globalAlpha = 1;
    }

    if (label) {
      var la = 1 - smooth((p - 0.03) / 0.08);
      label.style.opacity = la.toFixed(3);
      // beside the reactor on a wide screen, under it on a phone
      var rw = L.reactor.offsetWidth * s, rh = L.reactor.offsetHeight * s;
      var lx = M.phone ? fx - label.offsetWidth / 2 : fx + rw * 0.5 + 16;
      var ly = M.phone ? fy + rh * 0.62 + 12 : fy - 10;
      label.style.transform = "translate3d(" + lx.toFixed(1) + "px," + ly.toFixed(1) + "px,0)";
    }
    var a1 = smooth((p - 0.84) / 0.09), a2 = smooth((p - 0.89) / 0.09);
    line.style.opacity = a1.toFixed(3); line.style.transform = "translateY(" + ((1 - a1) * 14).toFixed(1) + "px)";
    gloss.style.opacity = a2.toFixed(3); gloss.style.transform = "translateY(" + ((1 - a2) * 10).toFixed(1) + "px)";
    sec.classList.toggle("is-lit", p > 0.96);

    glows(s, tx, ty, rxA, dawn, sun, now);
    shown = p;
  }

  var glowAt = 0;
  function glows(s, tx, ty, rxA, dawn, sun, now) {
    glowAt = now;
    var t = now / 1000;
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.clearRect(0, 0, cv.width, cv.height);
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.globalCompositeOperation = "lighter";
    if (sun > 0.01) {                                      // the sun's flare spills over the ridge
      var fr = 330 * s, sx = tx + D.sunC[0] * s, sy = ty + (D.sunC[1] + (1 - sun) * SUN_DROP * 0.6) * s;
      g.globalAlpha = 0.42 * sun * sun;
      g.drawImage(flare, sx - fr, sy - fr, 2 * fr, 2 * fr);
    }
    for (var i = 0; i < farms.length; i++) {
      var f = farms[i];
      if (f.a <= 0 || (f.hero && rxA >= 1)) continue;      // the first field's glow takes over from her drawing
      var x = tx + f.x * s, y = ty + f.y * s;
      var R = Math.max(f.r * s, 4.5) * (still ? 1 : 1 + 0.08 * Math.sin(t * f.sp + f.ph));
      if (f.a < 1) R *= 1 + 0.9 * Math.sin(Math.PI * f.a);  // comes on with a flare
      if (x + R < 0 || x - R > M.sw || y + R < 0 || y - R > M.sh) continue;
      g.globalAlpha = (f.hero ? 1 - rxA : f.a) * (1 - 0.12 * dawn);
      g.drawImage(sprite, x - R, y - R, 2 * R, 2 * R);
    }
    g.globalAlpha = 1;
    g.globalCompositeOperation = "source-over";
  }

  /* ---- the loop ---- */
  var p = -1, target = 0, last = 0, queued = false, dead = false, dirty = true, TAU = 110;
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
      if (dirty) { if (!layout()) return; dirty = false; shown = -2; poolKey = ""; }
      var on = readTarget();
      var dt = last ? Math.min(64, now - last) : 16;
      last = now;
      if (!on || p < 0 || still) p = target;
      else {
        p += (target - p) * (1 - Math.exp(-dt / TAU));
        if (Math.abs(target - p) < 0.0004) p = target;
      }
      if (shown !== p) frame(p, now);
      else if (on && !still && now - glowAt > 33) frame(p, now);   // the glows breathe
      if (p !== target || (on && !still && !document.hidden)) request();
      else last = 0;
    } catch (err) { fail(); }
  }
  function request() { if (!queued && !dead) { queued = true; requestAnimationFrame(tick); } }

  // anything wrong: take the additions out, and the CSS's last frame stays
  function fail() {
    dead = true;
    sec.classList.remove("is-live", "is-lit", "is-still");
    [pools, halo, cv, grain, vig].forEach(function (el) { if (el.parentNode) el.parentNode.removeChild(el); });
    art.removeAttribute("style");
    imgs.forEach(function (el) { el.style.cssText = el.getAttribute("data-static") || ""; });
    [line, gloss, label].forEach(function (el) { if (el) el.removeAttribute("style"); });
  }

  function setMode() {
    still = mq.matches;
    sec.classList.add("is-live");
    sec.classList.toggle("is-still", still);
    dirty = true; p = -1; last = 0;
    request();
  }

  try {
    imgs.forEach(function (el) { el.setAttribute("data-static", el.style.cssText); });
    L.close.insertAdjacentElement("afterend", pools);
    pools.insertAdjacentElement("afterend", halo);          // under her reactor
    art.insertAdjacentElement("afterend", cv);
    cv.insertAdjacentElement("afterend", grain);
    art.insertAdjacentElement("afterend", vig);            // over the picture, under the glows
    setMode();
  } catch (err) { fail(); return; }

  window.addEventListener("scroll", request, { passive: true });
  window.addEventListener("resize", function () { dirty = true; request(); });
  if (window.ResizeObserver) new ResizeObserver(function () { dirty = true; request(); }).observe(stage);
  document.addEventListener("visibilitychange", request);
  if (mq.addEventListener) mq.addEventListener("change", setMode);

  // the pictures are lazy for the page's first load; fetch them properly
  // once the section is within two screens
  function eager() {
    imgs.forEach(function (el) { el.loading = "eager"; });
    atlasImg.src = "assets/img/home/vision-student/pools.webp";
  }
  if ("IntersectionObserver" in window) {
    var near = new IntersectionObserver(function (es) {
      if (es.some(function (x) { return x.isIntersecting; })) { near.disconnect(); eager(); }
    }, { rootMargin: "200% 0px" });
    near.observe(sec);
  } else eager();
})();
