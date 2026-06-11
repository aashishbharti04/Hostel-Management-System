/* Progressive enhancement: theme toggle, flash dismissal, delete confirmation.
   The app is fully functional without JavaScript; this only improves UX. */
(function () {
  "use strict";

  // --- Dark / light theme toggle (persisted in localStorage) ---------------
  var root = document.documentElement;
  var toggle = document.getElementById("theme-toggle");

  function syncPressed() {
    if (toggle) {
      toggle.setAttribute(
        "aria-pressed",
        root.getAttribute("data-theme") === "dark" ? "true" : "false"
      );
    }
  }
  syncPressed();

  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem("hms-theme", next);
      } catch (e) {}
      syncPressed();
    });
  }

  // --- Dismissible flash messages ------------------------------------------
  document.querySelectorAll(".flash-close").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var flash = btn.closest(".flash");
      if (flash) flash.remove();
    });
  });

  // Auto-dismiss success flashes after a few seconds.
  document.querySelectorAll(".flash-success").forEach(function (flash) {
    setTimeout(function () {
      flash.style.transition = "opacity .4s ease";
      flash.style.opacity = "0";
      setTimeout(function () {
        flash.remove();
      }, 400);
    }, 4000);
  });

  // --- Confirm destructive actions -----------------------------------------
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.getAttribute("data-confirm"))) {
        e.preventDefault();
      }
    });
  });
})();
