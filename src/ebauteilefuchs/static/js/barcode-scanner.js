(() => {
  const startButtons = document.querySelectorAll("[data-barcode-scan-start]");
  const dialog = document.querySelector("[data-barcode-scanner]");
  const video = dialog?.querySelector("[data-barcode-video]");
  const status = dialog?.querySelector("[data-barcode-status]");
  const closeButton = dialog?.querySelector("[data-barcode-scan-close]");
  const photoButton = dialog?.querySelector("[data-barcode-photo-trigger]");
  const photoInput = dialog?.querySelector("[data-barcode-photo]");
  const choices = dialog?.querySelector("[data-barcode-choices]");
  if (!startButtons.length || !dialog || !video || !status || !photoButton || !photoInput || !choices) return;

  const PHOTO_FORMATS = [
    "DataMatrix",
    "Code128",
    "Code39",
    "EAN13",
    "EAN8",
    "ITF",
    "UPCA",
    "UPCE",
    "QRCode",
    "PDF417",
  ];
  const LIVE_FORMATS = [
    "qr_code",
    "data_matrix",
    "code_128",
    "code_39",
    "ean_13",
    "ean_8",
    "itf",
    "upc_a",
    "upc_e",
  ];
  const WASM_URL = "/static/vendor/zxing-wasm/zxing_reader.wasm?v=3.1.3";

  let stream = null;
  let scanning = false;
  let activeButton = null;
  let activeInput = null;
  let scanSession = 0;

  const stop = () => {
    scanSession += 1;
    scanning = false;
    stream?.getTracks().forEach((track) => track.stop());
    stream = null;
    video.srcObject = null;
    video.hidden = true;
  };

  const clearChoices = () => {
    choices.replaceChildren();
    choices.hidden = true;
  };

  const close = () => {
    stop();
    photoInput.value = "";
    clearChoices();
    dialog.close();
    activeButton?.focus();
  };

  const packagingSegments = (values) => values.flatMap((value) => String(value || "")
    .replace(/<(?:GS|RS|EOT)>/gi, "\u001d")
    .split(/[\u0004\u001c-\u001f]+/)
    .map((segment) => segment.trim().replace(/^\]d2/i, "").replace(/^\[\)>/, "").trim())
    .filter((segment) => segment && segment !== "05" && segment !== "06"));

  const parseWurthValues = (values) => {
    const fields = packagingSegments(values);
    const products = [];
    const lots = [];
    const quantities = [];
    fields.forEach((field) => {
      if (/^1P.+/i.test(field)) products.push(field.slice(2).trim());
      else if (/^1T.+/i.test(field)) lots.push(field.slice(2).trim());
      else if (/^Q\s*[+-]?\d+(?:[.,]\d+)?$/i.test(field)) quantities.push(field.slice(1).trim());
    });
    return {
      products: [...new Set(products.filter(Boolean))],
      lots: [...new Set(lots.filter(Boolean))],
      quantities: [...new Set(quantities.filter(Boolean))],
    };
  };

  const useValue = (value) => {
    const cleaned = String(value || "").trim();
    if (!cleaned || !activeInput || !activeButton) return;
    status.textContent = `Erkannt: ${cleaned}`;
    activeInput.value = cleaned;
    activeInput.blur();
    stop();
    dialog.close();
    const select = document.getElementById(activeButton.dataset.selectTarget);
    if (select && activeButton.dataset.selectValue) {
      select.value = activeButton.dataset.selectValue;
    }
    if (activeButton.dataset.scanUrl) {
      window.location.assign(`${activeButton.dataset.scanUrl}${encodeURIComponent(cleaned)}`);
    } else if (activeButton.hasAttribute("data-submit-on-scan")) {
      activeInput.form?.requestSubmit();
    } else {
      activeInput.focus();
    }
  };

  const offerValues = (values) => {
    const uniqueValues = [...new Set(values.map((value) => String(value || "").trim()).filter(Boolean))];
    const wurth = parseWurthValues(uniqueValues);
    const hasWurthMetadata = wurth.lots.length || wurth.quantities.length;
    if (wurth.products.length === 1 && !hasWurthMetadata && uniqueValues.length === 1) {
      useValue(wurth.products[0]);
      return;
    }
    if (wurth.products.length) {
      const details = [
        wurth.lots.length ? `Lot: ${wurth.lots.join(", ")}` : "",
        wurth.quantities.length ? `Menge: ${wurth.quantities.join(", ")}` : "",
      ].filter(Boolean);
      status.textContent = `Würth-Etikett erkannt. Produktcode wählen${details.length ? ` · ${details.join(" · ")}` : ""}:`;
      clearChoices();
      wurth.products.forEach((value) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "button button--secondary button--small";
        button.textContent = `Produktcode ${value}`;
        button.addEventListener("click", () => useValue(value));
        choices.append(button);
      });
      choices.hidden = false;
      choices.querySelector("button")?.focus();
      return;
    }
    if (hasWurthMetadata) {
      status.textContent = "Lotnummer beziehungsweise Packungsmenge erkannt, aber kein Würth-Produktcode. Fotografiere den Barcode mit Kennung 1P.";
      clearChoices();
      return;
    }
    if (uniqueValues.length === 1) {
      useValue(uniqueValues[0]);
      return;
    }
    if (!uniqueValues.length) {
      status.textContent = "Kein Barcode erkannt. Fotografiere den Code möglichst gerade, nah und gut beleuchtet erneut.";
      return;
    }
    status.textContent = "Mehrere Barcodes erkannt. Wähle die passende Nummer:";
    clearChoices();
    uniqueValues.forEach((value) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "button button--secondary button--small";
      button.textContent = value;
      button.addEventListener("click", () => useValue(value));
      choices.append(button);
    });
    choices.hidden = false;
    choices.querySelector("button")?.focus();
  };

  const imageDataFromPhoto = async (file) => {
    if (!("createImageBitmap" in window)) return file;
    const bitmap = await createImageBitmap(file);
    const longestSide = Math.max(bitmap.width, bitmap.height);
    const scale = Math.min(1, 2400 / longestSide);
    const width = Math.max(1, Math.round(bitmap.width * scale));
    const height = Math.max(1, Math.round(bitmap.height * scale));
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) {
      bitmap.close();
      return file;
    }
    context.drawImage(bitmap, 0, 0, width, height);
    bitmap.close();
    return context.getImageData(0, 0, width, height);
  };

  const scanPhoto = async (file) => {
    stop();
    const session = ++scanSession;
    clearChoices();
    status.textContent = "Foto wird ausschließlich auf diesem Gerät ausgewertet …";
    try {
      if (!("ZXingWASM" in window)) throw new Error("Decoder not loaded");
      window.ZXingWASM.prepareZXingModule({
        overrides: {
          locateFile: (path, prefix) => (path.endsWith(".wasm") ? WASM_URL : `${prefix}${path}`),
        },
      });
      const input = await imageDataFromPhoto(file);
      const results = await window.ZXingWASM.readBarcodes(input, {
        formats: PHOTO_FORMATS,
        tryHarder: true,
        maxNumberOfSymbols: 8,
      });
      if (session !== scanSession || !dialog.open) return;
      offerValues(results.map((result) => result.text));
    } catch (_error) {
      if (session === scanSession && dialog.open) {
        status.textContent = "Das Foto konnte nicht ausgewertet werden. Verwende ein scharfes JPEG- oder PNG-Foto oder gib die Nummer ein.";
      }
    } finally {
      photoInput.value = "";
    }
  };

  const scanFrame = async (detector, session) => {
    if (!scanning || session !== scanSession) return;
    try {
      const matches = await detector.detect(video);
      if (matches.length) {
        offerValues(matches.map((match) => match.rawValue));
        return;
      }
    } catch (_error) {
      status.textContent = "Das Live-Bild konnte nicht ausgewertet werden. Nutze alternativ „Foto aufnehmen“.";
    }
    window.setTimeout(() => scanFrame(detector, session), 180);
  };

  const startLiveScan = async (session) => {
    if (!window.isSecureContext) {
      status.textContent = "Tippe auf „Foto aufnehmen“. Das funktioniert im lokalen Netz auch ohne HTTPS und bleibt vollständig auf deinem Handy.";
      photoButton.focus();
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !("BarcodeDetector" in window)) {
      status.textContent = "Der Live-Scan wird von diesem Browser nicht unterstützt. Nutze „Foto aufnehmen“ oder gib die Nummer ein.";
      photoButton.focus();
      return;
    }
    try {
      const supported = typeof window.BarcodeDetector.getSupportedFormats === "function"
        ? await window.BarcodeDetector.getSupportedFormats()
        : [];
      if (session !== scanSession || !dialog.open) return;
      const formats = LIVE_FORMATS.filter((format) => supported.includes(format));
      const detector = new window.BarcodeDetector(formats.length ? { formats } : undefined);
      const nextStream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: { facingMode: { ideal: "environment" } },
      });
      if (session !== scanSession || !dialog.open) {
        nextStream.getTracks().forEach((track) => track.stop());
        return;
      }
      stream = nextStream;
      video.srcObject = stream;
      video.hidden = false;
      await video.play();
      if (session !== scanSession || !dialog.open) return;
      scanning = true;
      status.textContent = "Halte den Barcode vollständig und gut beleuchtet ins Bild oder nutze „Foto aufnehmen“.";
      scanFrame(detector, session);
    } catch (_error) {
      if (session !== scanSession || !dialog.open) return;
      stop();
      status.textContent = "Die Live-Kamera konnte nicht geöffnet werden. Nutze „Foto aufnehmen“ oder prüfe die Kamerafreigabe.";
    }
  };

  const start = (button) => {
    stop();
    const session = ++scanSession;
    activeButton = button;
    activeInput = document.getElementById(button.dataset.barcodeTarget);
    if (!activeInput) return;
    clearChoices();
    video.hidden = true;
    dialog.showModal();
    startLiveScan(session);
  };

  startButtons.forEach((button) => {
    button.addEventListener("click", () => start(button));
  });
  photoButton.addEventListener("click", () => photoInput.click());
  photoInput.addEventListener("change", () => {
    const file = photoInput.files?.[0];
    if (file) scanPhoto(file);
  });
  closeButton?.addEventListener("click", close);
  dialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    close();
  });
  dialog.addEventListener("close", stop);
})();
