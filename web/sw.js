/* music3 service worker：壳缓存 + 离线可开
 * 策略：
 *   - 页面/静态资源：stale-while-revalidate（先给缓存，后台更新）
 *   - /api/stream /api/cover：network-first（音频不能拿旧缓存）
 *   - /api/* 其他：network-only（数据要新）
 */
const VERSION = 'm3-v1';
const SHELL = ['/', '/manifest.json', '/icon.svg'];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(VERSION).then((c) => c.addAll(SHELL).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== location.origin) return;

  // 音频流、封面：network-first（但要能离线重播已缓存的封面）
  if (url.pathname === '/api/stream' || url.pathname === '/api/cover') {
    e.respondWith(
      fetch(req).then((r) => {
        if (url.pathname === '/api/cover' && r.ok) {
          const cp = r.clone();
          caches.open(VERSION).then((c) => c.put(req, cp)).catch(() => {});
        }
        return r;
      }).catch(() => caches.match(req))
    );
    return;
  }

  // 其他 API：不缓存
  if (url.pathname.startsWith('/api/')) return;

  // 页面与静态资源：stale-while-revalidate
  e.respondWith(
    caches.match(req).then((hit) => {
      const net = fetch(req).then((r) => {
        if (r.ok) {
          const cp = r.clone();
          caches.open(VERSION).then((c) => c.put(req, cp)).catch(() => {});
        }
        return r;
      }).catch(() => hit);
      return hit || net;
    })
  );
});
