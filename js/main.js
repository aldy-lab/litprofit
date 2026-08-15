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
  var heroImg = doc.querySelector(".hero-media img");

  function scrollFxFrame() {
    ticking = false;
    var d = doc.documentElement;

    if (bar) {
      var max = d.scrollHeight - d.clientHeight;
      bar.style.setProperty("--p", max > 0 ? (window.scrollY / max).toFixed(4) : "0");
    }

    /* the hero photograph drifts at a fraction of the scroll rate, and only
       while the hero is still on screen — past that it is wasted work */
    if (heroImg && !calm) {
      var y = window.scrollY;
      if (y < d.clientHeight * 1.2) {
        heroImg.style.transform = "translate3d(0," + (y * 0.16).toFixed(1) + "px,0) scale(1.06)";
      }
    }
  }

  function scrollFx() {
    if (!ticking) { ticking = true; window.requestAnimationFrame(scrollFxFrame); }
  }

  if (bar || heroImg) {
    on(window, "scroll", scrollFx, { passive: true });
    on(window, "resize", scrollFx);
    scrollFxFrame();
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

  /* ---------- enquiry form ---------- */
  var form = doc.getElementById("enquiryForm");
  if (form) {
    var note = doc.getElementById("formNote");

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
        say("Sending…");
        fetch(FORM_ENDPOINT, {
          method: "POST",
          body: data,
          headers: { Accept: "application/json" }
        }).then(function (res) {
          if (!res.ok) throw new Error("bad status " + res.status);
          form.reset();
          say("Thank you — we will come back to you shortly.", "is-ok");
        }).catch(function () {
          say("Something went wrong. Please email " + CONTACT_EMAIL + " directly.", "is-error");
        });
        return;
      }

      /* No endpoint configured: hand the enquiry to the visitor's mail
         client, fully composed. */
      var body = [
        "Name: " + get("name"),
        "Company: " + get("company"),
        "Phone: " + get("phone"),
        "Email: " + get("email"),
        "",
        get("message")
      ].join("\n");

      window.location.href = "mailto:" + CONTACT_EMAIL +
        "?subject=" + encodeURIComponent("Enquiry from litprofit.com") +
        "&body=" + encodeURIComponent(body);

      say("Your mail client is opening with the enquiry ready to send.", "is-ok");
    });
  }


  /* ---------- the general arrangement drawing ----------
     Hover or focus a part and it lights up in the drawing, the rest fading back.
     aria-expanded carries the open/closed state, so the control reports what
     it does rather than only looking like it. */
  var drawing = doc.getElementById("drawing");
  if (drawing) {
    var stages = all(".part", drawing);

    var select = function (btn) {
      stages.forEach(function (b) {
        b.setAttribute("aria-expanded", b === btn ? "true" : "false");
      });
      if (btn) drawing.setAttribute("data-active", btn.getAttribute("data-prt"));
      else drawing.removeAttribute("data-active");
    };

    stages.forEach(function (btn) {
      btn.setAttribute("aria-expanded", "false");
      on(btn, "mouseenter", function () { select(btn); });
      on(btn, "focus", function () { select(btn); });
      /* click keeps it open on touch, where there is no hover at all */
      on(btn, "click", function () {
        select(btn.getAttribute("aria-expanded") === "true" ? null : btn);
      });
    });

    on(drawing, "mouseleave", function () {
      /* do not yank the panel away from someone reading it via the keyboard */
      if (!drawing.contains(doc.activeElement)) select(null);
    });
  }

  /* ============================================================
     HIDDEN — things that reward a second look.
     None of it is announced, none of it is required, and none of it
     changes what the page says. All of it is keyboard- and
     reduced-motion-safe, and nothing here runs for a visitor who never
     goes looking.
     ============================================================ */

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
     Double-click the hero. The photograph sits at 30% under a heavy gradient;
     a second copy at full strength is revealed inside a soft circle that
     follows the pointer. Nothing announces it, and it costs nothing until it
     is switched on. */
  var hero = doc.querySelector(".hero");
  if (hero && CSS && CSS.supports && (CSS.supports("mask-image", "radial-gradient(#000,#000)") ||
                                      CSS.supports("-webkit-mask-image", "radial-gradient(#000,#000)"))) {
    var lampOn = false, pending = null, lx = 0, ly = 0;

    var place = function () {
      pending = null;
      hero.style.setProperty("--mx", lx + "px");
      hero.style.setProperty("--my", ly + "px");
    };

    on(hero, "pointermove", function (e) {
      if (!lampOn) return;
      var r = hero.getBoundingClientRect();
      lx = Math.round(e.clientX - r.left);
      ly = Math.round(e.clientY - r.top);
      /* one write per frame — pointermove fires far faster than the screen
         repaints, and setting a custom property invalidates style each time */
      if (!pending) pending = window.requestAnimationFrame(place);
    });

    on(hero, "dblclick", function (e) {
      /* never swallow a double-click meant for a link or a button */
      if (e.target.closest && e.target.closest("a, button")) return;
      lampOn = !lampOn;
      hero.classList.toggle("is-lamp", lampOn);
      if (lampOn) {
        var r = hero.getBoundingClientRect();
        lx = Math.round(e.clientX - r.left);
        ly = Math.round(e.clientY - r.top);
        place();
      }
    });

    /* moving the pointer off the hero puts the lamp away */
    on(hero, "pointerleave", function () {
      if (!lampOn) return;
      lampOn = false;
      hero.classList.remove("is-lamp");
    });
  }

  /* ---------- 3. frost ----------
     Type FROST. Ice ferns grow in from the four corners, crystals drift, the
     page cools, and a probe readout falls from deck temperature to the
     -25 C an RSW tank or blast freezer actually runs at. It thaws by itself
     after eleven seconds — an easter egg you cannot get out of is a bug.

     The fern is a dendrite: a stem with recursively smaller side branches at
     a fixed angle, which is roughly how ice actually grows on glass. It was
     generated once rather than drawn, and is baked in here as path data so
     nothing has to compute it at runtime. */
  var FERN = "M0.0 0.0L43.8 43.8M8.8 8.8L30.8 3.7M13.2 7.8L15.8 -0.0M13.7 6.2L11.8 3.9M13.7 6.2L16.6 5.5M14.2 4.6L12.5 2.6M14.2 4.6L16.9 4.0M15.8 -0.0L17.7 -5.5M13.2 7.8L19.0 13.6M14.3 8.9L17.2 8.2M14.3 8.9L13.7 11.8M15.5 10.1L18.1 9.5M15.5 10.1L14.9 12.7M19.0 13.6L23.0 17.6M17.6 6.7L20.0 -0.3M18.0 5.3L16.4 3.2M18.0 5.3L20.7 4.7M20.0 -0.3L21.7 -5.2M17.6 6.7L22.8 12.0M18.6 7.8L21.2 7.2M18.6 7.8L18.0 10.4M22.8 12.0L26.5 15.6M22.0 5.7L24.1 -0.5M24.1 -0.5L25.6 -4.9M22.0 5.7L26.6 10.4M26.6 10.4L29.9 13.6M26.4 4.7L28.2 -0.8M28.2 -0.8L29.6 -4.6M26.4 4.7L30.4 8.8M30.4 8.8L33.3 11.7M30.8 3.7L46.2 0.1M33.8 3.0L35.7 -2.5M33.8 3.0L37.9 7.0M36.9 2.3L38.6 -2.6M36.9 2.3L40.6 5.9M40.0 1.6L41.5 -2.8M40.0 1.6L43.3 4.8M43.1 0.8L44.4 -3.0M43.1 0.8L45.9 3.7M46.2 0.1L56.9 -2.3M8.8 8.8L3.7 30.8M7.8 13.2L13.6 19.0M8.9 14.3L11.8 13.7M8.9 14.3L8.2 17.2M10.1 15.5L12.7 14.9M10.1 15.5L9.5 18.1M13.6 19.0L17.6 23.0M7.8 13.2L-0.0 15.8M6.2 13.7L5.5 16.6M6.2 13.7L3.9 11.8M4.6 14.2L4.0 16.9M4.6 14.2L2.6 12.5M-0.0 15.8L-5.5 17.7M6.7 17.6L12.0 22.8M7.8 18.6L10.4 18.0M7.8 18.6L7.2 21.2M12.0 22.8L15.6 26.5M6.7 17.6L-0.3 20.0M5.3 18.0L4.7 20.7M5.3 18.0L3.2 16.4M-0.3 20.0L-5.2 21.7M5.7 22.0L10.4 26.6M10.4 26.6L13.6 29.9M5.7 22.0L-0.5 24.1M-0.5 24.1L-4.9 25.6M4.7 26.4L8.8 30.4M8.8 30.4L11.7 33.3M4.7 26.4L-0.8 28.2M-0.8 28.2L-4.6 29.6M3.7 30.8L0.1 46.2M3.0 33.8L7.0 37.9M3.0 33.8L-2.5 35.7M2.3 36.9L5.9 40.6M2.3 36.9L-2.6 38.6M1.6 40.0L4.8 43.3M1.6 40.0L-2.8 41.5M0.8 43.1L3.7 45.9M0.8 43.1L-3.0 44.4M0.1 46.2L-2.3 56.9M17.5 17.5L37.4 13.0M21.5 16.6L23.9 9.6M22.0 15.2L20.3 13.1M22.0 15.2L24.6 14.6M23.9 9.6L25.6 4.7M21.5 16.6L26.7 21.9M22.5 17.7L25.2 17.1M22.5 17.7L21.9 20.3M26.7 21.9L30.4 25.5M25.5 15.7L27.6 9.4M27.6 9.4L29.2 5.0M25.5 15.7L30.2 20.4M30.2 20.4L33.5 23.7M29.4 14.8L31.4 9.2M31.4 9.2L32.7 5.2M29.4 14.8L33.6 19.0M33.6 19.0L36.6 21.9M33.4 13.9L35.1 9.0M35.1 9.0L36.3 5.5M33.4 13.9L37.1 17.6M37.1 17.6L39.6 20.1M37.4 13.0L51.2 9.8M40.1 12.3L41.8 7.4M40.1 12.3L43.8 16.0M42.9 11.7L44.4 7.3M42.9 11.7L46.2 15.0M45.7 11.0L47.0 7.1M45.7 11.0L48.6 14.0M48.4 10.4L49.6 7.0M48.4 10.4L51.0 13.0M51.2 9.8L60.9 7.5M17.5 17.5L13.0 37.4M16.6 21.5L21.9 26.7M17.7 22.5L20.3 21.9M17.7 22.5L17.1 25.2M21.9 26.7L25.5 30.4M16.6 21.5L9.6 23.9M15.2 22.0L14.6 24.6M15.2 22.0L13.1 20.3M9.6 23.9L4.7 25.6M15.7 25.5L20.4 30.2M20.4 30.2L23.7 33.5M15.7 25.5L9.4 27.6M9.4 27.6L5.0 29.2M14.8 29.4L19.0 33.6M19.0 33.6L21.9 36.6M14.8 29.4L9.2 31.4M9.2 31.4L5.2 32.7M13.9 33.4L17.6 37.1M17.6 37.1L20.1 39.6M13.9 33.4L9.0 35.1M9.0 35.1L5.5 36.3M13.0 37.4L9.8 51.2M12.3 40.1L16.0 43.8M12.3 40.1L7.4 41.8M11.7 42.9L15.0 46.2M11.7 42.9L7.3 44.4M11.0 45.7L14.0 48.6M11.0 45.7L7.1 47.0M10.4 48.4L13.0 51.0M10.4 48.4L7.0 49.6M9.8 51.2L7.5 60.9M26.3 26.3L43.9 22.2M29.8 25.5L32.0 19.3M32.0 19.3L33.5 14.9M29.8 25.5L34.5 30.1M34.5 30.1L37.8 33.4M33.4 24.7L35.3 19.1M35.3 19.1L36.6 15.1M33.4 24.7L37.6 28.9M37.6 28.9L40.5 31.8M36.9 23.9L38.6 18.9M38.6 18.9L39.8 15.4M36.9 23.9L40.6 27.6M40.6 27.6L43.2 30.2M40.4 23.0L41.9 18.7M41.9 18.7L43.0 15.6M40.4 23.0L43.7 26.3M43.7 26.3L46.0 28.6M43.9 22.2L56.3 19.4M46.4 21.7L47.9 17.3M46.4 21.7L49.7 24.9M48.9 21.1L50.2 17.2M48.9 21.1L51.8 24.0M51.4 20.5L52.6 17.0M51.4 20.5L54.0 23.1M53.8 20.0L54.9 16.9M53.8 20.0L56.1 22.2M56.3 19.4L64.9 17.4M26.3 26.3L22.2 43.9M25.5 29.8L30.1 34.5M30.1 34.5L33.4 37.8M25.5 29.8L19.3 32.0M19.3 32.0L14.9 33.5M24.7 33.4L28.9 37.6M28.9 37.6L31.8 40.5M24.7 33.4L19.1 35.3M19.1 35.3L15.1 36.6M23.9 36.9L27.6 40.6M27.6 40.6L30.2 43.2M23.9 36.9L18.9 38.6M18.9 38.6L15.4 39.8M23.0 40.4L26.3 43.7M26.3 43.7L28.6 46.0M23.0 40.4L18.7 41.9M18.7 41.9L15.6 43.0M22.2 43.9L19.4 56.3M21.7 46.4L24.9 49.7M21.7 46.4L17.3 47.9M21.1 48.9L24.0 51.8M21.1 48.9L17.2 50.2M20.5 51.4L23.1 54.0M20.5 51.4L17.0 52.6M20.0 53.8L22.2 56.1M20.0 53.8L16.9 54.9M19.4 56.3L17.4 64.9M35.1 35.1L50.5 31.5M38.2 34.4L40.0 28.9M40.0 28.9L41.4 25.1M38.2 34.4L42.3 38.4M42.3 38.4L45.1 41.3M41.3 33.6L43.0 28.7M43.0 28.7L44.1 25.3M41.3 33.6L44.9 37.3M44.9 37.3L47.5 39.9M44.4 32.9L45.9 28.5M45.9 28.5L46.9 25.5M44.4 32.9L47.6 36.2M47.6 36.2L49.9 38.5M47.4 32.2L48.8 28.4M48.8 28.4L49.7 25.7M47.4 32.2L50.3 35.1M50.3 35.1L52.3 37.1M50.5 31.5L61.4 29.0M52.7 31.0L54.0 27.2M52.7 31.0L55.6 33.9M54.9 30.5L56.1 27.1M54.9 30.5L57.4 33.1M57.0 30.0L58.1 26.9M57.0 30.0L59.3 32.3M59.2 29.5L60.1 26.8M59.2 29.5L61.2 31.5M61.4 29.0L68.9 27.3M35.1 35.1L31.5 50.5M34.4 38.2L38.4 42.3M38.4 42.3L41.3 45.1M34.4 38.2L28.9 40.0M28.9 40.0L25.1 41.4M33.6 41.3L37.3 44.9M37.3 44.9L39.9 47.5M33.6 41.3L28.7 43.0M28.7 43.0L25.3 44.1M32.9 44.4L36.2 47.6M36.2 47.6L38.5 49.9M32.9 44.4L28.5 45.9M28.5 45.9L25.5 46.9M32.2 47.4L35.1 50.3M35.1 50.3L37.1 52.3M32.2 47.4L28.4 48.8M28.4 48.8L25.7 49.7M31.5 50.5L29.0 61.4M31.0 52.7L33.9 55.6M31.0 52.7L27.2 54.0M30.5 54.9L33.1 57.4M30.5 54.9L27.1 56.1M30.0 57.0L32.3 59.3M30.0 57.0L26.9 58.1M29.5 59.2L31.5 61.2M29.5 59.2L26.8 60.1M29.0 61.4L27.3 68.9M43.8 43.8L74.5 74.5M50.0 50.0L65.4 46.4M53.1 49.3L54.9 43.8M53.1 49.3L57.1 53.3M56.1 48.6L57.8 43.7M56.1 48.6L59.8 52.2M59.2 47.8L60.7 43.5M59.2 47.8L62.5 51.1M62.3 47.1L63.6 43.3M62.3 47.1L65.2 50.0M65.4 46.4L76.1 43.9M50.0 50.0L46.4 65.4M49.3 53.1L53.3 57.1M49.3 53.1L43.8 54.9M48.6 56.1L52.2 59.8M48.6 56.1L43.7 57.8M47.8 59.2L51.1 62.5M47.8 59.2L43.5 60.7M47.1 62.3L50.0 65.2M47.1 62.3L43.3 63.6M46.4 65.4L43.9 76.1M56.1 56.1L70.0 52.9M58.9 55.5L60.6 50.6M58.9 55.5L62.6 59.1M61.7 54.8L63.2 50.4M61.7 54.8L65.0 58.1M64.4 54.2L65.8 50.3M64.4 54.2L67.4 57.1M67.2 53.6L68.4 50.1M67.2 53.6L69.8 56.1M70.0 52.9L79.7 50.7M56.1 56.1L52.9 70.0M55.5 58.9L59.1 62.6M55.5 58.9L50.6 60.6M54.8 61.7L58.1 65.0M54.8 61.7L50.4 63.2M54.2 64.4L57.1 67.4M54.2 64.4L50.3 65.8M53.6 67.2L56.1 69.8M53.6 67.2L50.1 68.4M52.9 70.0L50.7 79.7M62.3 62.3L74.6 59.4M64.7 61.7L66.2 57.3M64.7 61.7L68.0 64.9M67.2 61.1L68.5 57.2M67.2 61.1L70.1 64.1M69.7 60.5L70.9 57.0M69.7 60.5L72.3 63.2M72.1 60.0L73.2 56.9M72.1 60.0L74.4 62.3M74.6 59.4L83.2 57.4M62.3 62.3L59.4 74.6M61.7 64.7L64.9 68.0M61.7 64.7L57.3 66.2M61.1 67.2L64.1 70.1M61.1 67.2L57.2 68.5M60.5 69.7L63.2 72.3M60.5 69.7L57.0 70.9M60.0 72.1L62.3 74.4M60.0 72.1L56.9 73.2M59.4 74.6L57.4 83.2M68.4 68.4L79.2 65.9M70.6 67.9L71.9 64.1M70.6 67.9L73.4 70.8M72.7 67.4L73.9 63.9M72.7 67.4L75.3 70.0M74.9 66.9L75.9 63.8M74.9 66.9L77.2 69.2M77.1 66.4L78.0 63.7M77.1 66.4L79.1 68.4M79.2 65.9L86.8 64.1M68.4 68.4L65.9 79.2M67.9 70.6L70.8 73.4M67.9 70.6L64.1 71.9M67.4 72.7L70.0 75.3M67.4 72.7L63.9 73.9M66.9 74.9L69.2 77.2M66.9 74.9L63.8 75.9M66.4 77.1L68.4 79.1M66.4 77.1L63.7 78.0M65.9 79.2L64.1 86.8M74.5 74.5L96.0 96.0M78.8 78.8L89.6 76.3M78.8 78.8L76.3 89.6M83.1 83.1L92.8 80.9M83.1 83.1L80.9 92.8M87.4 87.4L96.1 85.4M87.4 87.4L85.4 96.1M91.7 91.7L99.3 90.0M91.7 91.7L90.0 99.3M96.0 96.0L111.0 111.0";

  var FSEQ = "FROST";
  var ftyped = "";
  var frostTimer = null;

  function buildIce() {
    var wrap = doc.createElement("div");
    wrap.id = "frostIce";
    wrap.setAttribute("aria-hidden", "true");

    /* one fern, mirrored into each corner — the same crystal seen four ways */
    ["tl", "tr", "bl", "br"].forEach(function (corner) {
      var svg = doc.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("class", "fern f-" + corner);
      svg.setAttribute("viewBox", "-8 -8 124 124");
      var path = doc.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", FERN);
      svg.appendChild(path);
      wrap.appendChild(svg);
    });

    for (var i = 0; i < 7; i++) {
      var f = doc.createElement("span");
      f.className = "flake";
      f.style.left = (6 + i * 13.5) + "%";
      f.style.animationDelay = (i * 0.9) + "s";
      f.style.animationDuration = (9 + (i % 3) * 3) + "s";
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

  function setFrost(on) {
    var root = doc.documentElement;
    root.classList.toggle("is-frost", on);

    var ice = doc.getElementById("frostIce");
    var probe = doc.getElementById("frostProbe");

    if (on) {
      if (!ice) doc.body.appendChild(buildIce());
      if (!probe) { probe = buildProbe(); doc.body.appendChild(probe); }

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
        el.classList.add("is-out");
        setTimeout(function () {
          if (el && el.parentNode) el.parentNode.removeChild(el);
        }, 1100);
      });
    }
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
