# Pesquisa: Integração com dados de linhas e GPS de ônibus do DF

**Status:** Em discussão (Vitória + Davi)
**Contexto:** US #15 (Buscar Linha por Número), #16 (Rastrear Posição em Tempo Real), #17 (Visualizar Trajeto e Paradas) — as três dependem da mesma fonte de dados de linhas/GPS, por isso a decisão precisa ser tomada em conjunto.

---

## O que foi investigado

Não existe hoje uma API oficial, pública, gratuita e documentada do GDF/SEMOB para GPS em tempo real ou GTFS estático de ônibus:

- **DF no Ponto** (app oficial de rastreamento — [dfnoponto.semob.df.gov.br](https://dfnoponto.semob.df.gov.br/)) é voltado só ao usuário final, sem API pública para desenvolvedores.
- **Portal de Dados Abertos do DF** ([dados.df.gov.br](https://dados.df.gov.br)) — a SEMOB publica 8 datasets, nenhum é GPS/GTFS de frota (malha cicloviária, autos de infração STIP/STPC, dados de táxi, viagens de bicicleta compartilhada, PDA da SEMOB, informações gerenciais do PTU/DF).
- `onibus.df.gov.br` não está ativo; `dados.semob.df.gov.br` faz redirect 302 pro site institucional do DF no Ponto.
- Achamos referência a endpoints não documentados (`dados.semob.df.gov.br/posicao`, `/parada`, `/espaciais`, de um sistema chamado "Geomobi") num repositório comunitário do GitHub — o repositório está fora do ar (404) no momento da checagem. **Não recomendado como base**: engenharia reversa não documentada, sem SLA, pode sumir a qualquer momento.

## Como Google Maps e Moovit resolvem isso (sem feed oficial do GDF)

1. **Google Maps** — provavelmente recebe o GTFS estático da SEMOB por acordo bilateral direto (Transit Partner Program do Google), que nunca aparece em portal de dados abertos porque não é público. Isso explicaria ter rota/horário estimado no Google Maps sem bolinha de ônibus em tempo real.
2. **Moovit** — historicamente resolve a ausência de GTFS mapeando trajetos manualmente ("Moovit Community": voluntários andam no ônibus com GPS) e usa a **localização dos próprios usuários do app que estão dentro do veículo** para estimar posição ao vivo — não é telemetria do veículo, é crowdsourcing de usuário. Só funciona com volume de usuários ativos.

Conclusão: mesmo os grandes players não têm GPS ao vivo "de graça" pra DF — dependem de acordo direto com a agência ou de escala de usuários, nenhum dos dois algo que o Movecity tem hoje.

## Proposta em discussão

Ideia trazida pela Vitória, em alinhamento com o Davi:

- Usar a **API de rotas/transit do Google Maps** (já em uso/disponível) como base **estática**: nomes de linha, paradas e trajeto — consultada uma vez e **cacheada no nosso banco** (schema `mobilidade`), não a cada requisição do usuário.
- Para posição em tempo real (#16): usar a **localização real de usuários do Movecity que confirmarem estar embarcados numa linha específica** (mesmo modelo de bootstrap do Moovit), em vez de tentar simular ou depender de feed externo.
- Vantagem: evita ficar consumindo a API do Google constantemente em tempo de execução (custo/quota), já que ela não teria posição ao vivo pra oferecer mesmo se chamada em loop — a resposta seria sempre a mesma tabela estática.
- Isso também casa bem com o **Cenário 3 da própria US #16** ("Nenhum veículo em operação → Exibe aviso"): com poucos usuários no piloto, esse vai ser o estado mais comum, e já está previsto nos critérios de aceite — não é uma lacuna, é o comportamento esperado no MVP.

## Pontos de atenção antes de bater o martelo

- **Termos de uso do Google Maps Platform**: verificar se o ToS permite cachear/armazenar dados de linha e parada no nosso banco por tempo indeterminado, ou se há restrição de cache (comum em APIs de mapas).
- **Custo por chamada**: mapear quantas chamadas o MVP realmente faria (idealmente 1x por linha, refresh esporádico — não por usuário/sessão).
- **LGPD / consentimento**: compartilhar localização em tempo real do usuário exige opt-in explícito e claro — já é um requisito não-funcional documentado em [documento_visao.md](documento_visao.md) ("Proteção rigorosa de dados de geolocalização"). Precisa de UX de confirmação ("estou embarcado na linha X") e, idealmente, anonimização do ponto compartilhado (não expor identidade do usuário atrelada à posição).
- **Cold start**: no piloto, esperar ter poucos ou nenhum usuário reportando posição na maior parte do tempo — vale considerar dados simulados só para fins de demonstração/apresentação do TCC, deixando claro que é simulação.

## Decisão

_Pendente — em conversa entre Vitória e Davi._
