(() => {
  const status = document.querySelector("[data-connection-status]");
  const writeForms = [...document.querySelectorAll('form[method="post" i]')];

  const setAvailable = (available) => {
    if (status) {
      status.hidden = available;
      status.textContent = available
        ? ""
        : "Keine Serververbindung. Schreibvorgänge bleiben gesperrt, bis der Server wieder antwortet.";
      status.classList.toggle("is-offline", !available);
    }
    writeForms.forEach((form) => {
      form.querySelectorAll('button[type="submit"]').forEach((button) => {
        button.disabled = !available;
      });
    });
  };

  const verify = async () => {
    if (!navigator.onLine) {
      setAvailable(false);
      return;
    }
    try {
      const response = await fetch("/api/v1/health", { cache: "no-store" });
      setAvailable(response.ok);
    } catch {
      setAvailable(false);
    }
  };

  window.addEventListener("offline", () => setAvailable(false));
  window.addEventListener("online", verify);
  verify();

  if ("serviceWorker" in navigator && window.isSecureContext) {
    navigator.serviceWorker.register("/service-worker.js", { scope: "/" });
  }
})();
