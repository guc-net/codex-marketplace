// Strzałki klawiatury i przesunięcie palcem: poprzedni / następny odcinek.
(function () {
  function idz(rel) {
    var a = document.querySelector('a[rel="' + rel + '"]');
    if (a) location.href = a.href;
  }
  document.addEventListener("keydown", function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.key === "ArrowLeft") idz("prev");
    if (e.key === "ArrowRight") idz("next");
    if (e.key === "Escape") idz("index");
  });
  var x0 = null, y0 = null;
  document.addEventListener("touchstart", function (e) {
    x0 = e.touches[0].clientX; y0 = e.touches[0].clientY;
  }, { passive: true });
  document.addEventListener("touchend", function (e) {
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
    x0 = null;
    if (Math.abs(dx) > 60 && Math.abs(dx) > 2 * Math.abs(dy)) idz(dx < 0 ? "next" : "prev");
  }, { passive: true });
})();
