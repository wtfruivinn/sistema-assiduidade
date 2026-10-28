// ============================================================
// Service Worker — Sistema de Assiduidade
// Permite funcionamento offline básico (PWA)
// ============================================================

const CACHE_NAME = 'assiduidade-v1';
const URLS_PARA_CACHE = [
    '/',
    '/login/',
    '/painel/',
    '/static/css/estilo.css',
];

// Instalação: guardar os ficheiros essenciais em cache
self.addEventListener('install', (event) => {
    console.log('[Service Worker] A instalar...');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[Service Worker] A guardar ficheiros em cache');
            return cache.addAll(URLS_PARA_CACHE);
        }).catch((err) => {
            console.log('[Service Worker] Erro ao guardar em cache:', err);
        })
    );
    self.skipWaiting();
});

// Ativação: limpar caches antigas
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] A ativar...');
    event.waitUntil(
        caches.keys().then((nomes) => {
            return Promise.all(
                nomes.map((nome) => {
                    if (nome !== CACHE_NAME) {
                        console.log('[Service Worker] A apagar cache antiga:', nome);
                        return caches.delete(nome);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch: tentar rede primeiro, cache como fallback
self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;
    if (event.request.url.includes('/api/')) return;

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseClone);
                });
                return response;
            })
            .catch(() => {
                return caches.match(event.request);
            })
    );
});