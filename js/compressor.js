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

  /* One engine, more than one machine. The alternative was a second file with
     its own copy of project/cull/sort/shade, and two copies of a renderer are
     two renderers that drift: a fix to the culling in one is a bug that
     survives in the other. The geometry is the only part that differs. */
  var root = document.querySelector("[data-compressor]");
  if (!root) return;
  var MACHINE = root.getAttribute("data-machine") || "recip";
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

  /* A moving part is a range of vertices plus the rule for moving it. The
     originals are kept, because a transform applied to already-transformed
     coordinates compounds: rotate by a degree sixty times a second and after a
     minute the rotor is a smear. Every frame starts from the same geometry. */
  var PARTS = [];
  function movable(from, rule){
    var orig = V.slice(from * 3);
    PARTS.push({ from: from * 3, orig: orig, rule: rule });
  }

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

  /* ---------- the machines ----------
     A tone is an index into TONE below. GHOST is drawn translucent, which is
     what makes a casing something you can see the works through. */
  var STEEL = 0, DARK = 1, PIPE = 2, GHOST = 3, ROTOR = 4, GAS = 5;

  function buildRecip(){
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
  }

  /* ---------- twin-screw compressor, casing ghosted ----------
     The machine Litprofit overhauls under the SABROE, GRASSO and BITZER names:
     SAB 128, SAB 163, Grasso S3-900, CSH8563, OSKA 8591. A pair of helical
     rotors turning in a figure-of-eight bore -- four lobes on the male, six
     flutes on the female, which is the ratio nearly every marine screw uses --
     and gas carried from the suction end to the discharge end in the pockets
     between them.

     Drawn, not traced. The reference films for this are Howden's and BITZER's
     and are their copyright; what is reused is the arrangement, which is the
     same on every screw compressor ever built and belongs to nobody.

     Nothing here is a section through a real rotor profile: a true SRM or
     asymmetric profile is a manufacturer's own curve and not something to
     guess at. This is a generic lobe swept along a helix -- right in count,
     wrap and direction, and honest about being a diagram. */
  function lobeProfile(n, rTip, rRoot, lobeWidth){
    /* One turn of the profile as a closed polygon: a rounded tip, a flank
       down to the root, a rounded root, and back up. */
    var pts = [], i, k, a;
    for (i = 0; i < n; i++) {
      var base = (i / n) * Math.PI * 2;
      for (k = 0; k <= 8; k++) {
        a = base + (k / 8) * lobeWidth;
        pts.push([Math.cos(a) * rTip, Math.sin(a) * rTip]);
      }
      for (k = 0; k <= 8; k++) {
        a = base + lobeWidth + (k / 8) * ((Math.PI * 2 / n) - lobeWidth);
        pts.push([Math.cos(a) * rRoot, Math.sin(a) * rRoot]);
      }
    }
    return pts;
  }

  /* Sweep a profile along X, rotating it as it goes. That rotation IS the
     helix, and its sign is what makes the two rotors mesh rather than collide:
     they turn opposite ways, so they wrap opposite ways. */
  function screwRotor(x0, x1, cy, cz, prof, wrap, phase, seg, t){
    var start = F.length, rings = [], i, k;
    for (i = 0; i <= seg; i++) {
      var x = x0 + (x1 - x0) * (i / seg);
      var a = phase + wrap * (i / seg);
      var c = Math.cos(a), s2 = Math.sin(a), ring = [];
      for (k = 0; k < prof.length; k++) {
        var py = prof[k][0], pz = prof[k][1];
        ring.push(vert(x, cy + py * c - pz * s2, cz + py * s2 + pz * c));
      }
      rings.push(ring);
    }
    for (i = 0; i < seg; i++) {
      for (k = 0; k < prof.length; k++) {
        var n2 = (k + 1) % prof.length;
        quad(rings[i][k], rings[i][n2], rings[i + 1][n2], rings[i + 1][k], t);
      }
    }
    F.push({ i: rings[0].slice().reverse(), t: t });
    F.push({ i: rings[seg].slice(), t: t });
    orient(start, (x0 + x1) / 2, cy, cz);
    return rings;
  }

  function buildScrew(){
    /* ---- the bore: two overlapping cylinders, which is the shape of the
       casing and the reason a screw compressor looks like a figure of eight
       from the end ---- */
    /* 96 and -70 is 166 apart, and with 100 and 92 of tip radius the pair
       overlaps by 26 -- tips into roots, which is meshing. */
    var MY = 96, FY = -70;          // rotor centres, male above female
    var seg = 46;

    // the casing, ghosted -- barrel, both end covers and the flanges
    tubeX(70, 690, MY, 0, 112, 34, GHOST, false, false);
    tubeX(70, 690, FY, 0, 104, 34, GHOST, false, false);
    box(60, 84, -240, 250, -172, 172, GHOST);        // suction end cover
    box(676, 700, -240, 250, -172, 172, GHOST);      // discharge end cover
    box(84, 676, -236, -214, -160, 160, GHOST);      // the foot it stands on
    for (var fx = 150; fx < 640; fx += 240) {        // casing ribs
      tubeX(fx, fx + 14, MY, 0, 120, 30, GHOST, false, false);
      tubeX(fx, fx + 14, FY, 0, 112, 30, GHOST, false, false);
    }

    // ---- the rotors ----
    // four lobes driving six flutes: the 4/6 pair nearly every marine screw
    // uses, and the reason the two turn at different speeds
    /* A flute is a notch cut into a land, so the female's tip radius is the
       LARGE one and its root the small one. Written the other way round the
       profile turns inside out, and what came back was a heap of grey wedges
       rather than a rotor -- which is what a polygon does when its outline
       crosses itself.

       And the tips have to reach past the centre line into the other rotor's
       roots, which is what meshing IS -- but only just. Radii that overlap by
       more than the roots are deep leaves two solids occupying the same space,
       and no amount of shading makes that read. */
    var male   = lobeProfile(4, 100, 58, 0.58);
    var female = lobeProfile(6,  92, 54, 0.34);
    /* Four lobes driving six, so the female turns at four sixths of the male's
       speed and the other way about. That ratio is not decoration: it is why
       the two mesh at all, and getting it wrong makes a pair of screws that
       grind rather than turn. */
    var mFrom = V.length / 3;
    screwRotor(96, 664, MY, 0, male,   Math.PI * 1.05, 0,    seg, ROTOR);
    movable(mFrom, { spin: 1, cy: MY, cz: 0 });
    var fFrom = V.length / 3;
    screwRotor(96, 664, FY, 0, female, -Math.PI * 0.70, 0.4, seg, ROTOR);
    movable(fFrom, { spin: -4 / 6, cy: FY, cz: 0 });

    // the gas, carried in the pockets between the rotors
    for (var gi = 0; gi < 6; gi++) {
      var gFrom = V.length / 3;
      gasThread(112, 648, MY, 0, 15, Math.PI * 1.05, (gi / 6) * Math.PI * 2, 30);
      movable(gFrom, { spin: 1, cy: MY, cz: 0 });
    }

    // shafts out of both ends, and the bearings they run in
    tubeX(40, 100, MY, 0, 34, 20, DARK);
    tubeX(660, 760, MY, 0, 34, 20, DARK);
    tubeX(40, 100, FY, 0, 30, 20, DARK);
    tubeX(660, 700, FY, 0, 30, 20, DARK);
    tubeX(96, 128, MY, 0, 64, 22, DARK);             // suction-end bearing
    tubeX(632, 664, MY, 0, 64, 22, DARK);            // discharge-end bearing
    tubeX(96, 128, FY, 0, 58, 22, DARK);
    tubeX(632, 664, FY, 0, 58, 22, DARK);

    // ---- slide valve: the capacity control, under the bores ----
    /* The slide valve is how a screw compressor is turned down: it opens a
       path back to suction, so part of each pocket is returned instead of
       compressed. It moves, slowly, because that is what it does. */
    var sFrom = V.length / 3;
    box(180, 560, -196, -160, -46, 46, PIPE);
    tubeX(560, 740, -178, 0, 16, 16, PIPE);          // its rod
    movable(sFrom, { slide: 130 });
    tubeX(740, 790, -178, 0, 44, 22, DARK);          // and the actuator, fixed

    // suction and discharge branches
    box(60, 84, 150, 250, -120, 120, PIPE);
    box(676, 700, -150, -60, -90, 90, PIPE);
  }

  /* A slender helix following the flute, drawn between the rotors where the
     pocket actually is. Six threads, phased around, so the flow reads as
     continuous rather than as one wire. */
  function gasThread(x0, x1, cy, cz, r, wrap, phase, seg){
    var start = F.length, rings = [], i, k, ringPts = 7;
    for (i = 0; i <= seg; i++) {
      var f = i / seg;
      var x = x0 + (x1 - x0) * f;
      var a = phase + wrap * f;
      /* the pocket shrinks towards the discharge end, which is the whole
         story of the machine and the reason this tapers */
      var rr = r * (1 - 0.55 * f);
      var oy = cy + Math.cos(a) * 74, oz = cz + Math.sin(a) * 74, ring = [];
      for (k = 0; k < ringPts; k++) {
        var b = (k / ringPts) * Math.PI * 2;
        ring.push(vert(x, oy + Math.cos(b) * rr, oz + Math.sin(b) * rr));
      }
      rings.push({ ring: ring, u: f });
    }
    for (i = 0; i < seg; i++) {
      for (k = 0; k < ringPts; k++) {
        var n2 = (k + 1) % ringPts;
        F.push({ i: [rings[i].ring[k], rings[i].ring[n2],
                     rings[i + 1].ring[n2], rings[i + 1].ring[k]],
                 t: GAS, u: rings[i].u });
      }
    }
    orient(start, (x0 + x1) / 2, cy, cz);
    /* the threads travel with the rotor they sit in */
    return start;
  }

  var MACHINES = { recip: buildRecip, screw: buildScrew };
  (MACHINES[MACHINE] || buildRecip)();
  measureModel();

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
    { base: [ 56,  59,  68], hi: [243, 244, 247] },              // STEEL
    /* Same steel, but no edge stroked. A rotor is 46 rings of 72 points, and
       outlining every quad of that draws the mesh instead of the surface --
       the flutes came out looking like netting stretched over a cone. Flat
       shading alone gives the form; the wireframe was only ever helping on
       boxes, where the edges are real. */
    { base: [ 28,  30,  37], hi: [146, 149, 158] },              // DARK
    { base: [ 46,  49,  58], hi: [219, 221, 227] },              // PIPE
    /* The casing. Pale and cold and mostly not there -- the reference films
       show the works through a shell that reads as glass, and the whole point
       of a cutaway is that the shell is the least interesting thing in it.
       alpha is what makes it a cutaway rather than a barrel. */
    /* 0.20 was right for one pane and wrong for a casing: a barrel, its ribs,
       two end covers and a foot stack up to six layers of glass between the eye
       and the rotors, and six times 0.20 is a fog. The shell still reads --
       there is enough of it, from enough angles -- and the works behind it are
       now the brightest thing in the frame, which is the point of a cutaway. */
    { base: [ 96, 132, 176], hi: [176, 214, 255], alpha: 0.10 }, // GHOST
    { base: [ 74,  78,  92], hi: [255, 255, 255], smooth: true }, // ROTOR
    /* GAS. Not a colour on a part -- a colour along the LENGTH of one. In a
       screw compressor the pocket between the rotors gets smaller as it
       travels from the suction end to the discharge end, and everything that
       matters about the machine is in that one fact. Cold blue where the gas
       comes in, hot magenta where it leaves, which is the convention every
       manufacturer's cutaway uses and the one a refrigeration engineer reads
       without being told. */
    { grad: [[112, 176, 255], [255, 64, 150]], smooth: true }    // GAS
  ];
  var LIGHT = norm([-0.42, 0.78, 0.46]);
  var FILL  = norm([0.6, -0.2, -0.7]);

  function norm(v) {
    var m = Math.hypot(v[0], v[1], v[2]) || 1;
    return [v[0] / m, v[1] / m, v[2] / m];
  }

  /* ---------- projection ---------- */
  var yaw = -1.22, pitch = 0.30, autoYaw = true;
  /* Measured off the vertices rather than typed in. As constants they were the
     reciprocating machine's centre and size, so the screw compressor -- longer,
     twice as deep and with its axis somewhere else entirely -- was framed for a
     machine it is not, and came out over the edges on all four sides. */
  var CX = 0, CY = 0, CZ = 0, SPAN = 700;
  function measureModel(){
    var lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity], k, a;
    for (k = 0; k < V.length; k += 3) {
      for (a = 0; a < 3; a++) {
        if (V[k + a] < lo[a]) lo[a] = V[k + a];
        if (V[k + a] > hi[a]) hi[a] = V[k + a];
      }
    }
    CX = (lo[0] + hi[0]) / 2; CY = (lo[1] + hi[1]) / 2; CZ = (lo[2] + hi[2]) / 2;
    DX = hi[0] - lo[0]; DY = hi[1] - lo[1]; DZ = hi[2] - lo[2];
    SPAN = Math.max(1, Math.hypot(DX, DY, DZ));
  }
  var DX = 700, DY = 360, DZ = 330;
  var DIST = 1750, FOCAL = 2140;
  /* the steepest the drag is allowed to reach; the fit has to survive it */
  var PITCH_MAX = 0.62;
  /* FOCAL was a constant, which is only ever right at one canvas width: the
     machine sat well in a 1392px stage and on a phone it was three times the
     canvas and ran off every edge. Tying it to the width keeps the machine at
     the same fraction of the frame everywhere; the narrow case backs off a
     little further to leave the callout columns somewhere to live. */
  function refocus() {
    // Width alone was enough while the stage was 16/9. It is sized off the
    // viewport now, so on a short screen the width term asks for a machine
    // taller than the canvas and the cylinder heads leave the top of it. The
    // model stands about 360 units tall; the height term keeps that inside
    // four fifths of the frame whatever the shape of the box.
    /* Measured, not derived. Two closed-form attempts were both wrong in the
       same direction: the bounding sphere reserved the 895-unit diagonal for a
       shape 360 tall, and the axis version then counted the footprint diagonal
       twice, once as width and again as the depth the pitch tips into view.
       Each made the machine about half the size it should be.

       Projection is linear in FOCAL, so the extents can be measured once at
       FOCAL = 1 across the orientations this thing can actually reach, and the
       answer read off. Exact, no tuning, and it cannot be wrong about a
       machine it has never seen. */
    FOCAL = fitFocal(W, H);
    // 3.42 put the deep three-quarter at 97% of the canvas height: not
    // clipped, but one rounding away from it, and the cylinder heads are the
    // first thing to go. The projected height changes as it turns, so the
    // limit has to hold at the tallest angle, not the one on screen now.
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

  var OFFX = 0, OFFY = 0;
  var YAW0 = -1.22, YAW_SWEEP = 1.02, scrollYaw = 0;

  /* Sampled across the orientations this machine actually presents, not all of
     them. Sampling the full turn was tried and it fits for the end-on view,
     which the scroll never reaches and a drag reaches only if somebody works
     at it -- the machine came out at a third of the frame for a case that does
     not happen. This covers the scroll sweep with 35 degrees of margin either
     side; drag past that and an edge may cross the frame, which is a fair
     price for the machine being the size it should be the rest of the time. */
  function fitFocal(w, h){
    var maxW = 1e-6, maxH = 1e-6, i, j, k;
    var from = YAW0 - 0.6, to = YAW0 + YAW_SWEEP + 0.6;
    for (i = 0; i <= 12; i++) {
      var y = from + (to - from) * (i / 12);
      for (j = 0; j < 2; j++) {
        var pch = j ? PITCH_MAX : -0.12;
        var cy = Math.cos(y), sy = Math.sin(y), cp = Math.cos(pch), sp = Math.sin(pch);
        var lox = Infinity, hix = -Infinity, loy = Infinity, hiy = -Infinity;
        for (k = 0; k < V.length; k += 3) {
          var x = V[k] - CX, yy = V[k + 1] - CY, z = V[k + 2] - CZ;
          var x1 = x * cy + z * sy, z1 = -x * sy + z * cy;
          var y2 = yy * cp - z1 * sp, z2 = yy * sp + z1 * cp + DIST;
          /* at FOCAL = 1; the real value is a multiplier on both */
          var sx = x1 / z2, syv = -y2 / z2;
          if (sx < lox) lox = sx; if (sx > hix) hix = sx;
          if (syv < loy) loy = syv; if (syv > hiy) hiy = syv;
        }
        if (hix - lox > maxW) maxW = hix - lox;
        if (hiy - loy > maxH) maxH = hiy - loy;
      }
    }
    /* The fit is already conservative -- it reserves room for the steepest
       pitch a drag can reach, while the machine sits at a gentler one almost
       all the time -- so the fill factors can be generous without the worst
       case crossing the frame. At 0.92/0.88 the machine sat at two thirds of
       the height it had room for and looked lost in a wide stage. */
    return Math.min(w * 1.02 / maxW, h * 1.06 / maxH);
  }

  /* Written straight into V from the stored originals. The projection reads V
     and knows nothing about any of this. */
  function animateParts(t){
    if (!PARTS.length) return;
    for (var p = 0; p < PARTS.length; p++) {
      var part = PARTS[p], o = part.orig, base = part.from, k;
      if (part.rule.spin != null) {
        var a = t * part.rule.spin, c = Math.cos(a), sn = Math.sin(a);
        var cy = part.rule.cy, cz = part.rule.cz;
        for (k = 0; k < o.length; k += 3) {
          var y = o[k + 1] - cy, z = o[k + 2] - cz;
          V[base + k]     = o[k];
          V[base + k + 1] = cy + y * c - z * sn;
          V[base + k + 2] = cz + y * sn + z * c;
        }
      } else if (part.rule.slide != null) {
        /* eased, not linear: a hydraulic ram does not start and stop dead */
        var d = part.rule.slide * (0.5 - 0.5 * Math.cos(t * 0.22));
        for (k = 0; k < o.length; k += 3) {
          V[base + k]     = o[k] + d;
          V[base + k + 1] = o[k + 1];
          V[base + k + 2] = o[k + 2];
        }
      }
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
    animateParts(SPIN_T);
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

    /* Centre on what is actually on screen, not on the model origin. A long
       object rotating about a fixed point does not stay put: side-on it is
       widest and sits one way, three-quarter it is narrower and sits the
       other, so across a scroll the machine wandered from the right of the
       frame to the left and the composition never settled. Measuring the
       projected bounds costs one pass over points already computed. */
    var minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity;
    for (j = 0; j < S.length; j += 2) {
      if (S[j] < minx) minx = S[j];
      if (S[j] > maxx) maxx = S[j];
      if (S[j + 1] < miny) miny = S[j + 1];
      if (S[j + 1] > maxy) maxy = S[j + 1];
    }
    OFFX = w / 2 - (minx + maxx) / 2;
    OFFY = h / 2 - (miny + maxy) / 2;

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    ctx.translate(OFFX, OFFY);
    ctx.lineJoin = "round";

    for (var o = 0; o < order.length; o++) {
      var f = F[order[o]], ix = f.i, n = ix.length;
      // face normal in view space; orient() guarantees it points out of the
      // part, so a face is visible exactly when it leans back toward the eye
      var p0 = ix[0] * 3, p1 = ix[1] * 3, p2 = ix[2] * 3;
      var ux = P[p1] - P[p0], uy = P[p1 + 1] - P[p0 + 1], uz = P[p1 + 2] - P[p0 + 2];
      var vx = P[p2] - P[p0], vy = P[p2 + 1] - P[p0 + 1], vz = P[p2 + 2] - P[p0 + 2];
      var nn = norm([uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx]);
      /* A solid part hides its own far side; glass does not, and culling the
         back of the casing left the shell looking like a shell only on the
         side facing you. */
      if (!TONE[f.t].alpha &&
          nn[0] * P[p0] + nn[1] * P[p0 + 1] + nn[2] * P[p0 + 2] >= 0) continue;
      var ax = S[ix[0] * 2], ay = S[ix[0] * 2 + 1];
      var t = TONE[f.t], L = shade(nn);
      var lo, hi;
      if (t.grad) {
        /* f.u is where along the machine this face was built, 0 at the suction
           end and 1 at the discharge end -- stored once, because the vertex it
           came from moves every frame and the colour must not. */
        var u = f.u || 0;
        lo = [
          t.grad[0][0] + (t.grad[1][0] - t.grad[0][0]) * u,
          t.grad[0][1] + (t.grad[1][1] - t.grad[0][1]) * u,
          t.grad[0][2] + (t.grad[1][2] - t.grad[0][2]) * u
        ];
        hi = [255, 255, 255];
      } else { lo = t.base; hi = t.hi; }
      /* The gas is lit at about half, so it keeps its colour: a stream run all
         the way to white at the highlight stops being blue or magenta exactly
         where it is brightest, which is where you were looking. Everything
         else takes the full range -- applied to all of them, as it was at
         first, this dimmed the entire machine by nearly half and the rotors
         went from steel to slate. */
      var k = t.grad ? 0.55 : 1;
      var r = Math.round(lo[0] + (hi[0] - lo[0]) * L * k);
      var g = Math.round(lo[1] + (hi[1] - lo[1]) * L * k);
      var b = Math.round(lo[2] + (hi[2] - lo[2]) * L * k);

      ctx.beginPath();
      ctx.moveTo(ax, ay);
      for (j = 1; j < n; j++) ctx.lineTo(S[ix[j] * 2], S[ix[j] * 2 + 1]);
      ctx.closePath();
      /* Back-to-front sorting is already what this renderer does, so a
         translucent face blends over whatever was painted before it and the
         casing simply works -- provided the shell really is sorted behind and
         in front of the rotors rather than drawn as one lump, which is why
         each panel of it is its own box. */
      ctx.fillStyle = t.alpha
        ? "rgba(" + r + "," + g + "," + b + "," + t.alpha + ")"
        : "rgb(" + r + "," + g + "," + b + ")";
      ctx.fill();
      // The edge is what makes it read as a machined part rather than a blob.
      // Stroking every face at low alpha gives the creases for free.
      if (!t.smooth) {
        ctx.strokeStyle = t.alpha
          ? "rgba(150,196,255," + (0.05 + L * 0.14).toFixed(3) + ")"
          : "rgba(238,240,244," + (0.05 + L * 0.22).toFixed(3) + ")";
        ctx.lineWidth = 1;
        ctx.stroke();
      } else {
        /* A hairline of its own fill closes the seam between neighbouring
           quads -- without it a swept surface shows a pale grid of gaps where
           the antialiasing of two adjacent fills does not quite meet. */
        ctx.strokeStyle = ctx.fillStyle;
        ctx.lineWidth = 1;
        ctx.stroke();
      }
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
        sx: OFFX + x1 * FOCAL / z2,
        sy: OFFY - y2 * FOCAL / z2,
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

  /* The reference site turns its camera on scroll, and that is the half of it
     worth having: the machine answers the page rather than spinning at its
     own pace regardless of the reader. Progress is measured over the span
     where the section is crossing the screen, so a full pass turns it about
     a third of a revolution; the idle drift continues on top, so it is never
     dead when the page is still. Drag takes over from both. */
  /* The sweep stays in three-quarter the whole way. Running it from -0.62
     through to +1.48 put the machine exactly side-on at the middle of the
     section -- the one angle at which a compressor reads as a rectangle --
     and that is where a reader spends longest. A shorter arc from a deeper
     three-quarter shows the same amount of turning and never flattens. */

  function readScroll() {
    var r = root.getBoundingClientRect();
    var span = r.height + window.innerHeight;
    if (span <= 0) return;
    var t = (window.innerHeight - r.top) / span;   // 0 entering, 1 leaving
    scrollYaw = Math.max(0, Math.min(1, t)) * YAW_SWEEP;
  }

  var last = 0, drift = 0, SPIN_T = 0;
  function frame(now) {
    raf = 0;
    if (!reduce.matches) {
      var dts = last ? Math.min(64, now - last) : 16;
      /* slow enough to follow a single lobe round, which is the whole point of
         watching it: a rotor spun at anything like its real 3,000 rpm is a
         blur, and a blur teaches nobody how a screw compressor works */
      SPIN_T += dts * 0.00075;
    }
    if (autoYaw && !reduce.matches) {
      var dt = last ? Math.min(64, now - last) : 16;
      drift += dt * 0.000055;
      yaw = YAW0 + scrollYaw + drift;
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
    // Rebase, or the moment the drift resumes the machine jumps back to
    // wherever the scroll said it should have been.
    YAW0 = yaw - scrollYaw - drift;
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

  window.addEventListener("resize", function () {
    size(); readScroll();
    if (!running) { draw(W, H, DPR); drawTags(W, H); }
  });
  // passive: this only reads, and a non-passive scroll listener on the main
  // thread is the classic way to make a page feel heavy under the finger
  window.addEventListener("scroll", function () {
    readScroll();
    if (!running && !reduce.matches) { draw(W, H, DPR); drawTags(W, H); }
  }, { passive: true });

  // Only runs while it is on screen. A render loop left going behind three
  // screens of scroll is a flat battery and nothing to show for it.
  size();
  readScroll();
  yaw = YAW0 + scrollYaw;
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
