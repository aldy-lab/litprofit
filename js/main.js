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


  /* ---------- the refrigeration cycle ----------
     Hover or focus a station and the matching box lights up in the schematic.
     aria-expanded carries the open/closed state, so the control reports what
     it does rather than only looking like it. */
  var cycle = doc.getElementById("cycle");
  if (cycle) {
    var stages = all(".stage", cycle);

    var select = function (btn) {
      stages.forEach(function (b) {
        b.setAttribute("aria-expanded", b === btn ? "true" : "false");
      });
      if (btn) cycle.setAttribute("data-active", btn.getAttribute("data-stn"));
      else cycle.removeAttribute("data-active");
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

    on(cycle, "mouseleave", function () {
      /* do not yank the panel away from someone reading it via the keyboard */
      if (!cycle.contains(doc.activeElement)) select(null);
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

  /* ---------- analytics (opt-in, cookieless) ---------- */
  if (ANALYTICS_DOMAIN) {
    var s = doc.createElement("script");
    s.defer = true;
    s.setAttribute("data-domain", ANALYTICS_DOMAIN);
    s.src = "https://plausible.io/js/script.js";
    doc.head.appendChild(s);
  }
})();
