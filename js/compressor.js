/* ============================================================
   The compressor, in three dimensions
   ------------------------------------------------------------
   A semi-hermetic four-cylinder reciprocating compressor, built here out of
   boxes and cylinders and shaded live. It is the same machine as the side
   elevation further down the page, built from the same numbers, so the object
   and its drawing agree -- the elevation is this thing seen from the side.

   Modelled from the published envelope of the BITZER 4Z-8.2Y: 673 long, 439
   high, 420 wide, four cylinders at 55 mm bore and 34 mm stroke. Those are
   measurements, and measurements are not authorship. No manufacturer artwork
   is reproduced, traced or shipped here, and no supplied CAD is used: the
   STEP file that came with the enquiry is a third party's model of a
   different maker's machine, and being an authorised service partner is a
   right to work on the compressor, not a licence to republish drawings of it.

   No library. The whole renderer is below: project, cull, sort, shade, draw.
   three.js would have been about 280 KB over the wire to draw eleven boxes
   and nine cylinders, on a site that hand-draws everything else it shows.
   ============================================================ */
(function () {
  "use strict";

  var root = document.querySelector("[data-compressor]");
  if (!root) return;
  var canvas = root.querySelector("canvas");
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext("2d");
  if (!ctx) return;

  /* ---------- geometry helpers ----------
     Everything is authored in the elevation's own units with Y measured up
     from the mounting feet, so a number here can be checked against the
     drawing without converting anything. */
  var V = [];            // vertices, flat [x,y,z, x,y,z, ...]
  var F = [];            // faces: {i: [indices], t: tone}

  function vert(x, y, z) { V.push(x, y, z); return V.length / 3 - 1; }

  function quad(a, b, c, d, t) { F.push({ i: [a, b, c, d], t: t }); }

  /* Winding decided the cull, and the two builders below did not agree about
     it: boxes came out solid and cylinders came out see-through, with the far
     wall of the motor housing painting over the near one. Rather than reason
     out a sign convention twice, every part hands its own centre to this and
     any face whose normal points back at that centre is reversed. After it
     runs, "outward" is a fact about the data, and the cull is one dot product
     with no convention to remember. */
  function orient(from, cx, cy, cz) {
    for (var k = from; k < F.length; k++) {
      var ix = F[k].i;
      var a = ix[0] * 3, b = ix[1] * 3, c = ix[2] * 3;
      var ux = V[b] - V[a], uy = V[b + 1] - V[a + 1], uz = V[b + 2] - V[a + 2];
      var vx = V[c] - V[a], vy = V[c + 1] - V[a + 1], vz = V[c + 2] - V[a + 2];
      var nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      var ox = V[a] - cx, oy = V[a + 1] - cy, oz = V[a + 2] - cz;
      if (nx * ox + ny * oy + nz * oz < 0) F[k].i = ix.slice().reverse();
    }
  }

  function box(x0, x1, y0, y1, z0, z1, t) {
    var p = [
      vert(x0, y0, z0), vert(x1, y0, z0), vert(x1, y1, z0), vert(x0, y1, z0),
      vert(x0, y0, z1), vert(x1, y0, z1), vert(x1, y1, z1), vert(x0, y1, z1)
    ];
    quad(p[0], p[1], p[2], p[3], t);   // front
    quad(p[5], p[4], p[7], p[6], t);   // back
    quad(p[4], p[0], p[3], p[7], t);   // left
    quad(p[1], p[5], p[6], p[2], t);   // right
    quad(p[3], p[2], p[6], p[7], t);   // top
    quad(p[4], p[5], p[1], p[0], t);   // bottom
    orient(F.length - 6, (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
    return p;
  }

  /* A cylinder lying along X -- which is every cylinder on this machine:
     the motor housing, its cooling ribs, the shaft boss and the pipe stubs. */
  function tubeX(x0, x1, cy, cz, r, seg, t, capL, capR) {
    var ring0 = [], ring1 = [], k, a, start = F.length;
    for (k = 0; k < seg; k++) {
      a = (k / seg) * Math.PI * 2;
      ring0.push(vert(x0, cy + Math.sin(a) * r, cz + Math.cos(a) * r));
      ring1.push(vert(x1, cy + Math.sin(a) * r, cz + Math.cos(a) * r));
    }
    for (k = 0; k < seg; k++) {
      var n = (k + 1) % seg;
      quad(ring0[k], ring0[n], ring1[n], ring1[k], t);
    }
    if (capL !== false) F.push({ i: ring0.slice().reverse(), t: t });
    if (capR !== false) F.push({ i: ring1.slice(), t: t });
    orient(start, (x0 + x1) / 2, cy, cz);
    return [ring0, ring1];
  }

  /* Across the machine rather than along it: the sight glass, the bosses on
     the parting line, and anything else that looks out of a side face. */
  function tubeZ(z0, z1, cx, cy, r, seg, t) {
    var ring0 = [], ring1 = [], k, a, start = F.length;
    for (k = 0; k < seg; k++) {
      a = (k / seg) * Math.PI * 2;
      ring0.push(vert(cx + Math.cos(a) * r, cy + Math.sin(a) * r, z0));
      ring1.push(vert(cx + Math.cos(a) * r, cy + Math.sin(a) * r, z1));
    }
    for (k = 0; k < seg; k++) {
      var n = (k + 1) % seg;
      quad(ring0[k], ring0[n], ring1[n], ring1[k], t);
    }
    F.push({ i: ring0.slice(), t: t });
    F.push({ i: ring1.slice(), t: t });
    orient(start, cx, cy, (z0 + z1) / 2);
  }

  /* The two cylinder banks stand in a V. Each hinges on its own inner base
     corner -- rotating both about one shared point is what put them through
     each other in an X when the elevation was first drawn. */
  function rotZAbout(from, px, py, deg) {
    var r = deg * Math.PI / 180, c = Math.cos(r), s = Math.sin(r), k;
    for (k = from; k < V.length; k += 3) {
      var x = V[k] - px, y = V[k + 1] - py;
      V[k]     = px + x * c - y * s;
      V[k + 1] = py + x * s + y * c;
    }
  }

  /* ---------- the machine ---------- */
  var STEEL = 0, DARK = 1, PIPE = 2;

  // mounting feet and the rail they sit on
  for (var bx = 110; bx < 740; bx += 105) {
    box(bx, Math.min(bx + 105, 740), -8, 0, -128, 128, DARK);
  }
  [150, 300, 560, 690].forEach(function (fx) {
    box(fx, fx + 50, 0, 26, -132, -104, DARK);
    box(fx, fx + 50, 0, 26, 104, 132, DARK);
  });

  // motor housing: a semi-hermetic motor shares the crankcase, so the housing
  // is a plain cylinder capped where it meets the block
  tubeX(96, 302, 135, 0, 111, 28, STEEL, true, false);
  // End cover and its bolt circle. Without them the cap is a single flat
  // ellipse, and the largest shape on the canvas is a blank one.
  tubeX(88, 96, 135, 0, 92, 28, DARK);
  tubeX(82, 88, 135, 0, 54, 22, STEEL);
  for (var bk = 0; bk < 8; bk++) {
    var ba = (bk / 8) * Math.PI * 2;
    tubeX(86, 94, 135 + Math.sin(ba) * 76, Math.cos(ba) * 76, 8, 8, STEEL);
  }
  for (var rx = 118; rx < 292; rx += 17) {          // cooling ribs
    tubeX(rx, rx + 5, 135, 0, 119, 28, STEEL, false, false);
  }
  box(172, 268, 246, 296, -50, 50, DARK);           // terminal box
  box(180, 260, 296, 302, -42, 42, STEEL);          // its lid

  // crankcase
  box(300, 640, 24, 202, -150, 150, STEEL);
  box(300, 640, 24, 30, -152, 152, DARK);           // sump joint
  tubeX(636, 664, 114, 0, 46, 24, STEEL);           // shaft end boss
  tubeX(660, 668, 114, 0, 20, 20, DARK);            // shaft stub
  // the parting line between crankcase and sump, and the bolts along it
  box(300, 640, 96, 104, -154, 154, DARK);
  for (var px = 322; px < 634; px += 39) {
    tubeZ(152, 160, px, 100, 7, 10, STEEL);
    tubeZ(-160, -152, px, 100, 7, 10, STEEL);
  }
  tubeZ(150, 162, 386, 62, 21, 18, DARK);           // oil sight glass
  tubeZ(150, 166, 386, 62, 12, 18, PIPE);
  box(470, 600, 40, 92, 150, 156, DARK);            // inspection cover
  for (var cx2 = 484; cx2 < 596; cx2 += 36) {
    tubeZ(156, 161, cx2, 46, 6, 8, STEEL);
    tubeZ(156, 161, cx2, 86, 6, 8, STEEL);
  }

  // the two banks of two cylinders, in V
  // Signs are the opposite of the elevation's: SVG measures Y down and this
  // measures Y up, so the same splay is the other way round. Written straight
  // across from the drawing, both banks leaned inward and crossed -- the exact
  // X the elevation's own comment warns about, reintroduced by the flip.
  [[374, 464, 464, 21], [476, 566, 476, -21]].forEach(function (b) {
    var start = V.length;
    box(b[0], b[1], 202, 318, -128, 128, STEEL);            // barrel
    box(b[0] - 10, b[1] + 10, 318, 344, -138, 138, DARK);   // head
    for (var hx = b[0] + 22; hx < b[1]; hx += 23) {         // head bolts
      box(hx, hx + 7, 344, 350, -132, -120, STEEL);
      box(hx, hx + 7, 344, 350, 120, 132, STEEL);
    }
    rotZAbout(start, b[2], 202, b[3]);
  });

  // suction, leaving the block on the right; discharge routed over the motor
  box(640, 706, 170, 220, -26, 26, PIPE);
  tubeX(700, 772, 195, 0, 26, 18, PIPE);
  box(278, 302, 208, 322, -22, 22, PIPE);
  tubeX(136, 292, 310, 0, 22, 18, PIPE);

  /* ---------- shading ----------
     Flat per-face lambert with a cool fill and a rim term. The palette is the
     site's own greys: there is no third hue anywhere on this page and the
     compressor is not going to be the first. */
  /* Silver. The blue-steel set read as part of the navy behind it rather than
     as metal standing in front of it; a machined casting is close to neutral
     and gets its colour from what it is reflecting. The barest cool cast is
     kept in the shadows -- fully neutral greys go muddy against this ground --
     and the highlight runs almost to white so the lit edges catch. */
  var TONE = [
    { base: [ 56,  59,  68], hi: [243, 244, 247] },   // STEEL
    { base: [ 28,  30,  37], hi: [146, 149, 158] },   // DARK
    { base: [ 46,  49,  58], hi: [219, 221, 227] }    // PIPE
  ];
  var LIGHT = norm([-0.42, 0.78, 0.46]);
  var FILL  = norm([0.6, -0.2, -0.7]);

  function norm(v) {
    var m = Math.hypot(v[0], v[1], v[2]) || 1;
    return [v[0] / m, v[1] / m, v[2] / m];
  }

  /* ---------- projection ---------- */
  var yaw = -0.62, pitch = 0.30, autoYaw = true;
  var CX = 422, CY = 168, CZ = 0;          // model centre, in model units
  var DIST = 1750, FOCAL = 2140;
  /* FOCAL was a constant, which is only ever right at one canvas width: the
     machine sat well in a 1392px stage and on a phone it was three times the
     canvas and ran off every edge. Tying it to the width keeps the machine at
     the same fraction of the frame everywhere; the narrow case backs off a
     little further to leave the callout columns somewhere to live. */
  function refocus() {
    FOCAL = W * (W < 620 ? 1.60 : 1.86);
  }

  function project(out) {
    var cy = Math.cos(yaw), sy = Math.sin(yaw);
    var cp = Math.cos(pitch), sp = Math.sin(pitch);
    for (var k = 0, j = 0; k < V.length; k += 3, j += 3) {
      var x = V[k] - CX, y = V[k + 1] - CY, z = V[k + 2] - CZ;
      var x1 =  x * cy + z * sy;
      var z1 = -x * sy + z * cy;
      var y2 =  y * cp - z1 * sp;
      var z2 =  y * sp + z1 * cp + DIST;
      out[j] = x1; out[j + 1] = y2; out[j + 2] = z2;
    }
  }

  var P = new Float64Array(V.length);
  var S = new Float64Array((V.length / 3) * 2);

  function shade(n) {
    var d  = Math.max(0, n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]);
    var f  = Math.max(0, n[0] * FILL[0]  + n[1] * FILL[1]  + n[2] * FILL[2]);
    // The rim is taken against the view axis, which after projection is simply
    // +Z: a face turned away from the camera catches the edge light.
    var rim = Math.pow(1 - Math.min(1, Math.abs(n[2])), 4);
    return 0.06 + d * 0.62 + f * 0.12 + rim * 0.34 + Math.pow(d, 22) * 0.55;
  }

  var order = [];
  for (var fi = 0; fi < F.length; fi++) order.push(fi);

  function draw(w, h, dpr) {
    project(P);
    var scale = FOCAL, k, j;
    for (k = 0, j = 0; k < P.length; k += 3, j += 2) {
      var pz = P[k + 2] || 1;
      S[j]     = P[k]     * scale / pz;
      S[j + 1] = -P[k + 1] * scale / pz;
    }

    // depth per face, then paint back to front
    var depth = new Float64Array(F.length);
    for (k = 0; k < F.length; k++) {
      var idx = F[k].i, d = 0;
      for (j = 0; j < idx.length; j++) d += P[idx[j] * 3 + 2];
      depth[k] = d / idx.length;
    }
    order.sort(function (a, b) { return depth[b] - depth[a]; });

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    ctx.translate(w / 2, h / 2 + h * 0.02);
    ctx.lineJoin = "round";

    for (var o = 0; o < order.length; o++) {
      var f = F[order[o]], ix = f.i, n = ix.length;
      // face normal in view space; orient() guarantees it points out of the
      // part, so a face is visible exactly when it leans back toward the eye
      var p0 = ix[0] * 3, p1 = ix[1] * 3, p2 = ix[2] * 3;
      var ux = P[p1] - P[p0], uy = P[p1 + 1] - P[p0 + 1], uz = P[p1 + 2] - P[p0 + 2];
      var vx = P[p2] - P[p0], vy = P[p2 + 1] - P[p0 + 1], vz = P[p2 + 2] - P[p0 + 2];
      var nn = norm([uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx]);
      if (nn[0] * P[p0] + nn[1] * P[p0 + 1] + nn[2] * P[p0 + 2] >= 0) continue;
      var ax = S[ix[0] * 2], ay = S[ix[0] * 2 + 1];
      var t = TONE[f.t], L = shade(nn);
      var r = Math.round(t.base[0] + (t.hi[0] - t.base[0]) * L);
      var g = Math.round(t.base[1] + (t.hi[1] - t.base[1]) * L);
      var b = Math.round(t.base[2] + (t.hi[2] - t.base[2]) * L);

      ctx.beginPath();
      ctx.moveTo(ax, ay);
      for (j = 1; j < n; j++) ctx.lineTo(S[ix[j] * 2], S[ix[j] * 2 + 1]);
      ctx.closePath();
      ctx.fillStyle = "rgb(" + r + "," + g + "," + b + ")";
      ctx.fill();
      // The edge is what makes it read as a machined part rather than a blob.
      // Stroking every face at low alpha gives the creases for free.
      ctx.strokeStyle = "rgba(238,240,244," + (0.05 + L * 0.22).toFixed(3) + ")";
      ctx.lineWidth = 1;
      ctx.stroke();
    }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }

  /* ---------- callouts ----------
     Drawn on the canvas, not laid over it in HTML. As DOM nodes pinned to the
     anchor they sat on top of the casting they were pointing at and were
     unreadable against it; as canvas they can be led out to the margin the
     way a balloon on a print is, with the leader elbowing round rather than
     crossing the machine. The DOM copies stay in the markup for a screen
     reader and for the translation -- the text is read out of them here, so
     this file never holds a word of either language. */
  var tags = [];
  Array.prototype.forEach.call(root.querySelectorAll("[data-tag]"), function (el) {
    var a = el.getAttribute("data-at").split(",").map(Number);
    tags.push({
      n: (el.querySelector("b") || {}).textContent || "",
      label: (el.querySelector("span:last-child") || {}).textContent || "",
      x: a[0], y: a[1], z: a[2]
    });
  });

  var MONO_STACK = 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace';
  // 11px is right on a 1392px stage and a whisper on a 2160px one
  function monoFont(w) {
    return Math.round(Math.max(11, Math.min(15, w / 150))) + 'px ' + MONO_STACK;
  }

  function drawTags(w, h) {
    if (!tags.length) return;
    var cy = Math.cos(yaw), sy = Math.sin(yaw);
    var cp = Math.cos(pitch), sp = Math.sin(pitch);
    var i, t, live = [];
    for (i = 0; i < tags.length; i++) {
      t = tags[i];
      var x = t.x - CX, y = t.y - CY, z = t.z - CZ;
      var x1 = x * cy + z * sy, z1 = -x * sy + z * cy;
      var y2 = y * cp - z1 * sp, z2 = y * sp + z1 * cp + DIST;
      live.push({
        t: t,
        sx: w / 2 + x1 * FOCAL / z2,
        sy: h / 2 + h * 0.02 - y2 * FOCAL / z2,
        behind: z1 > 0,
        left: x1 < 0
      });
    }

    // Two columns at the sheet edge, each entry keeping its own vertical order
    // and never closer than a line to its neighbour.
    var narrow = w < 620;
    var GUTTER = Math.max(12, Math.min(30, w * 0.035)), STEP = 26;
    [true, false].forEach(function (side) {
      var col = live.filter(function (o) { return o.left === side; })
                    .sort(function (a, b) { return a.sy - b.sy; });
      var top = h * 0.16;
      col.forEach(function (o) {
        o.ly = Math.max(top, Math.min(h - 40, o.sy));
        if (o.ly < top) o.ly = top;
        top = o.ly + STEP;
        o.lx = side ? GUTTER : w - GUTTER;
        o.side = side;
      });
    });

    ctx.save();
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    ctx.font = monoFont(w);
    ctx.textBaseline = "middle";
    for (i = 0; i < live.length; i++) {
      var o = live[i];
      var dim = o.behind ? 0.48 : 1;
      if (!narrow) {
        var reach = Math.max(34, Math.min(116, w * 0.10));
        var elbow = o.side ? o.lx + reach : o.lx - reach;
        ctx.strokeStyle = "rgba(255,255,255," + (0.26 * dim).toFixed(3) + ")";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(o.sx, o.sy);
        ctx.lineTo(elbow, o.ly);
        ctx.lineTo(o.side ? o.lx + reach * 0.83 : o.lx - reach * 0.83, o.ly);
        ctx.stroke();
      }

      ctx.beginPath();
      ctx.arc(o.sx, o.sy, 3, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(214,216,226," + (0.85 * dim).toFixed(3) + ")";
      ctx.stroke();

      // The number leads in both columns. Written as "number, then label
      // offset by the number's width" it came out as "CYLINDER HEADS 03" on
      // the right, because right-aligned text grows the other way.
      ctx.textAlign = o.side ? "left" : "right";
      var lab = o.t.label.toUpperCase();
      if (narrow) {                       // numbers only; the names are below
        ctx.textAlign = "left";
        ctx.fillStyle = "rgba(214,216,226," + dim.toFixed(3) + ")";
        ctx.fillText(o.t.n, o.sx + 9, o.sy - 8);
        continue;
      }
      var nw = ctx.measureText(o.t.n).width + 10;
      var lw = ctx.measureText(lab).width + 10;
      ctx.fillStyle = "rgba(214,216,226," + dim.toFixed(3) + ")";
      ctx.fillText(o.t.n, o.side ? o.lx : o.lx - lw, o.ly);
      ctx.fillStyle = "rgba(176,179,196," + (0.9 * dim).toFixed(3) + ")";
      ctx.fillText(lab, o.side ? o.lx + nw : o.lx, o.ly);
    }
    ctx.restore();
  }

  /* ---------- loop ---------- */
  var W = 0, H = 0, DPR = 1, running = false, raf = 0;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  function size() {
    var r = canvas.getBoundingClientRect();
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    W = Math.max(1, Math.round(r.width));
    H = Math.max(1, Math.round(r.height));
    canvas.width = Math.round(W * DPR);
    canvas.height = Math.round(H * DPR);
    refocus();
  }

  var last = 0;
  function frame(now) {
    raf = 0;
    if (autoYaw && !reduce.matches) {
      var dt = last ? Math.min(64, now - last) : 16;
      yaw += dt * 0.000085;
    }
    last = now;
    draw(W, H, DPR);
    drawTags(W, H);
    // Nothing is moving under a reduced-motion preference unless a finger is
    // on it, so the loop parks itself instead of repainting the same frame.
    if (running && (!reduce.matches || down)) raf = requestAnimationFrame(frame);
  }

  function start() {
    if (running) return;
    running = true; last = 0;
    root.classList.add("is-live");
    raf = requestAnimationFrame(frame);
  }
  function stop() {
    running = false;
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
  }

  /* drag to turn it. Pointer events cover mouse, pen and touch in one path;
     touch-action on the canvas is what stops a drag also scrolling the page. */
  var down = false, lx = 0, ly = 0;
  canvas.addEventListener("pointerdown", function (e) {
    down = true; lx = e.clientX; ly = e.clientY; autoYaw = false;
    canvas.setPointerCapture(e.pointerId);
    root.classList.add("is-held");
  });
  canvas.addEventListener("pointermove", function (e) {
    if (!down) return;
    yaw += (e.clientX - lx) * 0.008;
    pitch = Math.max(-0.12, Math.min(0.62, pitch + (e.clientY - ly) * 0.005));
    lx = e.clientX; ly = e.clientY;
    if (!running) { draw(W, H, DPR); drawTags(W, H); }
  });
  function release() {
    if (!down) return;
    down = false;
    root.classList.remove("is-held");
    if (running && !raf) raf = requestAnimationFrame(frame);
    setTimeout(function () { if (!down) autoYaw = true; }, 2200);
  }
  canvas.addEventListener("pointerup", release);
  canvas.addEventListener("pointercancel", release);

  window.addEventListener("resize", function () { size(); if (!running) { draw(W, H, DPR); drawTags(W, H); } });

  // Only runs while it is on screen. A render loop left going behind three
  // screens of scroll is a flat battery and nothing to show for it.
  size();
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (es) {
      es.forEach(function (e) { e.isIntersecting ? start() : stop(); });
    }, { rootMargin: "120px" }).observe(root);
  } else {
    start();
  }
  draw(W, H, DPR);
  drawTags(W, H);
})();
