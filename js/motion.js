/* ============================================================
   MOTION -- the drawings draft themselves, the headings set in
   ------------------------------------------------------------
   Two things, both in the site's own language and nothing else:

   1. Drafting. Each line drawing below the fold is drawn the way it was
      drawn on paper: outlines first, in document order, then fills, then
      the lettering. The general arrangement on the home page and the
      compressor section follow the scroll (scrub), so the drawing is
      finished by the time it sits mid-screen and runs backwards if you go
      back up. The small ones -- the port plan, the 404 -- draft once.
      Lines that already carry a dash pattern (centre lines, dimension
      lines) or their own animation keep it; they only fade in, because a
      dash used for drafting would erase the pattern that gives them their
      meaning.

   2. Banners. A page's banner photograph drifts slowly inside its frame.

   Headings are not animated: tried, and taken out as one effect too many.

   The hero is left exactly as it is -- by decision, not by omission.

   GSAP and ScrollTrigger are served from this site (js/vendor),
   like every other file it uses, so this adds no third-party request; and
   js/motion-boot.js fetches them only when a target nears the screen.
   Under prefers-reduced-motion none of it runs and every drawing is simply
   there. With scripting off the page is the same.
   ============================================================ */
(function () {
  'use strict';

  if (!window.gsap || !window.ScrollTrigger) return;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var gsap = window.gsap;
  gsap.registerPlugin(window.ScrollTrigger);

  var SHAPES = 'path,line,polyline,polygon,rect,circle,ellipse';

  /* ---------- 1. drafting ---------- */
  function draft(svg, scrub) {
    var lines = [], fills = [], late = [];
    Array.prototype.forEach.call(svg.querySelectorAll(SHAPES + ',text'), function (el) {
      if (el.closest('defs, clipPath, mask')) return;
      var cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      if (el.tagName.toLowerCase() === 'text') { late.push(el); return; }
      var stroked = cs.stroke && cs.stroke !== 'none' && parseFloat(cs.strokeWidth) > 0;
      var own = (cs.strokeDasharray && cs.strokeDasharray !== 'none') ||
                (cs.animationName && cs.animationName !== 'none');
      var filled = cs.fill && cs.fill !== 'none' && cs.fill !== 'transparent' &&
                   !/rgba\([^)]*,\s*0\)$/.test(cs.fill);
      if (stroked && !own) {
        lines.push(el);
        if (filled) fills.push(el);
      } else {
        late.push(el);
      }
    });
    if (!lines.length) return;

    /* pathLength="1" makes every outline one unit long whatever its real
       length, so one dash of 1 and an offset from 1 to 0 draws any of them. */
    lines.forEach(function (el) {
      el.setAttribute('pathLength', '1');
      el.style.strokeDasharray = '1 1';
      el.style.strokeDashoffset = '1';
    });

    var tl = gsap.timeline({
      defaults: { ease: scrub ? 'none' : 'power2.inOut' },
      scrollTrigger: scrub
        ? { trigger: svg, start: 'top 88%', end: 'center 55%', scrub: 0.6 }
        : { trigger: svg, start: 'top 82%', once: true },
      onComplete: scrub ? null : function () {
        /* drawn for good: give the outlines back their own stroke */
        lines.forEach(function (el) {
          el.removeAttribute('pathLength');
          el.style.strokeDasharray = '';
          el.style.strokeDashoffset = '';
        });
      }
    });
    tl.to(lines, { strokeDashoffset: 0, duration: 1, stagger: { amount: 1.4 } }, 0);
    if (fills.length) tl.from(fills, { fillOpacity: 0, duration: 0.6, stagger: { amount: 0.5 } }, 0.9);
    if (late.length) tl.from(late, { opacity: 0, duration: 0.5, stagger: { amount: 0.5 } }, 1.2);
  }

  [['.ga', true], ['.rc', true], ['.pm', false], ['.nf-dwg', false]].forEach(function (d) {
    Array.prototype.forEach.call(document.querySelectorAll('svg' + d[0]), function (svg) { draft(svg, d[1]); });
  });

  /* ---------- banners ----------
     A banner photograph is already cropped to 21:8 by its frame, so it can
     travel a little inside that frame without losing anything: it moves at a
     slightly slower rate than the page, and the frame itself stays put. Only
     the banners -- the work photographs elsewhere are shown uncropped, and
     moving them would mean cutting into them. */
  Array.prototype.forEach.call(document.querySelectorAll('.page-media img'), function (img) {
    gsap.fromTo(img, { yPercent: -4, scale: 1.09 }, {
      yPercent: 4, scale: 1.09, ease: 'none',
      scrollTrigger: { trigger: img.parentNode, start: 'top bottom', end: 'bottom top', scrub: true }
    });
  });

})();
