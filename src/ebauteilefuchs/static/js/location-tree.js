(() => {
  const viewButtons = Array.from(document.querySelectorAll("[data-location-view]"));
  const viewPanels = Array.from(document.querySelectorAll("[data-location-panel]"));

  function activateView(view) {
    viewButtons.forEach((button) => {
      const active = button.dataset.locationView === view;
      button.setAttribute("aria-selected", String(active));
      button.classList.toggle("button--secondary", !active);
    });
    viewPanels.forEach((panel) => {
      panel.hidden = panel.dataset.locationPanel !== view;
    });
    try {
      localStorage.setItem("ebauteilefuchs-location-view", view);
    } catch (_error) {
      // The view remains usable when browser storage is unavailable.
    }
  }

  viewButtons.forEach((button) => {
    button.addEventListener("click", () => activateView(button.dataset.locationView));
  });

  let initialView = location.hash === "#verwalten" ? "tree" : "map";
  try {
    initialView = localStorage.getItem("ebauteilefuchs-location-view") || initialView;
  } catch (_error) {
    // Keep the default graphical view.
  }
  activateView(initialView === "tree" ? "tree" : "map");

  const map = document.querySelector(".storage-map");
  const mapQuery = document.querySelector("[data-storage-map-query]");
  const mapResult = document.querySelector("[data-storage-map-result]");
  const mapReset = document.querySelector("[data-storage-map-reset]");
  const normalize = (value) =>
    value
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLocaleLowerCase("de");

  function filterMap() {
    if (!map || !mapQuery) return;
    const nodes = Array.from(map.querySelectorAll("[data-location-search]"));
    const query = normalize(mapQuery.value);
    nodes.forEach((node) => node.classList.remove("is-map-match", "is-map-context", "is-map-dimmed"));
    if (!query) {
      if (mapResult) mapResult.textContent = "";
      return;
    }
    const matches = nodes.filter((node) => normalize(node.dataset.locationSearch).includes(query));
    matches.forEach((node) => {
      node.classList.add("is-map-match");
      let parent = node.parentElement?.closest(".storage-node");
      while (parent) {
        parent.classList.add("is-map-context");
        parent = parent.parentElement?.closest(".storage-node");
      }
    });
    nodes.forEach((node) => {
      if (!node.classList.contains("is-map-match") && !node.classList.contains("is-map-context")) {
        node.classList.add("is-map-dimmed");
      }
    });
    if (mapResult) mapResult.textContent = `${matches.length} Treffer hervorgehoben`;
  }

  mapQuery?.addEventListener("input", filterMap);
  mapReset?.addEventListener("click", () => {
    mapQuery.value = "";
    filterMap();
    mapQuery.focus();
  });

  const tree = document.querySelector(".location-tree");
  if (!tree) return;

  const checkboxes = Array.from(
    tree.querySelectorAll('input[name="location_ids"]'),
  );
  const counter = document.querySelector("[data-location-selection-count]");

  function descendantCheckboxes(button) {
    const branch = button.closest(".tree-branch");
    const childList = Array.from(branch?.children || []).find(
      (element) => element.tagName === "UL",
    );
    return childList
      ? Array.from(childList.querySelectorAll('input[name="location_ids"]'))
      : [];
  }

  function refresh() {
    const selected = checkboxes.filter((checkbox) => checkbox.checked).length;
    if (counter) {
      counter.textContent = `${selected} ausgewählt`;
    }

    tree.querySelectorAll("[data-select-descendants]").forEach((button) => {
      const descendants = descendantCheckboxes(button);
      const selectedDescendants = descendants.filter(
        (checkbox) => checkbox.checked,
      ).length;
      const allSelected =
        descendants.length > 0 && selectedDescendants === descendants.length;
      button.setAttribute("aria-pressed", String(allSelected));
      button.textContent = allSelected
        ? "Alle Unterplätze abwählen"
        : selectedDescendants > 0
          ? "Übrige Unterplätze auswählen"
          : "Alle Unterplätze auswählen";
    });
  }

  tree.addEventListener("click", (event) => {
    const button = event.target.closest("[data-select-descendants]");
    if (!button) return;
    const descendants = descendantCheckboxes(button);
    const shouldSelect = descendants.some((checkbox) => !checkbox.checked);
    descendants.forEach((checkbox) => {
      checkbox.checked = shouldSelect;
    });
    refresh();
  });

  tree.addEventListener("change", (event) => {
    if (event.target.matches('input[name="location_ids"]')) refresh();
  });

  refresh();
})();
