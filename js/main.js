/* ============================================================
   LITPROFIT — main.js
   Header state, mobile menu, scroll reveals, enquiry form.
   No dependencies, no third-party requests.
   ============================================================ */
(function () {
  "use strict";

  /* ============================================================
     CONFIG — the only block that needs editing to go live.
     ============================================================ */

  /* Enquiry form delivery. A static site cannot send mail by itself.
     Leave "" and the form opens the visitor's own mail client with
     everything pre-filled, so it works from day one; set it to a
     Formspree/Netlify/Basin endpoint to receive submissions directly. */
  var FORM_ENDPOINT = ""; // e.g. "https://formspree.io/f/XXXXXXXX"

  /* Where the mailto fallback sends to. */
  var CONTACT_EMAIL = "info@litprofit.com";

  /* Company profiles. Leave "" and the link is removed from the page
     entirely, so nothing dead ever ships. */
  var SOCIAL = {
    linkedin: "",
    facebook: ""
  };

  /* Cookieless analytics. Leave "" and no third-party request is made at
     all — nothing to disclose, and no consent banner needed. */
  var ANALYTICS_DOMAIN = "";

  /* ============================================================ */

  var doc = document;

  function on(el, ev, fn) { if (el) el.addEventListener(ev, fn); }
  function all(sel, root) {
    return Array.prototype.slice.call((root || doc).querySelectorAll(sel));
  }

  /* ---------- header: solid once scrolled ---------- */
  var header = doc.querySelector(".site-header");
  if (header) {
    var stuck = false;
    var onScroll = function () {
      var should = window.scrollY > 12;
      if (should !== stuck) {
        stuck = should;
        header.classList.toggle("is-stuck", should);
      }
    };
    on(window, "scroll", onScroll, { passive: true });
    onScroll();
  }

  /* ---------- mobile menu ---------- */
  var burger = doc.querySelector(".burger");
  var links = doc.querySelector(".nav-links");

  function setMenu(open) {
    if (!burger || !links) return;
    links.classList.toggle("is-open", open);
    burger.setAttribute("aria-expanded", open ? "true" : "false");
    /* lock the page behind the menu, and restore the scroll position after —
       position:fixed on body would otherwise jump the visitor to the top */
    if (open) {
      doc.body.dataset.scrollY = String(window.scrollY);
      doc.body.style.overflow = "hidden";
    } else {
      doc.body.style.overflow = "";
    }
  }

  on(burger, "click", function () {
    setMenu(burger.getAttribute("aria-expanded") !== "true");
  });

  /* a tap on any menu link closes it */
  all(".nav-links a").forEach(function (a) {
    on(a, "click", function () { setMenu(false); });
  });

  on(doc, "keydown", function (e) {
    if (e.key === "Escape") setMenu(false);
  });

  /* the menu is only a mobile construct — leaving that width must clear it,
     or the page stays scroll-locked on rotate */
  var mq = window.matchMedia("(min-width: 981px)");
  var onMQ = function (e) { if (e.matches) setMenu(false); };
  if (mq.addEventListener) mq.addEventListener("change", onMQ);
  else if (mq.addListener) mq.addListener(onMQ);

  /* ---------- scroll reveals ---------- */
  var reveals = all(".reveal");
  if (reveals.length) {
    if (!("IntersectionObserver" in window)) {
      reveals.forEach(function (el) { el.classList.add("is-in"); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
      reveals.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---------- scroll: progress, parallax ----------
     Both are read-only decoration and both are skipped entirely when the
     visitor has asked for reduced motion — not merely shortened, since a
     parallax that still moves is exactly what that setting is about. */
  var ticking = false;
  var calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var bar = doc.querySelector(".progress");
  var heroImg = doc.querySelector(".hero-drawing");

  /* ---------- words light as the sentence crosses the screen ----------
     Split once, on load, into one span per word. textContent is read before
     anything is written back, so the markup carries the sentence and this only
     re-expresses it -- with scripting off, or if this never runs, the
     stylesheet's dim colour never applies either, because .w is what it keys
     on and .w only exists once this has run. */
  var lw = doc.querySelector(".lightwords");
  var lwWords = null;
  if (lw) {
    var parts = lw.textContent.trim().split(/\s+/);
    lw.textContent = "";
    parts.forEach(function (word, i) {
      var sp = doc.createElement("span");
      sp.className = "w";
      sp.textContent = word;
      lw.appendChild(sp);
      if (i < parts.length - 1) lw.appendChild(doc.createTextNode(" "));
    });
    lwWords = lw.querySelectorAll(".w");
    if (calm) {
      Array.prototype.forEach.call(lwWords, function (w) { w.classList.add("lit"); });
      lwWords = null;
    }
  }

  function paintWords() {
    if (!lwWords) return;
    var r = lw.getBoundingClientRect();
    var vh = window.innerHeight;
    /* 0 as it comes up past the lower third, 1 by the time it is mid-screen */
    var startAt = vh * 0.85, endAt = vh * 0.35;
    var p = (startAt - r.top) / (startAt - endAt);
    p = p < 0 ? 0 : p > 1 ? 1 : p;
    var lit = Math.round(p * lwWords.length);
    for (var i = 0; i < lwWords.length; i++) {
      lwWords[i].classList.toggle("lit", i < lit);
    }
  }


  function scrollFxFrame() {
    ticking = false;
    var d = doc.documentElement;

    paintWords();

    if (bar) {
      var max = d.scrollHeight - d.clientHeight;
      bar.style.setProperty("--p", max > 0 ? (window.scrollY / max).toFixed(4) : "0");
    }

    /* the hero drawing drifts at a fraction of the scroll rate, and only while
       the hero is still on screen — past that it is wasted work */
    if (heroImg && !calm) {
      var y = window.scrollY;
      if (y < d.clientHeight * 1.2) {
        heroImg.style.transform = "translate3d(0," + (y * 0.12).toFixed(1) + "px,0)";
      }
    }
  }

  function scrollFx() {
    if (!ticking) { ticking = true; window.requestAnimationFrame(scrollFxFrame); }
  }

  /* Stop the pipe flow once the hero has gone by. The animation is CSS, so it
     keeps its own time and simply resumes where it left off. */
  /* Both drawings idle when they are not on screen. A CSS animation on a
     scrolled-away element still repaints, and on an 8,000px page that is most
     of the time. */
  ["\u002ehero", ".vessel-section"].forEach(function (sel) {
    var el = doc.querySelector(sel);
    if (!el || !("IntersectionObserver" in window)) return;
    new IntersectionObserver(function (es) {
      el.classList.toggle("is-idle", !es[0].isIntersecting);
    }, { rootMargin: "120px" }).observe(el);
  });

  if (bar || heroImg || lwWords) {
    on(window, "scroll", scrollFx, { passive: true });
    on(window, "resize", scrollFx);
    scrollFxFrame();
  }

  /* ---------- booking ----------
     The button is a plain link to Calendly, so it works with JavaScript off,
     with the script blocked, and in a new tab. On click we upgrade it to
     Calendly's own popup — but the widget is fetched ONLY AT THAT MOMENT.

     That ordering is the point. Embedding the widget on page load would send
     every visitor's IP to Calendly whether or not they ever book, and this site
     otherwise makes no third-party request at all. Loading it on the click
     keeps that true for everyone who does not book, and the person who does has
     chosen to. If the fetch fails for any reason, nothing is trapped: the
     original link is followed instead. */
  var CALENDLY_CSS = "https://assets.calendly.com/assets/external/widget.css";
  var CALENDLY_JS = "https://assets.calendly.com/assets/external/widget.js";
  var calendlyLoading = null;

  function loadCalendly() {
    if (window.Calendly) return Promise.resolve();
    if (calendlyLoading) return calendlyLoading;
    calendlyLoading = new Promise(function (resolve, reject) {
      var css = doc.createElement("link");
      css.rel = "stylesheet";
      css.href = CALENDLY_CSS;
      doc.head.appendChild(css);

      var js = doc.createElement("script");
      js.src = CALENDLY_JS;
      js.async = true;
      js.onload = resolve;
      js.onerror = reject;
      doc.head.appendChild(js);

      /* a blocker can leave onerror unfired — do not hang on the click */
      setTimeout(function () { window.Calendly ? resolve() : reject(); }, 6000);
    });
    return calendlyLoading;
  }

  all("[data-book]").forEach(function (a) {
    on(a, "click", function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;  /* let them open a tab */
      if (calm) return;                       /* reduced motion: plain link, no overlay */
      e.preventDefault();
      var href = a.getAttribute("href");
      loadCalendly().then(function () {
        window.Calendly.initPopupWidget({ url: href });
      }).catch(function () {
        window.open(href, "_blank", "noopener");
      });
    });
  });

  /* ---------- client rail ----------
     Arrows scroll by one card. They disable at each end rather than sitting
     there doing nothing, which is the only honest state for a control that
     cannot act. Touch devices get no arrows at all — swiping is the gesture. */
  var rail = doc.getElementById("clientRail");
  if (rail) {
    var railBtns = all(".rail-btn");

    var syncRail = function () {
      var max = rail.scrollWidth - rail.clientWidth - 1;
      railBtns.forEach(function (b) {
        var back = b.getAttribute("data-rail") === "-1";
        b.disabled = back ? rail.scrollLeft <= 0 : rail.scrollLeft >= max;
      });
    };

    railBtns.forEach(function (b) {
      on(b, "click", function () {
        var card = rail.querySelector(".cc");
        var step = card ? card.getBoundingClientRect().width + 14 : 240;
        rail.scrollBy({ left: step * (+b.getAttribute("data-rail")), behavior: "smooth" });
      });
    });

    on(rail, "scroll", syncRail, { passive: true });
    on(window, "resize", syncRail);
    syncRail();
  }

  /* ---------- current year in the footer ---------- */
  all("[data-year]").forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });

  /* ---------- social links: render only what is configured ---------- */
  all("[data-social]").forEach(function (el) {
    var url = SOCIAL[el.getAttribute("data-social")];
    if (url) el.setAttribute("href", url);
    else if (el.parentNode) el.parentNode.removeChild(el);
  });

  /* ---------- forms ----------
     Two forms, one behaviour: the enquiry form on /contacts/ and the
     application form on /careers/. Both post to FORM_ENDPOINT when one is
     configured, and otherwise hand a fully composed message to the visitor's
     own mail client — so neither is ever a dead end. Written as a loop
     because a second copy of this logic is a second place to fix it. */
  [["enquiryForm", "formNote", "Enquiry from litprofit.com",
    ["name", "company", "phone", "email"]],
   ["applyForm", "applyNote", "Application via litprofit.com",
    ["name", "email", "phone", "role"]]].forEach(function (cfg) {
    var form = doc.getElementById(cfg[0]);
    if (!form) return;
    var note = doc.getElementById(cfg[1]);
    var subject = cfg[2], fields = cfg[3];

    var say = function (msg, cls) {
      if (!note) return;
      note.textContent = msg;
      note.className = "form-note" + (cls ? " " + cls : "");
    };

    on(form, "submit", function (e) {
      e.preventDefault();

      if (!form.checkValidity()) {
        say("Please complete the required fields.", "is-error");
        var bad = form.querySelector(":invalid");
        if (bad) bad.focus();
        return;
      }

      var data = new FormData(form);
      var get = function (k) { return (data.get(k) || "").toString().trim(); };

      if (FORM_ENDPOINT) {
        say("Sending\u2026");
        fetch(FORM_ENDPOINT, {
          method: "POST", body: data, headers: { Accept: "application/json" }
        }).then(function (res) {
          if (!res.ok) throw new Error("bad status " + res.status);
          form.reset();
          say("Thank you \u2014 we will come back to you shortly.", "is-ok");
        }).catch(function () {
          say("Something went wrong. Please email " + CONTACT_EMAIL + " directly.",
              "is-error");
        });
        return;
      }

      var lines = fields.map(function (f) {
        return f.charAt(0).toUpperCase() + f.slice(1) + ": " + get(f);
      });
      lines.push("", get("message"));

      window.location.href = "mailto:" + CONTACT_EMAIL +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(lines.join("\n"));

      say("Your mail client is opening with everything ready to send.", "is-ok");
    });
  });

  /* ---------- the general arrangement drawing ----------
     Hover or focus a part and it lights up in the drawing while the rest of
     the package fades back. Buttons rather than hover-only decoration, so it
     works from the keyboard and under a finger; aria-expanded carries the
     state, and the CSS opens the description off that same attribute.

     NB: this was lost once, silently — a slice that replaced the form handler
     ran from the form comment to the console signature and took this with it.
     Nothing threw, the buttons simply stopped doing anything. */
  var drawing = doc.getElementById("drawing");
  if (drawing) {
    var parts = all(".part", drawing);

    var select = function (btn) {
      parts.forEach(function (b) {
        b.setAttribute("aria-expanded", b === btn ? "true" : "false");
      });
      if (btn) drawing.setAttribute("data-active", btn.getAttribute("data-prt"));
      else drawing.removeAttribute("data-active");
    };

    parts.forEach(function (btn) {
      btn.setAttribute("aria-expanded", "false");
      on(btn, "mouseenter", function () { select(btn); });
      on(btn, "focus", function () { select(btn); });
      /* touch has no hover: a tap toggles, so the description is reachable */
      on(btn, "click", function () {
        select(btn.getAttribute("aria-expanded") === "true" ? null : btn);
      });
    });

    /* leaving the block clears it, unless the keyboard is still inside */
    on(drawing, "mouseleave", function () {
      if (!drawing.contains(doc.activeElement)) select(null);
    });
  }

  /* ---------- 1. the mark, in the console ----------
     Drawn from the monogram's own geometry. Developers, competitors and
     the occasional curious client open devtools; this is who built it. */
  try {
    /* The // device, raked at the monogram's own angle — a block letter
       would have said nothing particular about this company. */
    var mark = [
      "",
      "     ╱╱   ╱╱",
      "    ╱╱   ╱╱     L I T P R O F I T",
      "   ╱╱   ╱╱      Ship repair and maintenance, worldwide",
      "  ╱╱   ╱╱       Klaipeda, Lithuania // since 2010",
      " ╱╱   ╱╱",
      "                Site by ALDY",
      "                Double-click the hero for a work light",
      "                Type FROST to ice the place over",
      ""
    ].join("\n");
    console.log("%c" + mark, "color:#8d90a6;font-family:monospace;line-height:1.35");
  } catch (e) { /* console is not guaranteed to exist */ }

  /* ---------- 2. the work light ----------
     Double-click the hero. The plant drawing is held back so the headline
     keeps its contrast; this brightens a circle of it under the cursor, the
     way a hand lamp works over a print on a bench.

     It reveals a second, brighter copy of the same drawing. brightness() on
     the backdrop was tried first and is wrong on a dark ground: it amplifies
     the navy into a blue disc instead of picking out the lines. */
  var hero = doc.querySelector(".hero");
  var supportsLamp = window.CSS && CSS.supports &&
      (CSS.supports("mask-image", "radial-gradient(#000,#000)") ||
       CSS.supports("-webkit-mask-image", "radial-gradient(#000,#000)"));

  if (hero && supportsLamp) {
    var lampOn = false, lampPending = null, lx = 0, ly = 0;

    var place = function () {
      lampPending = null;
      hero.style.setProperty("--mx", lx + "px");
      hero.style.setProperty("--my", ly + "px");
    };

    var track = function (e) {
      var r = hero.getBoundingClientRect();
      lx = Math.round(e.clientX - r.left);
      ly = Math.round(e.clientY - r.top);
      /* one write per frame — pointermove fires far faster than the screen
         repaints, and each custom-property write invalidates style */
      if (!lampPending) lampPending = window.requestAnimationFrame(place);
    };

    on(hero, "pointermove", function (e) { if (lampOn) track(e); });

    /* The visible control. Same toggle the double-click drives, so the two
       cannot disagree; when it turns the lamp on from a button press there is
       no pointer position yet, so it starts under the button itself and then
       follows the pointer as usual. */
    var lampBtn = doc.getElementById("lampToggle");
    var paintLamp = function () {
      hero.classList.toggle("is-lamp", lampOn);
      if (lampBtn) {
        lampBtn.setAttribute("aria-pressed", lampOn ? "true" : "false");
        var t = lampBtn.getAttribute(lampOn ? "data-off" : "data-on");
        if (t) lampBtn.setAttribute("title", t);
      }
    };
    if (lampBtn) {
      on(lampBtn, "click", function (e) {
        lampOn = !lampOn;
        if (lampOn) {
          var b = lampBtn.getBoundingClientRect(), r = hero.getBoundingClientRect();
          lx = Math.round(b.left + b.width / 2 - r.left);
          ly = Math.round(b.top + b.height / 2 - r.top);
          place();
        }
        paintLamp();
        e.stopPropagation();
      });
    }

    on(hero, "dblclick", function (e) {
      /* never swallow a double-click meant for a link or a button */
      if (e.target.closest && e.target.closest("a, button")) return;
      /* a double-click selects the word under the cursor; the lamp is not a
         text gesture, so drop the selection it just made */
      e.preventDefault();
      if (window.getSelection) window.getSelection().removeAllRanges();
      lampOn = !lampOn;
      paintLamp();
      if (lampOn) track(e);
    });

    /* moving off the hero puts the lamp away */
    on(hero, "pointerleave", function () {
      if (!lampOn) return;
      lampOn = false;
      paintLamp();
    });
  }

  /* ---------- 3. frost ----------
     Type FROST. Ice ferns grow in from the four corners, crystals drift, the
     page cools, and a probe readout falls from deck temperature to the
     -25 C an RSW tank or blast freezer actually runs at. It thaws by itself
     after eleven seconds — an easter egg you cannot get out of is a bug.

     Deliberately instrument-like rather than decorative: corner registration
     marks, a readout panel, sparse ice grains. An earlier version grew
     dendritic frost ferns across the screen; it looked like a Christmas card
     rather than a plant on test, and was cut. */
  var FSEQ = "FROST";
  var ftyped = "";
  var frostTimer = null;

  function buildIce() {
    var wrap = doc.createElement("div");
    wrap.id = "frostIce";
    wrap.setAttribute("aria-hidden", "true");

    /* A test banner across the top, so the mode announces itself. Without it
       the cold read as "nothing happened" — the earlier ferns were doing all
       the signalling, and cutting them left the effect invisible. */
    var banner = doc.createElement("div");
    banner.className = "cold-bar";
    banner.innerHTML =
      '<span>Cold test</span><span class="cb-sep">//</span>' +
      '<span>RSW circuit</span><span class="cb-sep">//</span>' +
      '<span>Setpoint &minus;25 &deg;C</span><span class="cb-sep">//</span>' +
      '<span class="cb-live">Recording</span>';
    wrap.appendChild(banner);

    /* registration marks at the corners — a print convention, not a
       snowflake. This is a plant under test, not a Christmas card. */
    ["tl", "tr", "bl", "br"].forEach(function (corner) {
      var m = doc.createElement("span");
      m.className = "reg reg-" + corner;
      wrap.appendChild(m);
    });

    for (var i = 0; i < 9; i++) {
      var f = doc.createElement("span");
      f.className = "flake";
      f.style.left = (5 + i * 10.6) + "%";
      f.style.animationDelay = (i * 0.9) + "s";
      f.style.animationDuration = (11 + (i % 4) * 3) + "s";
      wrap.appendChild(f);
    }
    return wrap;
  }

  function buildProbe() {
    var probe = doc.createElement("div");
    probe.id = "frostProbe";
    probe.setAttribute("aria-hidden", "true");
    probe.innerHTML =
      '<span class="fp-label">RSW tank <span class="fp-sep">//</span> probe</span>' +
      '<span class="fp-row"><span class="fp-t">18</span><span class="fp-u">&deg;C</span></span>' +
      '<span class="fp-state">Cooling</span>';
    return probe;
  }

  var paintFrostBtn = null;


  /* ============================================================
     REFRACTION  —  the frost probe only
     ------------------------------------------------------------
     The refraction field is a port of the fragment shader in liquid-glass-js
     (https://github.com/dashersw/liquid-glass-js) — Copyright (c) 2025 Armagan
     Amcalar, MIT. Permission is hereby granted, free of charge, to any person
     obtaining a copy of that software to deal in it without restriction,
     provided this notice travels with it; it is provided "as is", without
     warranty of any kind. Keep this header on any copy or port.

     CSS has no primitive for bending a backdrop, so this builds one: bake a
     displacement map into a canvas, encode the x/y offset per pixel into the
     R and G channels, and hand it to feDisplacementMap as a backdrop-filter.
     Because it filters the BACKDROP, the source is the live page — scrolling,
     the frost gradient animating in, all of it tracks for free.

     Scoped to one element on purpose. It is Chromium-only (Safari parses the
     SVG-referenced filter and paints nothing, so @supports cannot be used to
     detect it), and it bakes a canvas per element size. The probe is 175x97,
     appears only while the easter egg runs, and is the one surface here where
     glass is the subject rather than a finish. Everywhere else keeps the
     stylesheet's plain blur, which is what Safari and Firefox see here too.
     ============================================================ */
  var GLASS = {
    edgeIntensity: 0.015, rimIntensity: 0.028, baseIntensity: 0.05,
    edgeDistance: 0.5, rimDistance: 1.7, baseDistance: 0.2,
    cornerBoost: 0.06, rippleEffect: 0.26, blurRadius: 2, warp: false
  };
  var SUPERSAMPLE = 2, MAX_MAP_EDGE = 1400, BLUR_STD_PER_RADIUS = 0.35;

  /* Chromium only. Not a feature query: Safari accepts the declaration and
     draws nothing, so @supports reports success and the panel goes blank. */
  function canRefract() {
    var b = navigator.userAgentData && navigator.userAgentData.brands;
    if (b) {
      for (var i = 0; i < b.length; i++) {
        if (/Chromium|Google Chrome|Microsoft Edge/.test(b[i].brand)) return true;
      }
      return false;
    }
    return /Chrome\//.test(navigator.userAgent) && !/Edge\//.test(navigator.userAgent);
  }

  var refractDefs = null, refractSeq = 0;

  function bakeRefraction(el) {
    var r = el.getBoundingClientRect();
    var w = Math.round(r.width), h = Math.round(r.height);
    if (!w || !h) return null;

    /* CSS stays the single source of shape — read the radius rather than
       taking it as an argument. */
    var cs = getComputedStyle(el);
    var radius = parseFloat(cs.borderTopLeftRadius) || 0;
    if (/%$/.test(cs.borderTopLeftRadius)) radius = Math.min(w, h) * radius / 100;
    radius = Math.min(radius, Math.min(w, h) / 2);

    /* Displacement is in fractions of the page texture, whose live equivalent
       is the viewport — which is why this rebuilds on window resize, not only
       on element resize. */
    var pageW = window.innerWidth, pageH = window.innerHeight;
    var factor = Math.max(0.25, Math.min(SUPERSAMPLE, MAX_MAP_EDGE / Math.max(w, h)));
    var mw = Math.max(1, Math.round(w * factor)), mh = Math.max(1, Math.round(h * factor));

    var cv = doc.createElement("canvas");
    cv.width = mw; cv.height = mh;
    var ctx = cv.getContext("2d");
    var img = ctx.createImageData(mw, mh);
    var data = img.data;
    var dxs = new Float32Array(mw * mh), dys = new Float32Array(mw * mh);
    var maxAbs = 0, minEdge = Math.min(w, h);

    for (var y = 0; y < mh; y++) {
      for (var x = 0; x < mw; x++) {
        var px = (x + 0.5) / factor, py = (y + 0.5) / factor;
        var cx = px / w, cy = py / h;

        /* signed distance to the rounded rectangle, clamped at the edge */
        var tx = Math.abs(px - w / 2) - (w / 2 - radius);
        var ty = Math.abs(py - h / 2) - (h / 2 - radius);
        var outer = Math.hypot(Math.max(tx, 0), Math.max(ty, 0));
        var distPx = Math.max(-(outer + Math.min(Math.max(tx, ty), 0) - radius), 0);

        var edgeFall = Math.exp(-distPx * GLASS.edgeDistance);
        var rimFall = Math.exp(-distPx * GLASS.rimDistance);
        var baseFall = 1 - Math.exp(-distPx * GLASS.baseDistance);

        /* warp stays off: centre distortion looks impressive on a demo tile
           and makes anything under the middle of the panel unreadable */
        var total = (GLASS.warp ? baseFall * GLASS.baseIntensity : 0) +
                    edgeFall * GLASS.edgeIntensity + rimFall * GLASS.rimIntensity;

        var nx = cx - 0.5, ny = cy - 0.5;
        var nlen = Math.hypot(nx, ny) || 1;
        nx /= nlen; ny /= nlen;

        var corner = Math.exp(-(Math.max(Math.min(cx, 1 - cx), Math.min(cy, 1 - cy)) *
                                minEdge) * 0.3) * GLASS.cornerBoost;
        var ripple = Math.sin((distPx / minEdge) * 25) * GLASS.rippleEffect * rimFall;

        var dx = (nx * (total + corner) - ny * ripple) * pageW;
        var dy = (ny * (total + corner) + nx * ripple) * pageH;

        var i = y * mw + x;
        dxs[i] = dx; dys[i] = dy;
        var a = Math.max(Math.abs(dx), Math.abs(dy));
        if (a > maxAbs) maxAbs = a;
      }
    }

    /* feDisplacementMap decodes b as scale*(b/255 - 0.5), and the obvious
       neutral 128 is NOT zero: 128/255 = 0.50196, so a flat interior would
       drift by scale/510 px. With warp off the middle is supposed to be
       perfectly undistorted, and that drift is exactly what you would see. */
    var scale = Math.max(maxAbs * 2, 1e-4);
    var bias = scale * (128 / 255 - 0.5);
    for (var k = 0; k < mw * mh; k++) {
      var o = k * 4;
      data[o]     = Math.max(0, Math.min(255, Math.round(255 * (0.5 + (dxs[k] - bias) / scale))));
      data[o + 1] = Math.max(0, Math.min(255, Math.round(255 * (0.5 + (dys[k] - bias) / scale))));
      data[o + 2] = 128;
      data[o + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);

    /* Edge pixels sample up to scale/2 away plus the blur spread. A region
       that stops at the box clips the refraction to transparent at the
       corners — and displacement is viewport-proportional, so on an element
       this small the margin can exceed the box. Size it from the field. */
    var margin = scale / 2 + 3 * GLASS.blurRadius * BLUR_STD_PER_RADIUS;
    var mx = (margin / w) * 100, my = (margin / h) * 100;

    if (!refractDefs || !refractDefs.isConnected) {
      var svg = doc.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("aria-hidden", "true");
      svg.setAttribute("width", "0"); svg.setAttribute("height", "0");
      svg.style.cssText = "position:absolute;width:0;height:0;overflow:hidden";
      refractDefs = doc.createElementNS("http://www.w3.org/2000/svg", "defs");
      svg.appendChild(refractDefs);
      doc.body.appendChild(svg);
    }

    var id = "lg-refract-" + (++refractSeq);
    var NS = "http://www.w3.org/2000/svg";
    var f = doc.createElementNS(NS, "filter");
    f.setAttribute("id", id);
    f.setAttribute("filterUnits", "objectBoundingBox");
    f.setAttribute("x", (-mx) + "%"); f.setAttribute("y", (-my) + "%");
    f.setAttribute("width", (100 + mx * 2) + "%");
    f.setAttribute("height", (100 + my * 2) + "%");

    var fe = doc.createElementNS(NS, "feImage");
    fe.setAttribute("result", "map");
    fe.setAttribute("preserveAspectRatio", "none");
    /* A primitive with no subregion fills the FILTER REGION, and this region
       is deliberately ~216% of the box so the corners are not clipped. Left
       unset, the map was being stretched across all of that -- putting its
       1-2px rim band well outside the element, which is why the displacement
       measured 13/255 over a gradient and 12 over a photograph: it was bending
       the wrong pixels. primitiveUnits is userSpaceOnUse by default, so pin it
       to the box in user units. */
    fe.setAttribute("x", "0"); fe.setAttribute("y", "0");
    fe.setAttribute("width", String(w)); fe.setAttribute("height", String(h));
    fe.setAttributeNS("http://www.w3.org/1999/xlink", "href", cv.toDataURL());
    fe.setAttribute("href", cv.toDataURL());

    var dm = doc.createElementNS(NS, "feDisplacementMap");
    dm.setAttribute("in", "SourceGraphic"); dm.setAttribute("in2", "map");
    dm.setAttribute("scale", String(scale));
    dm.setAttribute("xChannelSelector", "R"); dm.setAttribute("yChannelSelector", "G");
    dm.setAttribute("result", "disp");

    var gb = doc.createElementNS(NS, "feGaussianBlur");
    gb.setAttribute("in", "disp");
    gb.setAttribute("stdDeviation", String(GLASS.blurRadius * BLUR_STD_PER_RADIUS));

    f.appendChild(fe); f.appendChild(dm); f.appendChild(gb);
    refractDefs.appendChild(f);

    if (el._lgFilter && el._lgFilter.parentNode) {
      el._lgFilter.parentNode.removeChild(el._lgFilter);
    }
    el._lgFilter = f;
    /* url() ALONE, replacing the stylesheet's blur(10px) saturate(130%)
       outright. Chaining a blur in front of it seemed obviously right -- keep
       the frosting, add the bend -- and it is wrong: a blur smooths the
       backdrop, and displacement of an already-smooth image moves nothing you
       can see. Measured over the same frame, the displacement's own
       contribution was max 26/255 across 7470 pixels with no pre-blur, and
       10-13 across ~1200 with blur(3px) or blur(9px) in front. The pre-blur
       was erasing the effect it was meant to accompany.

       So the frosting is the filter's own feGaussianBlur, which is why it sits
       AFTER the displacement in the chain and why it is small. Text stays
       readable on the panel's own rgba(7,8,36,0.78) ground, not on blur. */
    el.style.backdropFilter = "url(#" + id + ")";
    el.style.webkitBackdropFilter = "url(#" + id + ")";
    return f;
  }

  function releaseRefraction(el) {
    if (!el) return;
    if (el._lgResize) { window.removeEventListener("resize", el._lgResize); el._lgResize = null; }
    if (el._lgFilter && el._lgFilter.parentNode) {
      el._lgFilter.parentNode.removeChild(el._lgFilter);
    }
    el._lgFilter = null;
  }

  function refract(el) {
    if (!el || !canRefract()) return;
    bakeRefraction(el);
    /* the window resize changes pageW/pageH for the whole field at once, so
       debounce it rather than rebaking on every frame of a drag */
    var t = null;
    el._lgResize = function () {
      clearTimeout(t);
      t = setTimeout(function () { if (el.isConnected) bakeRefraction(el); }, 180);
    };
    window.addEventListener("resize", el._lgResize);
  }

  function setFrost(on) {
    var root = doc.documentElement;
    root.classList.toggle("is-frost", on);
    if (paintFrostBtn) paintFrostBtn(on);

    var ice = doc.getElementById("frostIce");
    var probe = doc.getElementById("frostProbe");

    if (on) {
      if (!ice) doc.body.appendChild(buildIce());
      if (!probe) {
        probe = buildProbe();
        doc.body.appendChild(probe);
        /* after layout, so the bake reads the real box */
        requestAnimationFrame(function () { refract(probe); });
      }

      var t = 18, target = -25;
      var readout = probe.querySelector(".fp-t");
      var state = probe.querySelector(".fp-state");
      clearInterval(probe._iv);
      probe._iv = setInterval(function () {
        t -= 1;
        readout.textContent = String(t);
        if (t <= 0) probe.classList.add("is-below");
        if (t <= target) {
          clearInterval(probe._iv);
          state.textContent = "Holding";
          probe.classList.add("is-held");
        }
      }, 60);

      clearTimeout(frostTimer);
      frostTimer = setTimeout(function () { setFrost(false); }, 11000);
    } else {
      clearTimeout(frostTimer);
      [ice, probe].forEach(function (el) {
        if (!el) return;
        if (el._iv) clearInterval(el._iv);
        releaseRefraction(el);
        el.classList.add("is-out");
        setTimeout(function () {
          if (el && el.parentNode) el.parentNode.removeChild(el);
        }, 1100);
      });
    }
  }

  /* The button and the typed word are the same switch, so the button's state
     has to follow setFrost rather than its own click -- the effect also times
     out after eleven seconds, and an aria-pressed left at true would be
     telling a screen reader the page is still iced when it is not. */
  var frostBtn = doc.getElementById("frostToggle");
  if (frostBtn) {
    on(frostBtn, "click", function () {
      setFrost(!doc.documentElement.classList.contains("is-frost"));
    });
    paintFrostBtn = function (on_) {
      frostBtn.setAttribute("aria-pressed", on_ ? "true" : "false");
      var label = frostBtn.getAttribute(on_ ? "data-off" : "data-on");
      if (label) frostBtn.setAttribute("title", label);
    };
  }

  on(doc, "keydown", function (e) {
    var ft = e.target;
    if (ft && /^(INPUT|TEXTAREA|SELECT)$/.test(ft.tagName)) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (!e.key || e.key.length !== 1) return;
    ftyped = (ftyped + e.key.toUpperCase()).slice(-FSEQ.length);
    if (ftyped === FSEQ) {
      setFrost(!doc.documentElement.classList.contains("is-frost"));
      ftyped = "";
    }
  });

  /* ---------- analytics (opt-in, cookieless) ---------- */
  if (ANALYTICS_DOMAIN) {
    var s = doc.createElement("script");
    s.defer = true;
    s.setAttribute("data-domain", ANALYTICS_DOMAIN);
    s.src = "https://plausible.io/js/script.js";
    doc.head.appendChild(s);
  }
})();
