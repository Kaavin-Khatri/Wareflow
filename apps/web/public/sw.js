// WareFlow PWA Service Worker — Offline Shell & Stale-While-Revalidate Caching
const CACHE_NAME = "wareflow-pwa-v1";
const STATIC_ASSETS = [
  "/offline",
  "/dashboard",
  "/admin/inventory",
  "/admin/products",
  "/admin/stock/adjust",
  "/admin/stock/transfer",
  "/icon.svg",
  "/wareflow-logo.svg",
  "/manifest.json",
];

// Install: Pre-cache static shell & offline fallback
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn("[SW] Pre-caching partial failure:", err);
      });
    }),
  );
  self.skipWaiting();
});

// Activate: Purge obsolete caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name)),
      );
    }),
  );
  self.clients.claim();
});

// Fetch Strategy
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests and cross-origin analytics
  if (request.method !== "GET") {
    return;
  }

  // 1. Navigation requests (HTML pages): Network-first with offline fallback
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          }
          return response;
        })
        .catch(async () => {
          const cachedResponse = await caches.match(request);
          if (cachedResponse) {
            return cachedResponse;
          }
          const offlinePage = await caches.match("/offline");
          return (
            offlinePage ||
            new Response("Offline", { status: 503, headers: { "Content-Type": "text/html" } })
          );
        }),
    );
    return;
  }

  // 2. Static Assets (_next/static, public svg/images, fonts): Cache-first
  if (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.endsWith(".svg") ||
    url.pathname.endsWith(".png") ||
    url.pathname.endsWith(".woff2")
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) return cachedResponse;
        return fetch(request).then((networkResponse) => {
          if (networkResponse.ok) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          }
          return networkResponse;
        });
      }),
    );
    return;
  }

  // 3. API Read Endpoints (/products, /stock, /categories): Stale-While-Revalidate
  if (
    url.pathname.includes("/products") ||
    url.pathname.includes("/stock") ||
    url.pathname.includes("/categories")
  ) {
    event.respondWith(
      caches.open(CACHE_NAME).then(async (cache) => {
        const cachedResponse = await cache.match(request);
        const fetchPromise = fetch(request)
          .then((networkResponse) => {
            if (networkResponse.ok) {
              cache.put(request, networkResponse.clone());
            }
            return networkResponse;
          })
          .catch(() => cachedResponse); // Return cached on network error

        return cachedResponse || fetchPromise;
      }),
    );
    return;
  }

  // Default: Network with cache fallback
  event.respondWith(fetch(request).catch(() => caches.match(request)));
});
