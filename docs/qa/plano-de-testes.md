# Plano de Testes — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/plano-de-testes.md>

Plano de QA para validar, a cada sprint, as User Stories entregues. Os casos estão em [`casos-de-teste.md`](casos-de-teste.md) e a rastreabilidade em [`matriz-rastreabilidade.md`](matriz-rastreabilidade.md).

## 1. Objetivo e escopo

**Objetivo:** confirmar, com passos repetíveis, que cada cenário BDD das USs entregues se comporta como descrito, e saber o que ainda não foi validado.

**Dentro do escopo:** as USs entregues em `homolog` e `main` (autenticação, mapa e rastreamento, ETA, rotas, colaboração, alertas, viagem), mais as correções do card #179 e o bug #188.

**Fora do escopo:** testes de carga; validação com ônibus reais em campo (planejada pela equipe, ver a seção 6); US #21, #26, #28, #115 e #118, que não têm código entregue.

## 2. Níveis de teste

| Nível | O que valida | Onde está | Quem roda |
|---|---|---|---|
| Unitário e de componente | Regras de negócio e telas isoladas | pytest (`src/backend/*/tests`), Jest (`src/frontend/**/__tests__`) | CI em todo PR |
| Integração | Serviços com o banco real, migrations, contêineres dos 4 serviços | job `test-backend` e `verificar-servicos` do CI | CI em todo PR |
| Aceitação manual (este plano) | Os cenários BDD de cada US, no aplicativo publicado | `casos-de-teste.md` | QA da equipe, por sprint |
| Em campo | Precisão do ETA e do embarque com ônibus reais | não automatizado | equipe, em Taguatinga e Ceilândia |

## 3. Ambientes e pré-requisitos

### 3.1 Ambientes reais hoje

| Item | Situação | Fonte |
|---|---|---|
| Frontend | O workflow `deploy-vercel.yml` publica a branch `homolog` na **produção** da Vercel ("homolog É o ambiente de produção visível"). A URL pública não está registrada nos docs; consulte o painel da Vercel. | `.github/workflows/deploy-vercel.yml` |
| Backend | Quatro apps no Fly.io, atrás do Gateway `https://movecity-gateway.fly.dev`. O workflow `deploy-fly.yml` dispara em push para `homolog` **e** para `main`, nos mesmos apps e com um único `DATABASE_URL`. | `.github/workflows/deploy-fly.yml`, `docs/secrets-por-plataforma.md` |
| Banco | PostgreSQL no Neon, compartilhado | `docs/secrets-por-plataforma.md` |
| Local | Backend em `http://localhost:8000`, frontend com `NEXT_PUBLIC_API_URL` apontando para ele | `docs/setup-local.md` |

> **Consequência para o QA:** não existe ambiente de homologação separado do de produção. Casos que criam dados (cadastro, reporte, viagem) gravam no banco que o público usa. Use contas e linhas de teste identificáveis e desfaça o que criar. A issue #42 aparece fechada desde 14/10, mas os workflows não mudaram; vale confirmar com a equipe.

### 3.2 Pré-requisitos

- **Usuário de teste:** não há conta de teste registrada nos docs. Cadastre uma (caso CT-AUT-01) com um e-mail seu e termos aceitos; nunca use dados pessoais reais de terceiros.
- **Navegador:** Chrome atual, com o DevTools; testar também em largura de celular (≈ 375 px) e em modo escuro/claro quando o caso pedir.
- **Localização:** o app só funciona completo com geolocalização. Para testar **de longe do ônibus**, simule a posição no Chrome: DevTools → três pontos → *More tools* → *Sensors* → *Location* → *Other…* e informe latitude e longitude. O embarque exige um ônibus da linha a até 100 m da posição informada (valor configurável por `RAIO_EMBARQUE_M`) ou, na regra de embarque com o ônibus chegando, estar a até 400 m de uma parada da linha com o ônibus a até 2 min dela.
- **Feed de GPS real (SEMOB):** os ônibus e posições vêm do feed oficial e mudam a todo instante; o cache do backend é de 20 s. Antes de rodar casos de rastreamento, abra a linha no mapa e anote o prefixo e a posição do ônibus que vai usar. Linhas sem ônibus em operação (madrugada) impedem os casos que dependem de veículo; registre o caso como **Bloqueado** e não como **Reprovado**.
- **Linhas sugeridas:** use uma linha com operação frequente na região (por exemplo, a `0.110`, usada nos testes da equipe). Confirme a disponibilidade no momento do teste.

## 4. Critérios

### 4.1 Entrada (pode começar a testar)
- PR mergeado em `homolog` e deploys de backend e frontend concluídos com sucesso (`gh run list --branch homolog`).
- CI verde no PR e suítes automatizadas passando (ver o [relatório unitário](relatorio-testes-unitarios.md)).
- Casos da US existentes e revisados nesta pasta.

### 4.2 Saída (a US pode ser dada como validada em homologação)
- 100% dos casos de severidade **Crítica** e **Alta** da US **Aprovados**.
- Nenhum defeito aberto de severidade Crítica ou Alta; Média e Baixa registrados em issue.
- Resultado comentado na issue (DoD-Sprint do `ai/workflow.md`).
- Para entrar em produção (DoD-Release): regressão mínima aprovada após a promoção para `main`.

### 4.3 Severidade e prioridade

| Severidade | Significado | Exemplo |
|---|---|---|
| Crítica | Impede o uso, expõe dado ou age como outro usuário | `X-User-Id` falso aceito (#188) |
| Alta | Cenário principal da US falha | embarque nunca confirma |
| Média | Cenário secundário falha ou há contorno | mensagem de erro errada |
| Baixa | Cosmético ou texto | rótulo, espaçamento |

| Prioridade | Quando testar |
|---|---|
| P1 | Toda sprint e toda promoção (regressão mínima) |
| P2 | Quando a US ou a área for alterada |
| P3 | Antes da defesa ou da promoção para produção |

### 4.4 Estados de um caso

`Não executado` · `Aprovado` · `Reprovado` · `Bloqueado` (ambiente ou dado impede) · `Não aplicável`.

## 5. Regressão mínima

Rode antes de toda promoção `homolog` → `main` (casos P1 dos dois pacotes abaixo):

| Pacote | Casos |
|---|---|
| Acesso | CT-AUT-01, CT-AUT-02, CT-AUT-03, CT-AUT-06 |
| Mapa e linha | CT-MAP-01, CT-MAP-02, CT-MAP-04, CT-MAP-05 |
| Parada e tempo | CT-PAR-01, CT-PAR-04, CT-ETA-01, CT-ETA-02 |
| Rota | CT-ROT-01, CT-ROT-02 |
| Viagem | CT-VIA-01, CT-VIA-02, CT-VIA-03 |
| Segurança | CT-SEG-01 |

## 6. Dívida e limites conhecidos

- **Precisão do ETA e do embarque em campo:** a tolerância proposta é de 2 minutos para ETA até 10 minutos, e as regras do embarque com o ônibus chegando (400 m, 2 minutos) ainda não foram medidas. Os casos marcam o que se vê na tela, não a exatidão do tempo.
- **Aviso com a tela bloqueada (Web Push):** não existe ainda; o aviso de proximidade só aparece com o app aberto (US #172).
- **Dispositivos:** iOS e Android reais não fazem parte da execução de referência.
- **Dados:** o feed do SEMOB muda; resultados esperados dependem de "uma linha em operação".

## 7. Entregáveis do QA por sprint

1. Planilha de execução (cópia da seção de casos, com estado e data).
2. Defeitos abertos como issues (`[Bug]`), vinculados ao caso e à US.
3. Atualização dos [relatórios](README.md) com o procedimento "Como regerar".
