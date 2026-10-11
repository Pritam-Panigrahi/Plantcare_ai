const CACHE_NAME = 'naturelens-cache-v1';
const STATIC_ASSETS = [
  '/',
  '/offline',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/js/explorer.js',
  '/static/js/guide.js',
  '/static/js/missions.js',
  '/static/js/journal.js',
  '/static/images/logo.svg',
  '/static/images/hero-nature.svg',
  '/static/images/monarch-butterfly.svg',
  '/static/images/english-oak.svg',
  '/static/images/dandelion.svg',
  '/static/images/european-robin.svg',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Pass non-GET requests straight to network
  if (event.request.method !== 'GET') {
    return;
  }

  // Handle navigation requests (pages)
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match('/offline') || caches.match('/');
      })
    );
    return;
  }

  // Stale-while-revalidate for static files
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => {
        // Return cached or fallback
        return cachedResponse;
      });

      return cachedResponse || fetchPromise;
    })
  );
});
