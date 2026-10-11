/* Loads the motion layer only when something it animates is about to scroll
   into view: a drawing it drafts or a banner. GSAP and ScrollTrigger are
   ~117 KB; a page whose motion targets never come near the
   screen -- or a visitor who reads the first screen and leaves -- never
   downloads them. The four URLs (content-hashed by the build) ride on this
   script's data-load attribute, in the order they must run.
   Reduced motion: nothing is loaded at all. */
(function () {
  'use strict';
  var me = document.currentScript;
  if (!me || !('IntersectionObserver' in window)) return;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var urls = (me.getAttribute('data-load') || '').split(' ').filter(Boolean);
  var targets = document.querySelectorAll(
    'svg.ga, svg.rc, svg.pm, svg.nf-dwg, .page-media img');
  if (!urls.length || !targets.length) return;

  var started = false;
  function load() {
    if (started) return;
    started = true;
    io.disconnect();
    urls.forEach(function (src) {
      var s = document.createElement('script');
      s.src = src;
      s.async = false;          /* keep execution order: gsap, plugins, motion */
      document.body.appendChild(s);
    });
  }
  var io = new IntersectionObserver(function (es) {
    for (var i = 0; i < es.length; i++) if (es[i].isIntersecting) { load(); return; }
  }, { rootMargin: '0px 0px 700px 0px' });
  Array.prototype.forEach.call(targets, function (t) { io.observe(t); });
})();
