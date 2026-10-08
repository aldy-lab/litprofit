/* ============================================================
   ISOMETRIC WORKING DRAWINGS -- one per service page
   ------------------------------------------------------------
   The refrigeration page has its machine: the compressor plate and the
   hand-built 3D unit. The other three services had a photograph and text.
   These give each of them a machine of its own, drawn in the same hairline
   language, and every one of them DOES the thing the service is about:

     pumps   -- a pump skid and its valve station. Open the valves and the
                refrigerant lights only the pipes it can actually reach; the
                pump will not run against a closed outlet.
     spool   -- a pipe spool on the jig. Weld the joints, then pressure-test;
                the test is refused until every joint is welded.
     stores  -- a warehouse rack. Pick a category and its bins light.
     plant   -- (home page) the engine room as an index of all four services.

   Projection and the "only what is live gets the accent" rule follow the
   iso-glow method (after iso-figure by Tolga Cohce, MIT). The accent is the
   site's own cool line colour, not a warm one.

   Dependency-free, like compressor.js. Strings arrive per figure in the
   svg's data-t attribute, so every label is translated by the build.
   Off screen, nothing animates; under prefers-reduced-motion the light still
   switches on and off, it just does not travel.
   ============================================================ */
(function () {
  'use strict';

  var C = Math.cos(Math.PI / 6), S = Math.sin(Math.PI / 6);
  var REDUCE = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);

  function f(n) { return Math.round(n * 100) / 100; }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* ---- the kernel ----
     +x runs down-right, +y down-left, +z up. Paint order is the only depth
     sort, so every figure draws back to front. The frame is computed from
     the figure's extreme corners and fits them tightly: widening it to 4:3
     only bought empty margin, and at a capped height that margin is what
     made every drawing smaller than its box. */
  function frame(points, pad) {
    pad = pad == null ? 22 : pad;
    var xs = [], ys = [];
    points.forEach(function (p) {
      xs.push((p[0] - p[1]) * C);
      ys.push((p[0] + p[1]) * S - p[2]);
    });
    var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs);
    var y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
    var W = x1 - x0 + 2 * pad, H = y1 - y0 + 2 * pad;
    var OX = -x0 + (W - (x1 - x0)) / 2, OY = -y0 + (H - (y1 - y0)) / 2;

    function P(x, y, z) { return [(x - y) * C + OX, (x + y) * S - z + OY]; }
    function D(x, y, z) { return [(x - y) * C, (x + y) * S - z]; }
    function plane(O, U, V) {
      var o = P(O[0], O[1], O[2]), u = D(U[0], U[1], U[2]), v = D(V[0], V[1], V[2]);
      return 'matrix(' + [u[0], u[1], v[0], v[1], o[0], o[1]].map(f).join(' ') + ')';
    }
    function TOP(x, y, z)   { return plane([x, y, z], [1, 0, 0], [0, 1, 0]); }
    function FRONT(x, y, z) { return plane([x, y, z], [1, 0, 0], [0, 0, -1]); }  /* y = max face */
    function SIDE(x, y, z)  { return plane([x, y, z], [0, -1, 0], [0, 0, -1]); } /* x = max face */
    function rect(tr, w, h, cls) {
      return '<g transform="' + tr + '"><rect class="' + (cls || 'iso-face') +
             '" width="' + w + '" height="' + h + '"/></g>';
    }
    /* A box is its three visible faces. Square corners on purpose: this is a
       working drawing, and rounding the top alone leaves the walls notched. */
    function box(x, y, z, w, d, h, cls) {
      return '<g' + (cls ? ' class="' + cls + '"' : '') + '>' +
        rect(SIDE(x + w, y + d, z + h), d, h, 'iso-face iso-side') +
        rect(FRONT(x, y + d, z + h), w, h, 'iso-face iso-front') +
        rect(TOP(x, y, z + h), w, d, 'iso-face iso-top') + '</g>';
    }
    function path(pts) {
      return 'M' + pts.map(function (p) {
        var q = P(p[0], p[1], p[2]); return f(q[0]) + ' ' + f(q[1]);
      }).join(' L');
    }
    return { P: P, D: D, TOP: TOP, FRONT: FRONT, SIDE: SIDE, rect: rect, box: box, path: path,
             viewBox: '0 0 ' + f(W) + ' ' + f(H) };
  }

  /* parallel hairlines on a face, in face-local units */
  function slits(a0, a1, step, b0, b1) {
    var s = '';
    for (var a = a0; a <= a1 + 0.001; a += step) {
      s += '<line class="iso-detail" x1="' + f(a) + '" y1="' + b0 + '" x2="' + f(a) + '" y2="' + b1 + '"/>';
    }
    return s;
  }

  /* Filters are userSpaceOnUse with a generous region: a perfectly straight
     pipe has a zero-height bounding box and vanishes under a default one. */
  function defs(id) {
    var R = ' filterUnits="userSpaceOnUse" x="-400" y="-400" width="2400" height="2000"';
    return '<defs>' +
      '<filter id="' + id + '-glow"' + R + '><feGaussianBlur stdDeviation="3.2" result="b"/>' +
        '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>' +
      '<filter id="' + id + '-soft"' + R + '><feGaussianBlur stdDeviation="1.6" result="b"/>' +
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>' +
      '<filter id="' + id + '-bloom"' + R + '><feGaussianBlur stdDeviation="9"/></filter>' +
      '</defs>';
  }

  /* A pipe that can carry light: a dark under-stroke so crossings read, the
     grey line, and over it a group that only shows while .hot -- the glowing
     line and a dash of light travelling along it. */
  function pipe(K, id, figId, pts) {
    var d = K.path(pts);
    return '<path class="iso-wire-under" d="' + d + '"/>' +
           '<path class="iso-wire" d="' + d + '"/>' +
           '<g class="iso-flow" id="' + id + '">' +
             '<path class="iso-glow-wire" filter="url(#' + figId + '-soft)" d="' + d + '"/>' +
             '<path class="iso-pulse" pathLength="1000" d="' + d + '"/>' +
           '</g>';
  }

  var FIGS = {};

  /* ============================================================
     PUMPS -- a skid and its valve station
     ============================================================ */
  FIGS.pumps = function (svg, api, t) {
    var ID = 'pumps';
    var K = frame([[0, 0, 0], [320, 0, 0], [0, 240, 0], [320, 240, 0],
                   [24, 24, 66], [304, 86, 112], [178, 84, 112]]);
    var TOP = K.TOP, FRONT = K.FRONT, SIDE = K.SIDE, box = K.box;
    var s = defs(ID);

    function valve(key, x, y, z, label, lx, ly) {
      return '<g class="iso-press iso-valve" id="' + ID + '-' + key + '" data-v="' + key + '">' +
        '<g transform="' + TOP(x, y, z + 9) + '"><circle class="iso-halo" r="18" filter="url(#' + ID + '-bloom)"/></g>' +
        box(x - 9, y - 9, z - 9, 18, 18, 18) +
        box(x - 2, y - 2, z + 9, 4, 4, 9) +
        '<g transform="' + TOP(x, y, z + 18) + '"><circle class="iso-wheel" r="9"/>' +
          '<line class="iso-detail" x1="-9" y1="0" x2="9" y2="0"/><line class="iso-detail" x1="0" y1="-9" x2="0" y2="9"/></g>' +
        '<g transform="' + TOP(x + (lx || 12), y + (ly || -12), z + 9) + '"><text class="iso-label" font-size="8">' + esc(label) + '</text></g>' +
        '</g>';
    }

    /* ground plate */
    s += box(0, 0, 0, 320, 240, 8);
    s += '<g transform="' + TOP(0, 0, 8) + '"><rect class="iso-detail" x="10" y="10" width="300" height="220"/></g>';

    /* receiver, girth seams on the long face */
    s += box(24, 24, 8, 110, 56, 58);
    s += '<g transform="' + FRONT(24, 80, 66) + '">' + slits(22, 92, 35, 20, 58) +
         '<text class="iso-label" x="8" y="13" font-size="8">' + esc(t.receiver) + '</text></g>';

    /* suction: receiver -> V1 -> pump */
    s += pipe(K, ID + '-suc', ID, [[110, 80, 30], [110, 172, 30], [158, 172, 30]]);
    s += valve('v1', 110, 120, 30, 'V1', -34, 4);

    /* bypass: tee -> V3 -> back into the receiver */
    s += pipe(K, ID + '-byp', ID, [[178, 110, 86], [178, 60, 86], [150, 60, 86], [150, 60, 40], [134, 60, 40]]);
    s += valve('v3', 178, 84, 86, 'V3');

    /* skid, pump casing, coupling, motor */
    s += box(150, 140, 8, 140, 70, 10);
    s += box(158, 152, 18, 40, 40, 40);
    s += '<g transform="' + FRONT(158, 192, 58) + '"><text class="iso-label" x="5" y="12" font-size="7">' + esc(t.pump) + '</text></g>';
    s += box(198, 164, 30, 8, 16, 16);
    s += box(206, 148, 18, 74, 48, 44);
    s += '<g transform="' + FRONT(206, 196, 62) + '">' + slits(8, 52, 4, 10, 40) +
         '<circle id="' + ID + '-led" class="iso-led" filter="url(#' + ID + '-soft)" cx="64" cy="10" r="3.6"/></g>';

    /* discharge riser and the branch to the plant */
    s += pipe(K, ID + '-dis', ID, [[178, 172, 58], [178, 172, 86], [178, 110, 86]]);
    s += pipe(K, ID + '-plt', ID, [[178, 110, 86], [296, 110, 86]]);
    s += box(173, 105, 81, 10, 10, 10);
    s += valve('v2', 236, 110, 86, 'V2');

    /* the sign the flow arrives at -- the one large lit element */
    s += box(296, 86, 60, 8, 48, 52);
    s += '<g transform="' + SIDE(304, 134, 112) + '" class="iso-screen" id="' + ID + '-scr">' +
         '<rect class="iso-glass" x="4" y="7" width="40" height="22"/>' +
         '<rect class="iso-halo" x="4" y="7" width="40" height="22" filter="url(#' + ID + '-bloom)"/>' +
         '<text class="iso-screen-t" x="24" y="21" font-size="6" text-anchor="middle">' + esc(t.plant) + '</text></g>';

    svg.setAttribute('viewBox', K.viewBox);
    svg.insertAdjacentHTML('beforeend', s);

    var st = { v1: false, v2: false, v3: false };
    function q(id) { return svg.querySelector('#' + ID + '-' + id); }
    function flow(id, on) { q(id).classList.toggle('hot', on); }

    function render() {
      var on = st.v1 && (st.v2 || st.v3);
      flow('suc', on); flow('dis', on);
      flow('plt', on && st.v2); flow('byp', on && st.v3);
      ['v1', 'v2', 'v3'].forEach(function (k) { q(k).classList.toggle('lit', st[k]); });
      q('led').classList.toggle('hot', on);
      q('scr').classList.toggle('hot', on && st.v2);
      var r = [on ? t.r_on : t.r_off];
      if (!st.v1) r.push(t.r_suction);
      else if (!st.v2 && !st.v3) r.push(t.r_nooutlet);
      else { if (st.v2) r.push(t.r_plant); if (st.v3) r.push(t.r_bypass); }
      api.readout(r.join(' · '));
    }
    function toggle(k) { st[k] = !st[k]; api.flash(q(k)); render(); }

    svg.addEventListener('click', function (e) {
      var v = e.target.closest('[data-v]'); if (v) toggle(v.getAttribute('data-v'));
    });
    render();
    return {
      key: function (e) {
        var k = { '1': 'v1', '2': 'v2', '3': 'v3' }[e.key];
        if (k) { toggle(k); return true; }
        return false;
      },
      demo: function () { api.after(500, function () { toggle('v1'); }); api.after(1100, function () { toggle('v2'); }); }
    };
  };

  /* ============================================================
     SPOOL -- weld the joints, then pressure-test
     ============================================================ */
  FIGS.spool = function (svg, api, t) {
    var ID = 'spool';
    var K = frame([[0, 30, 0], [330, 30, 0], [0, 210, 0], [330, 210, 0],
                   [231, 178, 62], [36, 95, 62]]);
    var TOP = K.TOP, FRONT = K.FRONT, box = K.box;
    var s = defs(ID);

    function joint(n, x, y, z, w, d, h, lx, ly) {
      var cx = x + w / 2, cy = y + d / 2;
      return '<g class="iso-press iso-joint" id="' + ID + '-j' + n + '" data-j="' + n + '">' +
        '<g transform="' + TOP(cx, cy, z + h) + '"><circle class="iso-halo" r="20" filter="url(#' + ID + '-bloom)"/></g>' +
        box(x, y, z, w, d, h) +
        '<g transform="' + TOP(cx + (lx === undefined ? 8 : lx), cy + (ly === undefined ? -14 : ly), z + h) + '"><text class="iso-label" font-size="8">J' + n + '</text></g>' +
        '</g>';
    }

    s += box(0, 30, 0, 330, 180, 8);
    /* the jig: a slotted table */
    s += box(20, 60, 8, 290, 130, 18);
    s += '<g transform="' + K.TOP(20, 60, 26) + '">' +
         [20, 52, 84, 116].map(function (y) {
           return '<line class="iso-detail" x1="10" y1="' + y + '" x2="280" y2="' + y + '"/>';
         }).join('') + '</g>';

    /* V-blocks the spool rests on */
    s += box(70, 96, 26, 14, 26, 10);
    s += box(150, 96, 26, 14, 26, 10);
    s += box(234, 150, 26, 20, 14, 10);

    /* the spool, back to front */
    s += box(36, 95, 30, 6, 28, 28);                 /* flange F1 */
    s += box(42, 102, 37, 70, 14, 14);               /* S1 */
    s += joint(1, 112, 99, 34, 8, 20, 20);
    s += box(120, 102, 37, 70, 14, 14);              /* S2 */
    s += joint(2, 190, 99, 34, 8, 20, 20);
    s += box(198, 102, 37, 40, 14, 14);              /* S3 */
    s += box(238, 102, 37, 14, 14, 14);              /* elbow */
    s += box(238, 116, 37, 14, 20, 14);              /* S4a */
    s += joint(3, 235, 136, 34, 20, 8, 20, 30, 2);
    s += box(238, 144, 37, 14, 26, 14);              /* S4b */
    s += joint(4, 235, 170, 34, 20, 8, 20, 48, 0);
    s += box(231, 178, 30, 28, 6, 28);               /* flange F2 */

    /* the test medium, along the top of the spool */
    s += pipe(K, ID + '-test', ID, [[39, 109, 51], [245, 109, 51], [245, 181, 51]]);

    /* gauge on the blind flange */
    s += '<g transform="' + FRONT(231, 184, 58) + '" class="iso-screen" id="' + ID + '-gauge">' +
         '<circle class="iso-halo" cx="14" cy="14" r="11" filter="url(#' + ID + '-bloom)"/>' +
         '<circle class="iso-glass" cx="14" cy="14" r="10"/>' +
         [-120, -60, 0, 60, 120].map(function (a) {
           var r = a * Math.PI / 180;
           return '<line class="iso-tick" x1="' + f(14 + 7 * Math.sin(r)) + '" y1="' + f(14 - 7 * Math.cos(r)) +
                  '" x2="' + f(14 + 9 * Math.sin(r)) + '" y2="' + f(14 - 9 * Math.cos(r)) + '"/>';
         }).join('') +
         '<line id="' + ID + '-needle" class="iso-needle" x1="14" y1="14" x2="14" y2="6" transform="rotate(-120 14 14)"/>' +
         '</g>';

    svg.setAttribute('viewBox', K.viewBox);
    svg.insertAdjacentHTML('beforeend', s);

    var st = { w: [false, false, false, false], testing: false, held: false };
    var needle = svg.querySelector('#' + ID + '-needle');
    var stopNeedle = null;
    function q(id) { return svg.querySelector('#' + ID + '-' + id); }
    function welded() { return st.w.filter(Boolean).length; }
    function setNeedle(a) { needle.setAttribute('transform', 'rotate(' + f(a) + ' 14 14)'); }

    function render() {
      st.w.forEach(function (on, i) { q('j' + (i + 1)).classList.toggle('lit', on); });
      q('test').classList.toggle('hot', st.testing || st.held);
      q('gauge').classList.toggle('hot', st.testing || st.held);
      var n = welded();
      if (st.held) api.readout(n + '/4 ' + t.r_welds + ' · ' + t.r_holding);
      else if (st.testing) api.readout(n + '/4 ' + t.r_welds + ' · ' + t.r_testing);
      else api.readout(n + '/4 ' + t.r_welds + (n === 4 ? ' · ' + t.r_ready : ''));
    }
    function weld(i) {
      if (st.testing || st.held) return;
      st.w[i] = true; api.flash(q('j' + (i + 1))); render();
    }
    function test() {
      if (st.testing || st.held) return;
      var first = st.w.indexOf(false);
      if (first !== -1) {
        api.flash(q('j' + (first + 1)));
        api.readout(welded() + '/4 ' + t.r_welds + ' · ' + t.r_refused + ' · ' + t.r_weld + ' J' + (first + 1));
        return;
      }
      st.testing = true; render();
      if (REDUCE) { setNeedle(70); st.testing = false; st.held = true; render(); return; }
      var t0 = null;
      stopNeedle = api.loop(function (ts) {
        if (t0 === null) t0 = ts;
        var k = Math.min(1, (ts - t0) / 1600), e = 1 - Math.pow(1 - k, 3);
        setNeedle(-120 + 190 * e);
        if (k >= 1) { stopNeedle(); st.testing = false; st.held = true; render(); }
      });
    }
    function reset() {
      if (stopNeedle) stopNeedle();
      st = { w: [false, false, false, false], testing: false, held: false };
      setNeedle(-120); render();
    }

    svg.addEventListener('click', function (e) {
      var j = e.target.closest('[data-j]');
      if (j) { weld(+j.getAttribute('data-j') - 1); return; }
      if (e.target.closest('#' + ID + '-gauge')) test();
    });
    render();
    return {
      key: function (e) {
        if ('1234'.indexOf(e.key) !== -1 && e.key.length === 1) { weld(+e.key - 1); return true; }
        if (e.key === 't' || e.key === 'T') { test(); return true; }
        if (e.key === 'r' || e.key === 'R') { reset(); return true; }
        return false;
      },
      demo: function () {
        [0, 1, 2, 3].forEach(function (i) { api.after(450 + i * 380, function () { weld(i); }); });
        api.after(450 + 4 * 380 + 300, test);
      }
    };
  };

  /* ============================================================
     STORES -- a warehouse rack by category
     ============================================================ */
  FIGS.stores = function (svg, api, t) {
    var ID = 'stores';
    var K = frame([[0, 0, 0], [340, 0, 0], [0, 170, 0], [340, 170, 0],
                   [20, 40, 214], [320, 110, 214]]);
    var TOP = K.TOP, FRONT = K.FRONT, box = K.box;
    var ORDER = ['C', 'E', 'P', 'T', 'V'];
    /* rows bottom to top */
    var ROWS = [['E', 'E', 'E', 'T', 'P'], ['C', 'C', 'C', 'V', 'V'], ['V', 'V', 'P', 'P', 'T']];
    var SHELF = [14, 72, 130];
    var s = defs(ID), count = {};

    s += box(0, 0, 0, 340, 170, 8);
    s += '<g transform="' + TOP(0, 0, 8) + '"><rect class="iso-detail" x="10" y="10" width="320" height="150"/></g>';
    s += box(20, 40, 8, 6, 6, 186);
    s += box(314, 40, 8, 6, 6, 186);

    ROWS.forEach(function (row, r) {
      var z0 = SHELF[r];
      s += box(20, 40, z0, 300, 70, 4);
      row.forEach(function (c, i) {
        count[c] = (count[c] || 0) + 1;
        var x = 30 + i * 58, code = c + '-' + (count[c] < 10 ? '0' : '') + count[c];
        s += '<g class="iso-press iso-bin" data-c="' + c + '">' +
             box(x, 52, z0 + 4, 50, 48, 40) +
             '<g transform="' + FRONT(x, 100, z0 + 44) + '">' +
               '<rect class="iso-halo" x="6" y="6" width="38" height="15" filter="url(#' + ID + '-bloom)"/>' +
               '<rect class="iso-tag" x="8" y="8" width="34" height="11"/>' +
               '<text class="iso-tag-t" x="25" y="16.2" font-size="7" text-anchor="middle">' + code + '</text>' +
               '<line class="iso-detail" x1="14" y1="30" x2="36" y2="30"/>' +
             '</g></g>';
      });
    });

    /* cap and the header board that names the selection -- the lit element */
    s += box(20, 40, 188, 300, 70, 4);
    s += box(26, 100, 192, 288, 4, 22);
    s += '<g transform="' + FRONT(26, 104, 214) + '" class="iso-screen" id="' + ID + '-scr">' +
         '<rect class="iso-halo" x="4" y="4" width="280" height="14" filter="url(#' + ID + '-bloom)"/>' +
         '<rect class="iso-glass" x="4" y="4" width="280" height="14"/>' +
         '<text id="' + ID + '-scr-t" class="iso-screen-t" x="144" y="13.6" font-size="7" text-anchor="middle"></text></g>';
    s += box(20, 104, 8, 6, 6, 186);
    s += box(314, 104, 8, 6, 6, 186);

    svg.setAttribute('viewBox', K.viewBox);
    svg.insertAdjacentHTML('beforeend', s);

    var st = { sel: null };
    var bins = Array.prototype.slice.call(svg.querySelectorAll('[data-c]'));
    var scr = svg.querySelector('#' + ID + '-scr'), scrT = svg.querySelector('#' + ID + '-scr-t');

    function render() {
      bins.forEach(function (b) { b.classList.toggle('lit', b.getAttribute('data-c') === st.sel); });
      scr.classList.toggle('hot', !!st.sel);
      scrT.textContent = (st.sel ? t.cats[st.sel] : t.select).toUpperCase();
      api.readout(st.sel ? t.cats[st.sel] + ' · ' + t.r_bins + ': ' + count[st.sel] : t.r_none);
    }
    function pick(c) { st.sel = (st.sel === c) ? null : c; render(); }

    svg.addEventListener('click', function (e) {
      var b = e.target.closest('[data-c]'); if (b) { api.flash(b); pick(b.getAttribute('data-c')); }
    });
    render();
    return {
      key: function (e) {
        var i = '12345'.indexOf(e.key);
        if (e.key.length === 1 && i !== -1) { pick(ORDER[i]); return true; }
        if (e.key === 'Escape' && st.sel) { st.sel = null; render(); return true; }
        return false;
      },
      demo: function () { api.after(600, function () { pick('P'); }); }
    };
  };


  /* ============================================================
     PLANT -- the engine room, as an index of the four services
     ------------------------------------------------------------
     Home page only. A hull section with the four kinds of work in it:
     01 the refrigeration plant, 02 the pump skid and its valve, 03 the pipe
     runs along the frames, 04 the spares rack. A zone and the service card
     with the same number light together; a second click (or Enter) opens
     that service. The names come from the cards themselves, so the figure
     can never disagree with them. Untouched and on screen, it walks through
     the four once every few seconds; the first touch stops the tour.
     ============================================================ */
  FIGS.plant = function (svg, api, t) {
    var ID = 'plant';
    var K = frame([[0, 0, 0], [380, 0, 0], [0, 260, 0], [380, 260, 0],
                   [0, 0, 160], [380, 0, 160], [0, 260, 160]], 16);
    var TOP = K.TOP, FRONT = K.FRONT, SIDE = K.SIDE, box = K.box;
    var s = defs(ID);

    function tag(tr, x, y, n) {
      return '<g transform="' + tr + '"><rect class="iso-tag" x="' + x + '" y="' + y + '" width="22" height="11"/>' +
             '<text class="iso-tag-t" x="' + (x + 11) + '" y="' + (y + 8.2) + '" font-size="7" text-anchor="middle">' + n + '</text></g>';
    }
    function halo(x, y, w, d) {
      return '<g transform="' + TOP(x, y, 10) + '"><rect class="iso-halo" width="' + w + '" height="' + d +
             '" rx="' + Math.min(w, d) / 2 + '" filter="url(#' + ID + '-bloom)"/></g>';
    }
    function hit(pts) { return '<path class="iso-hit" d="' + K.path(pts) + '"/>'; }

    /* the hull section: deck plating, two walls with their frames, a ladder */
    s += box(0, 0, 0, 380, 260, 10);
    s += '<g transform="' + TOP(0, 0, 10) + '">' +
         [52, 104, 156, 208].map(function (y) { return '<line class="iso-detail" x1="12" y1="' + y + '" x2="372" y2="' + y + '"/>'; }).join('') +
         [95, 190, 285].map(function (x) { return '<line class="iso-detail" x1="' + x + '" y1="12" x2="' + x + '" y2="252"/>'; }).join('') + '</g>';
    s += box(0, 0, 10, 8, 260, 150);
    s += '<g transform="' + SIDE(8, 260, 160) + '">' + slits(30, 230, 50, 0, 150) +
         '<line class="iso-detail" x1="0" y1="70" x2="252" y2="70"/></g>';
    s += box(0, 0, 10, 380, 8, 150);
    s += '<g transform="' + FRONT(0, 8, 160) + '">' + slits(48, 328, 56, 0, 150) +
         '<line class="iso-detail" x1="8" y1="70" x2="380" y2="70"/>' +
         '<line class="iso-detail" x1="344" y1="8" x2="344" y2="150"/><line class="iso-detail" x1="362" y1="8" x2="362" y2="150"/>' +
         slits(16, 144, 14, 0, 0).replace(/x1="([\d.]+)" y1="0" x2="([\d.]+)" y2="0"/g, 'x1="344" y1="$1" x2="362" y2="$2"') +
         '</g>';

    /* 03 -- pipe runs along the frames */
    var hdrA = [[18, 244, 122], [18, 18, 122], [336, 18, 122]];
    var hdrB = [[30, 18, 106], [336, 18, 106]];
    s += '<g class="iso-press iso-zone" data-n="3">' +
         hit(hdrA) + hit(hdrB) +
         pipe(K, ID + '-hA', ID, hdrA) + pipe(K, ID + '-hB', ID, hdrB) +
         box(12, 12, 116, 12, 12, 12) +
         [90, 190, 290].map(function (x) { return box(x, 8, 100, 6, 16, 3); }).join('') +
         tag(FRONT(0, 8, 160), 150, 6, '03') + '</g>';

    /* 01 -- refrigeration plant: control panel, compressor, motor, discharge */
    s += '<g class="iso-press iso-zone" data-n="1">' + halo(36, 36, 140, 80) +
         box(40, 26, 10, 40, 12, 90) +
         tag(FRONT(40, 38, 100), 9, 10, '01') +
         '<g transform="' + FRONT(40, 38, 100) + '">' + slits(8, 32, 6, 30, 50) + '</g>' +
         box(40, 44, 10, 130, 66, 8) +
         box(50, 50, 18, 58, 52, 42) +
         '<g transform="' + FRONT(50, 102, 60) + '">' + slits(8, 50, 6, 8, 34) + '</g>' +
         box(108, 70, 28, 6, 14, 14) +
         box(114, 56, 18, 50, 42, 34) +
         '<g transform="' + FRONT(114, 98, 52) + '">' + slits(6, 44, 4, 6, 28) + '</g>' +
         pipe(K, ID + '-d1', ID, [[92, 76, 60], [92, 76, 106], [92, 18, 106]]) + '</g>';

    /* 02 -- pump skid with its valve on the riser */
    s += '<g class="iso-press iso-zone" data-n="2">' + halo(216, 46, 128, 72) +
         box(220, 50, 10, 120, 60, 8) +
         pipe(K, ID + '-d2', ID, [[250, 80, 52], [250, 80, 106], [250, 18, 106]]) +
         box(230, 62, 18, 40, 36, 34) +
         box(270, 74, 26, 6, 12, 12) +
         box(276, 64, 18, 56, 32, 30) +
         '<g transform="' + FRONT(276, 96, 48) + '">' + slits(6, 26, 4, 6, 24) + '</g>' +
         tag(FRONT(276, 96, 48), 31, 9, '02') +
         box(244, 74, 72, 12, 12, 12) + box(248, 78, 84, 4, 4, 7) +
         '<g transform="' + TOP(250, 80, 91) + '"><circle class="iso-wheel" r="8"/>' +
           '<line class="iso-detail" x1="-8" y1="0" x2="8" y2="0"/><line class="iso-detail" x1="0" y1="-8" x2="0" y2="8"/></g>' +
         '</g>';

    /* 04 -- spares rack, front left: back posts, shelves with bins, front posts */
    var r = '<g class="iso-press iso-zone" data-n="4">' + halo(36, 182, 118, 58);
    r += box(40, 186, 10, 4, 4, 117) + box(146, 186, 10, 4, 4, 117);
    [10, 48, 86].forEach(function (z) {
      r += box(40, 186, z, 110, 50, 4);
      for (var i = 0; i < 3; i++) {
        var x = 46 + i * 34;
        r += box(x, 192, z + 4, 28, 38, 24) +
             '<g transform="' + FRONT(x, 230, z + 28) + '"><rect class="iso-tag" x="7" y="5" width="14" height="6"/></g>';
      }
    });
    r += box(40, 186, 124, 110, 50, 3);
    r += tag(FRONT(40, 236, 127), 4, -16, '04');
    r += box(40, 232, 10, 4, 4, 117) + box(146, 232, 10, 4, 4, 117) + '</g>';
    s += r;

    /* where each callout's leader lands: a point on the part it names */
    var ANCHOR = { 1: [79, 76, 60], 2: [304, 80, 48], 3: [300, 18, 122], 4: [40, 236, 70] };
    Object.keys(ANCHOR).forEach(function (n) {
      var q = K.P.apply(null, ANCHOR[n]);
      s += '<circle class="iso-anchor" data-anchor="' + n + '" cx="' + f(q[0]) + '" cy="' + f(q[1]) + '" r="0.01"/>';
    });

    svg.setAttribute('viewBox', K.viewBox);
    svg.insertAdjacentHTML('beforeend', s);

    /* the cards this figure indexes, matched by their printed number */
    var section = svg.closest('section') || document;
    var cards = {};
    Array.prototype.forEach.call(section.querySelectorAll('a.iso-call, a.card'), function (a) {
      var n = parseInt((a.querySelector('.card-num') || {}).textContent, 10);
      if (n >= 1 && n <= 4) cards[n] = a;
    });
    var zones = {};
    Array.prototype.forEach.call(svg.querySelectorAll('[data-n]'), function (g) { zones[g.getAttribute('data-n')] = g; });

    var st = { sel: 0, touched: false };
    function name(n) {
      var c = cards[n], h = c && c.querySelector('h3');
      return '0' + n + (h ? ' · ' + h.textContent.trim() : '');
    }
    /* Leader lines, from each callout's inner edge to its anchor. They live
       in an overlay over the whole plate, in CSS pixels, so they are redrawn
       whenever the plate changes size; hidden (display:none) they measure 0
       and nothing is drawn. */
    var annot = svg.closest('.iso-annot'), lead = annot && annot.querySelector('.iso-leaders');
    function leaders() {
      if (!lead) return;
      var box = annot.getBoundingClientRect();
      if (!lead.getBoundingClientRect().width) { lead.innerHTML = ''; return; }
      lead.setAttribute('viewBox', '0 0 ' + f(box.width) + ' ' + f(box.height));
      var out = '';
      Object.keys(cards).forEach(function (n) {
        var dot = svg.querySelector('[data-anchor="' + n + '"]');
        var hd = cards[n].querySelector('h3') || cards[n];
        if (!dot) return;
        var a = dot.getBoundingClientRect(), c = hd.getBoundingClientRect(), cr = cards[n].getBoundingClientRect();
        var ax = a.left + a.width / 2 - box.left, ay = a.top + a.height / 2 - box.top;
        var left = cr.left + cr.width / 2 < ax + box.left;
        var x0 = (left ? cr.right + 12 : cr.left - 12) - box.left;
        var y0 = c.top + Math.min(c.height, 22) / 2 - box.top;
        var x1 = x0 + (left ? 28 : -28);
        out += '<g class="iso-leader" data-lead="' + n + '"><path d="M' + f(x0) + ' ' + f(y0) + ' H' + f(x1) +
               ' L' + f(ax) + ' ' + f(ay) + '"/><circle cx="' + f(ax) + '" cy="' + f(ay) + '" r="3"/>' +
               '<circle class="iso-leader-end" cx="' + f(x0) + '" cy="' + f(y0) + '" r="1.6"/></g>';
      });
      lead.innerHTML = out;
      paintLeaders();
    }
    function paintLeaders() {
      if (!lead) return;
      Array.prototype.forEach.call(lead.querySelectorAll('[data-lead]'), function (g) {
        g.classList.toggle('hot', +g.getAttribute('data-lead') === st.sel);
      });
    }
    if (annot && 'ResizeObserver' in window) new ResizeObserver(leaders).observe(annot);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(leaders);

    function render() {
      paintLeaders();
      for (var n = 1; n <= 4; n++) {
        var on = st.sel === n;
        zones[n].classList.toggle('lit', on);
        Array.prototype.forEach.call(zones[n].querySelectorAll('.iso-flow'), function (fl) { fl.classList.toggle('hot', on); });
        if (cards[n]) cards[n].classList.toggle('is-iso-lit', on);
      }
      api.readout(st.sel ? name(st.sel) : (t.r_none || ''));
    }
    function pick(n) { st.sel = n; render(); }
    function open(n) { if (cards[n]) window.location.href = cards[n].href; }
    function touch() { st.touched = true; }

    svg.addEventListener('click', function (e) {
      var z = e.target.closest('[data-n]'); if (!z) return;
      var n = +z.getAttribute('data-n');
      touch(); api.flash(z);
      if (st.sel === n) open(n); else pick(n);
    });
    Object.keys(cards).forEach(function (n) {
      var c = cards[n];
      function on() { touch(); pick(+n); }
      c.addEventListener('mouseenter', on);
      c.addEventListener('focus', on);
    });
    render();

    /* the tour: one zone after another while nobody has touched it */
    function tour() {
      if (REDUCE) return;
      (function next() {
        api.after(2800, function () {
          if (st.touched) return;
          if (api.visible()) pick(st.sel % 4 + 1);
          next();
        });
      })();
    }
    return {
      key: function (e) {
        var i = '1234'.indexOf(e.key);
        if (e.key.length === 1 && i !== -1) { touch(); pick(i + 1); return true; }
        if (e.key === 'Enter' && st.sel) { open(st.sel); return true; }
        if (e.key === 'Escape' && st.sel) { touch(); pick(0); return true; }
        return false;
      },
      demo: function () { api.after(400, function () { if (!st.touched) pick(1); }); tour(); }
    };
  };

  /* ============================================================
     MOUNT
     ============================================================ */
  function mount(svg) {
    var id = svg.getAttribute('data-iso'), make = FIGS[id];
    if (!make || svg.getAttribute('data-iso-on')) return;
    svg.setAttribute('data-iso-on', '1');
    var plate = svg.closest('[data-iso-plate]') || svg.parentNode;
    var out = plate.querySelector('[data-iso-readout]');
    var t = {};
    try { t = JSON.parse(svg.getAttribute('data-t') || '{}'); } catch (e) { /* labels stay blank */ }

    var timers = [], loops = [], visible = false;
    var api = {
      readout: function (str) { if (out) out.textContent = str; },
      visible: function () { return visible; },
      after: function (ms, fn) { timers.push(setTimeout(fn, ms)); },
      /* frames only while the drawing is on screen */
      loop: function (fn) {
        var live = true, raf = 0;
        function step(ts) { if (!live) return; if (visible) fn(ts); raf = requestAnimationFrame(step); }
        raf = requestAnimationFrame(step);
        var stop = function () { live = false; cancelAnimationFrame(raf); };
        loops.push(stop);
        return stop;
      },
      flash: function (el) {
        if (!el) return;
        el.classList.add('down');
        setTimeout(function () { el.classList.remove('down'); }, 140);
      }
    };

    var h = make(svg, api, t) || {};
    svg.setAttribute('tabindex', '0');
    svg.addEventListener('keydown', function (e) {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (h.key && h.key(e)) e.preventDefault();
    });

    /* Opens lit: the demo runs the first time the drawing is actually seen,
       using the same functions as a click, so a visitor who never touches
       it still sees what it does. */
    var demoed = false;
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        es.forEach(function (en) {
          visible = en.isIntersecting;
          plate.classList.toggle('iso-paused', !visible);
          if (visible && !demoed && h.demo) { demoed = true; h.demo(); }
        });
      }, { threshold: 0.25 }).observe(svg);
    } else {
      visible = true;
      if (h.demo) { demoed = true; h.demo(); }
    }
  }

  function boot() { Array.prototype.forEach.call(document.querySelectorAll('svg[data-iso]'), mount); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
