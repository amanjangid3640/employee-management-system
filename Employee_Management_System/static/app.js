document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[data-confirm]").forEach(form => {
    form.addEventListener("submit", event => {
      if (!window.confirm(form.dataset.confirm || "Are you sure?")) event.preventDefault();
    });
  });
  document.querySelectorAll(".flash").forEach(message => {
    window.setTimeout(() => {
      message.style.transition = "opacity .35s";
      message.style.opacity = "0";
      window.setTimeout(() => message.remove(), 400);
    }, 4500);
  });
});
