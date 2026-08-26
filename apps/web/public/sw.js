// WareFlow PWA Service Worker — Offline Shell & Resilient Cache Strategy
const CACHE_NAME = "wareflow-pwa-v3";
const STATIC_ASSETS = ["/offline", "/icon.svg", "/wareflow-logo.svg", "/manifest.json"];

const OFFLINE_FALLBACK_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WareFlow — Offline</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #090d16; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; text-align: center; }
    .card { background: rgba(30,41,59,0.7); border: 1px solid rgba(255,255,255,0.1); padding: 2rem; border-radius: 1rem; max-width: 400px; margin: 1rem; backdrop-filter: blur(12px); }
    h1 { color: #38bdf8; font-size: 1.5rem; margin-bottom: 0.5rem; }
    p { color: #94a3b8; font-size: 0.9rem; margin-bottom: 1.5rem; }
    button { background: #8b5cf6; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; }
  </style>
</head>
<body>
  <div class="card">
    <h1>WareFlow Offline</h1>
    <p>You are currently offline. Check your network connection and retry.</p>
    <button onclick="window.location.reload()">Retry Connection</button>
  </div>
</body>
</html>`;

const createOfflineResponse = () =>
  new Response(OFFLINE_FALLBACK_HTML, {
    status: 503,
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });

// Install: Pre-cache static shell
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.allSettled(
        STATIC_ASSETS.map((asset) =>
          cache.add(asset).catch(() => {
            // Non-blocking asset pre-cache
          }),
        ),
      ),
    ),
  );
  self.skipWaiting();
});

// Activate: Purge obsolete caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) =>
        Promise.all(
          cacheNames.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name)),
        ),
      ),
  );
  self.clients.claim();
});

// Fetch Strategy
self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Skip non-GET requests
  if (request.method !== "GET") {
    return;
  }

  let url;
  try {
    url = new URL(request.url);
  } catch {
    return;
  }

  // Only handle same-origin HTTP(S) requests
  if (!url.protocol.startsWith("http") || url.origin !== self.location.origin) {
    return;
  }

  // Bypass service worker for auth endpoints, API routes, and Server-Sent Events / WebSockets
  if (
    url.pathname.startsWith("/api/") ||
    url.pathname.startsWith("/login") ||
    url.pathname.startsWith("/logout") ||
    url.pathname.includes("/_next/webpack-hmr") ||
    url.pathname.includes("/__nextjs")
  ) {
    return;
  }

  // 1. Navigation requests (HTML pages): Network-first with offline fallback
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          }
          return response;
        })
        .catch(async () => {
          const cachedResponse = await caches.match(request);
          if (cachedResponse) return cachedResponse;
          const offlinePage = await caches.match("/offline");
          if (offlinePage) return offlinePage;
          return createOfflineResponse();
        }),
    );
    return;
  }

  // 2. Static Assets (_next/static, public svg/images, fonts): Cache-first
  if (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.endsWith(".svg") ||
    url.pathname.endsWith(".png") ||
    url.pathname.endsWith(".jpg") ||
    url.pathname.endsWith(".woff2") ||
    url.pathname.endsWith(".ico")
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) return cachedResponse;
        return fetch(request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              const responseClone = networkResponse.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
            }
            return networkResponse;
          })
          .catch(() => {
            // Return empty response with 404 instead of throwing unhandled error
            return new Response(null, { status: 404, statusText: "Not Found" });
          });
      }),
    );
    return;
  }

  // Default: Network with Cache Fallback
  event.respondWith(
    fetch(request).catch(async () => {
      const cached = await caches.match(request);
      return cached || new Response(null, { status: 504, statusText: "Gateway Timeout" });
    }),
  );
});
