const CACHE_NAME = 'jareyeslaw-v2';
const urlsToCache = [
  '/',
  '/jareyeslaw-site/index.html',
  '/jareyeslaw-site/css/style.css',
  '/jareyeslaw-site/js/script.js',
  '/jareyeslaw-site/images/logo.png',
  '/jareyeslaw-site/images/atty-jen-reyes.png',
  '/jareyeslaw-site/images/icon-192x192.png',
  '/jareyeslaw-site/images/icon-512x512.png',
  '/jareyeslaw-site/about.html',
  '/jareyeslaw-site/profile.html',
  '/jareyeslaw-site/appearances.html',
  '/jareyeslaw-site/lawyering.html',
  '/jareyeslaw-site/practice-areas.html',
  '/jareyeslaw-site/litigation.html',
  '/jareyeslaw-site/commercial-law.html',
  '/jareyeslaw-site/labor-employment.html',
  '/jareyeslaw-site/civil-law.html',
  '/jareyeslaw-site/specific-projects.html',
  '/jareyeslaw-site/legislative-consultancy.html',
  '/jareyeslaw-site/government-interactions.html',
  '/jareyeslaw-site/ask-atty-jen.html',
  '/jareyeslaw-site/commitment.html',
  '/jareyeslaw-site/confidentiality.html',
  '/jareyeslaw-site/transparency.html',
  '/jareyeslaw-site/approach.html',
  '/jareyeslaw-site/contact.html'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames =>
      Promise.all(
        cacheNames.filter(name => name !== CACHE_NAME).map(name => caches.delete(name))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) return response;
        return fetch(event.request).then(fetchResponse => {
          if (!fetchResponse || fetchResponse.status !== 200 || fetchResponse.type !== 'basic') {
            return fetchResponse;
          }
          const responseToCache = fetchResponse.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseToCache);
          });
          return fetchResponse;
        });
      })
      .catch(() => {
        if (event.request.destination === 'document') {
          return caches.match('/jareyeslaw-site/index.html');
        }
      })
  );
});
