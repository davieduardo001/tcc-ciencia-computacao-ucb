# Plano de Testes — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/plano-de-testes.md>

Plano de QA para validar, a cada sprint, as User Stories entregues. Os casos estão em [`casos-de-teste.md`](casos-de-teste.md) e a rastreabilidade em [`matriz-rastreabilidade.md`](matriz-rastreabilidade.md).

## 1. Objetivo e escopo

**Objetivo:** confirmar, com passos repetíveis, que cada cenário BDD das USs entregues se comporta como descrito, e saber o que ainda não foi validado.

**Dentro do escopo:** as USs entregues em `homolog` e `main` (autenticação, mapa e rastreamento, ETA, rotas, colaboração, alertas, viagem), mais as correções do card #179, o bug #188 e as correções da execução de 27 e 28/10 (#211 a #232, #237). Estado da execução em 28/10/2026: ver o [quadro geral](execucao-casos-p1.md#quadro-geral-dos-49-casos-atualizado-em-2810).

**Fora do escopo:** testes de carga; validação com ônibus reais em campo (planejada pela equipe, ver a seção 6); as USs #28, #115, #118, #199 e #207, que não têm código entregue (as duas últimas e a #28 estão abertas na Sprint 4; #115 e #118 são trabalho futuro). As USs #21 e #26 foram entregues depois da escrita dos casos e ainda não têm caso manual dedicado (ver a [matriz](matriz-rastreabilidade.md), nota 3).

## 2. Níveis de teste

| Nível | O que valida | Onde está | Quem roda |
|---|---|---|---|
| Unitário e de componente | Regras de negócio e telas isoladas | pytest (`src/backend/*/tests`), Jest (`src/frontend/**/__tests__`) | CI em todo PR |
| Integração | Serviços com o banco real, migrations, contêineres dos 4 serviços | job `test-backend` e `verificar-servicos` do CI | CI em todo PR |
| Aceitação manual (este plano) | Os cenários BDD de cada US, no aplicativo publicado | `casos-de-teste.md`; registro em `execucao-casos-p1.md` | QA da equipe; a primeira execução dos 49 casos foi em 27 e 28/10/2026 |
| Em campo | Precisão do ETA e do embarque com ônibus reais | não automatizado | equipe, em Taguatinga e Ceilândia |

## 3. Ambientes e pré-requisitos

### 3.1 Ambientes reais hoje

| Item | Situação | Fonte |
|---|---|---|
| Frontend | O workflow `deploy-vercel.yml` publica a branch `homolog` na **produção** da Vercel ("homolog É o ambiente de produção visível"). Os casos de 27 e 28/10 foram executados em `https://movecity-frontend.vercel.app`. | `.github/workflows/deploy-vercel.yml`, `execucao-casos-p1.md` |
| Backend | Quatro apps no Fly.io, atrás do Gateway `https://movecity-gateway.fly.dev`. O workflow `deploy-fly.yml` dispara em push para `homolog` **e** para `main`, nos mesmos apps e com um único `DATABASE_URL`. | `.github/workflows/deploy-fly.yml`, `docs/secrets-por-plataforma.md` |
| Banco | PostgreSQL no Neon, compartilhado | `docs/secrets-por-plataforma.md` |
| Local | Backend em `http://localhost:8000`, frontend com `NEXT_PUBLIC_API_URL` apontando para ele | `docs/setup-local.md` |

> **Consequência para o QA:** não existe ambiente de homologação separado do de produção (a execução de 27/10 registra que é por decisão de custo). Os 49 casos foram executados **em produção**, e o merge em `homolog` já publica o código no ar. Casos que criam dados (cadastro, reporte, viagem) gravam no banco que o público usa. Use contas e linhas de teste identificáveis e desfaça o que criar: a execução deixou a conta de teste `qa.movecity.1793098062@example.com` no banco compartilhado, que deve ser removida. A issue #42 aparece fechada desde 14/10, mas os workflows não mudaram.

### 3.2 Pré-requisitos

- **Usuário de teste:** não há conta de teste registrada nos docs. Cadastre uma (caso CT-AUT-01) com um e-mail seu e termos aceitos; nunca use dados pessoais reais de terceiros.
- **Navegador:** Chrome atual, com o DevTools; testar também em largura de celular (≈ 375 px) e em modo escuro/claro quando o caso pedir.
- **Localização:** o app só funciona completo com geolocalização. Para testar **de longe do ônibus**, simule a posição no Chrome: DevTools → três pontos → *More tools* → *Sensors* → *Location* → *Other…* e informe latitude e longitude. O embarque exige um ônibus da linha a até 100 m da posição informada (valor padrão do código, configurável por `RAIO_EMBARQUE_M`) ou, na regra de embarque com o ônibus chegando, estar a até 400 m de uma parada da linha com o ônibus a até 2 min dela.
- **Raio de embarque em produção: 100 km, por decisão do grupo.** O secret `RAIO_EMBARQUE_M` do app `movecity-mobilidade` está em `100000` (lido em 27/10), e o grupo decidiu mantê-lo até a defesa para demonstrar o embarque de qualquer lugar. É um **limite conhecido, só para a demonstração**, a reverter para `100` depois (`flyctl secrets set RAIO_EMBARQUE_M=100 -a movecity-mobilidade`). Enquanto isso, o embarque pelo popup é aceito longe do ônibus: o CT-VIA-01 fica **reprovado por configuração** e o CT-VIA-07 **não verificável**, pois a regra de 100 m (e a do ônibus chegando) fica mascarada. Para validar essas regras, volte o secret a `100` antes.
- **E-mail:** o sistema envia e-mail **somente na recuperação de senha** (SMTP, issue #237, PR #238), validada na produção em 28/10. Não há e-mail de confirmação de conta nem outro envio; o CT-AUT-05 depende de uma caixa de entrada real do testador.
- **Feed de GPS real (SEMOB):** os ônibus e posições vêm do feed oficial e mudam a todo instante; o cache do backend é de 20 s. Antes de rodar casos de rastreamento, abra a linha no mapa e anote o prefixo e a posição do ônibus que vai usar. Linhas sem ônibus em operação (madrugada) impedem os casos que dependem de veículo; registre o caso como **Bloqueado** e não como **Reprovado**.
- **Linhas sugeridas:** use uma linha com operação frequente na região (por exemplo, a `0.110`, usada nos testes da equipe). Confirme a disponibilidade no momento do teste.

## 4. Critérios

### 4.1 Entrada (pode começar a testar)
- PR mergeado em `homolog` e deploys de backend e frontend concluídos com sucesso (`gh run list --branch homolog`). Como `homolog` publica na produção, a validação da sprint já acontece no ambiente que o público usa.
- CI verde no PR e suítes automatizadas passando (ver o [relatório unitário](relatorio-testes-unitarios.md)).
- Casos da US existentes e revisados nesta pasta.

### 4.2 Saída (a US pode ser dada como validada em homologação)
- 100% dos casos de severidade **Crítica** e **Alta** da US **Aprovados**. Na execução de 27 e 28/10 houve uma exceção registrada: o CT-VIA-01 (Alta) ficou reprovado por configuração, não por código, com decisão do grupo de manter o raio de 100 km até a defesa.
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

`Não executado` · `Aprovado` · `Aprovado em parte` (ou com ressalva; a célula diz o que não foi visto) · `Reprovado` (ou `Reprovado por configuração`, quando a causa não é código) · `Bloqueado` (ambiente ou dado impede) · `Não verificável hoje` (não há como observar o comportamento no estado atual do sistema) · `Não aplicável`.

## 5. Regressão mínima

Rode antes de toda promoção `homolog` → `main` (casos P1 dos pacotes abaixo). Como `homolog` já está na produção, a mesma regressão serve para conferir cada merge em `homolog`. Resultado da primeira execução (27 e 28/10/2026): ver o [quadro geral](execucao-casos-p1.md#quadro-geral-dos-49-casos-atualizado-em-2810).

| Pacote | Casos |
|---|---|
| Acesso | CT-AUT-01, CT-AUT-02, CT-AUT-03, CT-AUT-06 |
| Mapa e linha | CT-MAP-01, CT-MAP-02, CT-MAP-04, CT-MAP-05 |
| Parada e tempo | CT-PAR-01, CT-PAR-04, CT-ETA-01, CT-ETA-02 |
| Rota | CT-ROT-01, CT-ROT-02 |
| Viagem | CT-VIA-01, CT-VIA-02, CT-VIA-03 |
| Segurança | CT-SEG-01 |

Observações para a próxima regressão:
- O CT-VIA-01 só valida a regra de 100 m com `RAIO_EMBARQUE_M=100`; com o valor de demonstração (100 km) ele reprova por configuração.
- O CT-AUT-03 deve incluir a renovação real da sessão (`POST /auth/refresh` com sucesso, #212 e #222), que só foi observada em 28/10.
- O CT-SEG-01 foi confirmado em `/api/auth/me`; falta repetir com o `POST` numa rota de Colaboração ou de viagem.
- O CT-AUT-01 deve incluir o envio com `termos_aceitos: false` (defeito #211, corrigido no PR #218).

## 6. Dívida e limites conhecidos

- **Precisão do ETA e do embarque em campo:** a tolerância proposta é de 2 minutos para ETA até 10 minutos, e as regras do embarque com o ônibus chegando (400 m, 2 minutos) ainda não foram medidas. Os casos marcam o que se vê na tela, não a exatidão do tempo.
- **Aviso com a tela bloqueada (Web Push):** foi entregue (US #195, PR #196), mas a validação em aparelho real depende da issue #200 (chaves VAPID pelo CI, aberta). O CT-VIA-08, do aviso de proximidade, ficou não verificável hoje (precisa de um ônibus se aproximando da parada de descida) e entra no ensaio da defesa.
- **Alertas sem canal de entrega:** o alerta de atraso (#27) e as notificações de rotas preferidas (#22) usam o `NotificadorNulo`; o CT-NOT-02 ficou não verificável e o efeito das preferências (CT-NOT-01) não é observável. A entrega por push é a US #207, aberta.
- **Casos não executados:** CT-MAP-03 e CT-ETA-03 exigem simular a posição pelo DevTools (*Sensors*) à mão.
- **Folha de rota no celular (#217):** o PR #220 está em `homolog`, mas a conferência em celular real continua pendente.
- **Dispositivos:** iOS e Android reais não fazem parte da execução de referência.
- **Dados:** o feed do SEMOB muda; resultados esperados dependem de "uma linha em operação".

## 7. Entregáveis do QA por sprint

1. Registro de execução (hoje, [`execucao-casos-p1.md`](execucao-casos-p1.md)), com estado, data, ambiente e evidência por caso; o estado final de cada caso também fica na coluna Estado de `casos-de-teste.md`.
2. Defeitos abertos como issues (`[Bug]`), vinculados ao caso e à US.
3. Atualização dos [relatórios](README.md) com o procedimento "Como regerar".
