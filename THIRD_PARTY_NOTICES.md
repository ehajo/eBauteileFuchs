# Hinweise zu Drittkomponenten

eBauteileFuchs liefert folgende Drittkomponente lokal aus:

## zxing-wasm reader 3.1.3

- Projekt: <https://github.com/Sec-ant/zxing-wasm>
- Zweck: lokale Erkennung von Barcodes in aufgenommenen Bildern
- JavaScript-spezifischer Code: MIT License, Copyright (c) 2023 Ze-Zheng Wu
- ZXing-C++ und die WebAssembly-Lesebindung: Apache License 2.0
- Eingebundener ZXing-C++-Stand: `a17fd9dc65d6aa0dd2f660fdfca7a6a6613d938f`
- SHA-256 der ausgelieferten Datei `zxing_reader.wasm`:
  `2ebda08a93eea3efcd8399cda6b276e6a0b1de4fec60b4d8988a047de4c6d1ba`

Der vollständige MIT-Lizenztext liegt zusätzlich unter
`src/ebauteilefuchs/static/vendor/zxing-wasm/LICENSE.txt`. Die Apache License
2.0 liegt im Wurzelverzeichnis des Projekts als `LICENSE` vor.

Die Komponente wird ausschließlich lokal ausgeliefert. eBauteileFuchs lädt zur
Laufzeit weder Decoder-Code noch WebAssembly von einem CDN.
