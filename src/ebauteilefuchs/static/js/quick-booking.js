(() => {
  const form = document.querySelector("[data-quick-booking]");
  if (!form) return;
  const location = form.querySelector("[data-balance-select]");
  const balanceOutput = form.querySelector("[data-current-balance]");
  const unitInput = form.querySelector("[data-booking-unit]");

  const number = (value) => Number(String(value || "0").replace(",", "."));
  const update = () => {
    const option = location?.selectedOptions[0];
    const balance = number(option?.dataset.balance);
    const unit = option?.dataset.unit || "Stück";
    if (balanceOutput) balanceOutput.textContent = `${balance} ${unit}`;
    if (unitInput) unitInput.value = unit;
    form.querySelectorAll('[name="delta"]').forEach((button) => {
      const delta = button.value;
      if (delta === "all") button.disabled = balance <= 0;
      else if (delta.startsWith("-")) button.disabled = balance < Math.abs(number(delta));
    });
  };

  location?.addEventListener("change", update);
  form.addEventListener("submit", (event) => {
    const submitter = event.submitter;
    if (submitter) {
      if (submitter.name) {
        const submittedAction = document.createElement("input");
        submittedAction.type = "hidden";
        submittedAction.name = submitter.name;
        submittedAction.value = submitter.value;
        form.append(submittedAction);
      }
      submitter.disabled = true;
      submitter.textContent = "Wird gebucht …";
    }
  });
  update();
})();
