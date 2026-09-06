/* Legacy cleaner — index.html no longer registers this SW.
 * Kept so any previously-registered worker uninstalls quietly without navigating. */
self.addEventListener("install", function () {
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    (async function () {
      try {
        var keys = await caches.keys();
        await Promise.all(keys.map(function (k) {
          return caches.delete(k);
        }));
      } catch (e) {}
      try {
        await self.registration.unregister();
      } catch (e) {}
    })()
  );
});
