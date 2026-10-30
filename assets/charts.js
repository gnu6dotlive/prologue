/* Graphiques interactifs : une fiche au survol ou au toucher de chaque marque
   (attribut data-tip), et des bascules qui montrent ou cachent une série
   (attribut data-toggles du SVG, groupes data-series). Sans JavaScript, le
   graphique reste lisible tel quel, toutes séries visibles. */
(function () {
  "use strict";
  var tip;

  function build() {
    tip = document.createElement("div");
    tip.className = "chart-tip";
    tip.setAttribute("role", "status");
    tip.hidden = true;
    document.body.appendChild(tip);
  }

  function show(mark, x, y) {
    if (!tip) build();
    tip.textContent = mark.getAttribute("data-tip");
    tip.hidden = false;
    var w = tip.offsetWidth, h = tip.offsetHeight, m = 12;
    var left = Math.min(Math.max(m, x + 14), window.innerWidth - w - m);
    var top = y + 18;
    if (top + h > window.innerHeight - m) top = y - h - 14;
    tip.style.left = left + "px";
    tip.style.top = Math.max(m, top) + "px";
  }
  function hide() { if (tip) tip.hidden = true; }

  function centre(el) {
    var r = el.getBoundingClientRect();
    return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  }

  document.addEventListener("pointermove", function (e) {
    var mark = e.target.closest && e.target.closest("svg.chart [data-tip]");
    if (mark) show(mark, e.clientX, e.clientY); else hide();
  });
  document.addEventListener("pointerdown", function (e) {
    var mark = e.target.closest && e.target.closest("svg.chart [data-tip]");
    if (mark && e.pointerType !== "mouse") show(mark, e.clientX, e.clientY);
    else if (!mark) hide();
  });
  document.addEventListener("focusin", function (e) {
    var mark = e.target.closest && e.target.closest("svg.chart [data-tip]");
    if (mark) { var c = centre(mark); show(mark, c.x, c.y); } else hide();
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") hide(); });
  window.addEventListener("scroll", hide, { passive: true });

  // les bascules, au-dessus du graphique, hors de la zone qui défile sur mobile
  Array.prototype.forEach.call(document.querySelectorAll("svg.chart[data-toggles]"), function (svg) {
    var toggles;
    try { toggles = JSON.parse(svg.getAttribute("data-toggles")); } catch (err) { return; }
    var bar = document.createElement("div");
    bar.className = "chart-toggles";
    toggles.forEach(function (t) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = t.label;
      b.setAttribute("aria-pressed", t.on ? "true" : "false");
      b.addEventListener("click", function () {
        var on = b.getAttribute("aria-pressed") !== "true";
        b.setAttribute("aria-pressed", on ? "true" : "false");
        Array.prototype.forEach.call(svg.querySelectorAll('[data-series="' + t.key + '"]'), function (g) {
          g.style.display = on ? "" : "none";
        });
        hide();
      });
      bar.appendChild(b);
    });
    var host = svg.closest("figure") || svg;
    host.parentNode.insertBefore(bar, host);
  });
})();
