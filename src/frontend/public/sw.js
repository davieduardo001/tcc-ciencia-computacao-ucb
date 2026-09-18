/* Service worker do Movecity.
 *
 * REGRA QUE MANDA EM TUDO AQUI: dado de transporte nunca é cacheado.
 *
 * O produto existe para dizer onde o ônibus está agora. Servir uma
 * posição guardada seria reproduzir exatamente o problema que o projeto
 * denuncia no app oficial — a tela mostrando um ônibus que não existe
 * mais. Por isso este worker só toca em GET de mesma origem: o Gateway
 * mora em outro domínio, então toda chamada de API passa direto, sem
 * nem entrar no `fetch` handler. O mesmo vale para os tiles do mapa e
 * para o Google.
 *
 * O que ele faz, então, é o que dá para fazer sem mentir: guardar a
 * casca do aplicativo (HTML, JS, CSS, ícones) para o app abrir rápido e
 * não quebrar numa oscilação de rede.
 */

const VERSAO = "movecity-v1";

// Hasheados pelo Next e imutáveis: se a URL é a mesma, o conteúdo é o
// mesmo. Pode servir do cache sem perguntar à rede.
const IMUTAVEIS = ["/_next/static/", "/icons/"];

self.addEventListener("install", () => {
  // Sem pré-cache: a lista de assets do Next muda a cada build, e uma
  // lista escrita à mão envelheceria em silêncio. O cache se enche com
  // o que a pessoa realmente usa.
  //
  // Também não chamamos skipWaiting: trocar o worker no meio da sessão
  // pode servir um chunk novo para uma página velha. A versão nova
  // assume na próxima abertura.
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    (async () => {
      const nomes = await caches.keys();
      await Promise.all(
        nomes.filter((nome) => nome !== VERSAO).map((nome) => caches.delete(nome))
      );
      await self.clients.claim();
    })()
  );
});

function ehImutavel(url) {
  return IMUTAVEIS.some((prefixo) => url.pathname.startsWith(prefixo));
}

async function cachePrimeiro(requisicao) {
  const cache = await caches.open(VERSAO);
  const guardado = await cache.match(requisicao);
  if (guardado) return guardado;

  const resposta = await fetch(requisicao);
  if (resposta.ok) cache.put(requisicao, resposta.clone());
  return resposta;
}

async function redePrimeiro(requisicao) {
  const cache = await caches.open(VERSAO);
  try {
    const resposta = await fetch(requisicao);
    if (resposta.ok) cache.put(requisicao, resposta.clone());
    return resposta;
  } catch (erro) {
    const guardado = await cache.match(requisicao);
    if (guardado) return guardado;
    throw erro;
  }
}

self.addEventListener("fetch", (evento) => {
  const requisicao = evento.request;

  // Só GET: POST de login, cadastro e reporte nunca podem ser repetidos
  // de um cache.
  if (requisicao.method !== "GET") return;

  const url = new URL(requisicao.url);

  // Outra origem (Gateway, SEMOB, CARTO, Google) passa direto.
  if (url.origin !== self.location.origin) return;

  // Se algum dia a API for servida pelo próprio Next, continua fora.
  if (url.pathname.startsWith("/api/")) return;

  evento.respondWith(
    ehImutavel(url) ? cachePrimeiro(requisicao) : redePrimeiro(requisicao)
  );
});
