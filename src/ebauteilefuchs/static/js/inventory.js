(() => {
  const form = document.querySelector(".inventory-booking-form");
  if (!form) return;
  const quantity = form.querySelector("[data-quantity-input]");
  const balanceSelect = form.querySelector("[data-balance-select]");
  const preview = form.querySelector("[data-booking-preview]");
  const mode = form.dataset.inventoryMode;

  const number = (value) => Number(String(value || "0").replace(",", "."));
  const updatePreview = () => {
    if (!preview || !balanceSelect) return;
    const current = number(balanceSelect.selectedOptions[0]?.dataset.balance);
    form.querySelectorAll("[data-quick-quantity]").forEach((button) => {
      const requested = button.dataset.quickQuantity === "all"
        ? current
        : number(button.dataset.quickQuantity);
      button.disabled = current <= 0 || requested > current;
    });
    let change = quantity ? number(quantity.value) : 0;
    if (mode === "stock-out" || mode === "transfer") change *= -1;
    const adjustmentMode = form.querySelector('[name="adjustment_mode"]:checked')?.value;
    if (mode === "adjustment") {
      const target = number(form.querySelector('[name="target_quantity"]')?.value);
      const difference = number(form.querySelector('[name="difference"]')?.value);
      change = adjustmentMode === "target" ? target - current : difference;
    }
    preview.textContent = `Bisher: ${current}. Änderung: ${change >= 0 ? "+" : ""}${change}. Neuer Bestand: ${current + change}.`;
  };

  form.querySelectorAll("[data-quick-quantity]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!quantity) return;
      quantity.value = button.dataset.quickQuantity === "all"
        ? balanceSelect?.selectedOptions[0]?.dataset.balance || "0"
        : button.dataset.quickQuantity;
      quantity.focus();
      updatePreview();
    });
  });
  const toggleAdjustment = () => {
    const adjustmentMode = form.querySelector('[name="adjustment_mode"]:checked')?.value;
    const targetWrapper = form.querySelector("[data-adjustment-target]");
    const differenceWrapper = form.querySelector("[data-adjustment-difference]");
    if (!targetWrapper || !differenceWrapper) return;
    const showTarget = adjustmentMode !== "difference";
    targetWrapper.hidden = !showTarget;
    differenceWrapper.hidden = showTarget;
    targetWrapper.querySelector("input").required = showTarget;
    differenceWrapper.querySelector("input").required = !showTarget;
  };
  form.querySelectorAll("input, select").forEach((field) => field.addEventListener("input", updatePreview));
  form.querySelectorAll('[name="adjustment_mode"]').forEach((field) => field.addEventListener("change", toggleAdjustment));
  form.addEventListener("submit", () => {
    const submit = form.querySelector('[type="submit"]');
    if (submit) { submit.disabled = true; submit.textContent = "Buchung läuft …"; }
  });
  toggleAdjustment();
  updatePreview();
})();
