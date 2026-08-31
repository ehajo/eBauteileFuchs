const CACHE_NAME = "ebauteilefuchs-m5-shell-v9";
const APP_SHELL = [
  "/offline",
  "/static/css/design-tokens.css",
  "/static/css/app.css",
  "/static/js/pwa.js",
  "/static/js/barcode-scanner.js",
  "/static/vendor/zxing-wasm/reader.js",
  "/static/vendor/zxing-wasm/zxing_reader.wasm",
  "/static/branding/ehajo-logo.svg",
  "/static/branding/ehajo-logo.png",
  "/static/branding/e_rand_t.png",
  "/static/branding/fuchs-maskottchen.png",
  "/static/branding/app-icon-192.svg",
  "/static/branding/app-icon-512.svg",
  "/static/manifest.webmanifest"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
    ))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/static/") || url.pathname === "/manifest.webmanifest") {
    event.respondWith(
      fetch(request).catch(() => caches.match(request, { ignoreSearch: true }))
    );
    return;
  }
  if (request.mode === "navigate") {
    event.respondWith(fetch(request).catch(() => caches.match("/offline")));
  }
});
