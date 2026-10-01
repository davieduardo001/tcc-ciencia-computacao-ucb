# Adequação de UI ao Protótipo v3 — Web, Tablet e Mobile

Mapeamento do que precisa ser corrigido/ajustado na interface real (`src/frontend`) para ficar
aderente ao protótipo de alta fidelidade "MoveCity App v3" (arquivo fornecido localmente,
export estático do Figma) e funcionar bem nos três tamanhos de tela. Este documento é o
planejamento — nenhuma das tarefas abaixo marcadas como pendentes foi implementada ainda.

## Contexto importante sobre o protótipo v3

O arquivo `MoveCity App v3.html` **não tem nenhuma media query** — é um mock de largura fixa
(simulando um celular), sem variação de layout para tablet/desktop. Ou seja: o protótipo define
a linguagem visual (cores, componentes, ícones, espaçamento) e o fluxo mobile, mas **não** define
como tablet/desktop devem se comportar — isso é uma decisão nossa, não uma cópia direta do
protótipo.

## Arquitetura atual de breakpoints

Hoje existe **um único breakpoint**, em `src/frontend/app/mapa/mapa.css`:

```css
@media (max-width: 920px) { /* ... */ }
```

- **`< 920px`**: layout "mobile" — sidebar (`.ms-sidebar`) escondida, navegação inferior
  (`.ms-bottomnav`) + botão de ação central com arco (`.ms-fab-area`) aparecem.
- **`≥ 920px`**: layout "desktop" — sidebar com todos os itens de navegação, sem bottomnav/FAB.

**Não existe uma faixa "tablet" própria.** Uma tela de tablet em retrato (ex.: iPad, 768×1024)
cai inteira no bucket "mobile" — e é exatamente aí que os problemas aparecem.

## Problema encontrado: layout mobile "esticado" em tablet

Testado em 768×1024 (preset tablet do browser pane) na tela `/mapa`:

- A barra de navegação inferior (`.ms-bottomnav`) e a busca no topo (`.ms-topbar`) foram
  desenhadas pensando em ~375–430px de largura. Em 768px elas simplesmente esticam: os 4 itens
  da navegação inferior ficam com vãos enormes entre si, e a busca vira uma barra desproporcional.
- Comparação: a tela `/login` (que não usa o `AppShell`, é full-screen com `max-width` próprio)
  continua coerente em 768px — confirma que o problema é específico do chrome compartilhado
  (`AppShell`/`mapa.css`), não um padrão geral do projeto.
- A tela `/ocorrencias` (US #23, já implementada) foi validada em 1440px (desktop) e ficou boa —
  o formulário tem `max-width` e não estica; o problema real está nos elementos de navegação do
  `AppShell`, não no conteúdo das páginas.

### Proposta de correção (pendente de validação)

Duas abordagens possíveis — **isso é uma decisão de produto, não só técnica**, por isso está em
aberto:

1. **Opção A — Capar a largura do chrome mobile.** `.ms-bottomnav`, `.ms-topbar` (dentro do
   media query de 920px) ganham um `max-width` (ex.: 480px) centralizado, em vez de ocupar
   `100%` da tela. Mudança pequena, localizada, baixo risco de quebrar o que já funciona.
2. **Opção B — Criar uma faixa tablet de verdade.** Um segundo breakpoint (ex.: 768–920px) com
   layout próprio (ex.: sidebar compacta — só ícones — em vez do bottomnav). Mais fiel a um app
   "adaptado" por tamanho de tela, mas é bem mais trabalho e mexe em mais lugares.

**Recomendação:** começar pela Opção A (menor risco, resolve o esticamento) e só evoluir pra
Opção B se o resultado não for suficiente.

## Telas do protótipo v3 vs. o que existe hoje em `homolog`

| Tela (prototype) | Rota real | Usa `AppShell`? | Status de auditoria |
|---|---|---|---|
| Login / Criar conta | `/login`, `/cadastro` | Não (layout próprio) | Verificado em tablet — OK, só sobra espaço vazio embaixo do form em telas altas (polimento, não bug) |
| Recuperar/redefinir senha | `/recuperar-senha`, `/redefinir-senha` | Não | **Não auditado** nesta rodada |
| Mapa | `/mapa` | Sim | Mobile OK; **tablet com o problema acima**; desktop OK |
| Reportar/visualizar ocorrências | `/ocorrencias` | Sim | Mobile OK (validado com screenshot); desktop OK (validado com screenshot); **tablet não auditado individualmente** (herda o problema do AppShell) |
| Tutorial / onboarding | `/tutorial` | Não (layout próprio) | **Não auditado** nesta rodada |
| Configurações / Perfil | `/configuracoes` | Não (layout próprio, cores fora do design system v3 — ver nota abaixo) | **Não auditado em tablet/desktop** |
| Alertas, Favoritos, Perfil (tela dedicada) | — | — | Ainda não implementadas (telas "Em breve") — fora de escopo até existirem |

> **Nota sobre `/configuracoes`:** essa tela usa uma paleta própria (azul `#2563eb`) que não
> corresponde aos tokens de marca v3 (`--mc-teal`, `--mc-petroleo` etc. em `globals.css`). Parece
> ter sido construída antes da identidade visual v3 ser definida e nunca atualizada. Candidata a
> re-skin quando chegarmos nela.

## Bugs encontrados e corrigidos nesta rodada (branch `fix/guia-primeiro-acesso-nao-salva`)

Não fazem parte da adequação visual, mas foram relatados junto e já têm causa raiz + correção:

1. **Guia/tutorial não salvava que já tinha sido visto.** Causa raiz: o Gateway nunca teve proxy
   para `PUT /auth/me/first-access` (só existia `GET /auth/me`) — toda chamada do front caía em
   404 antes de chegar no Auth Service, e o erro era engolido silenciosamente pelo `catch` do
   front. `first_access` nunca persistia como `false`, e o tutorial voltava a aparecer sempre.
   **Corrigido** — proxy adicionado em `gateway/routes.py`, com teste de regressão.
2. **Botão de ajuda "(?)" ao lado do nome do usuário.** Não existia. **Adicionado** na sidebar do
   `AppShell` (ao lado do nome/e-mail, antes do botão de sair), reabre o tutorial sob demanda.
   Só aparece pra quem está autenticado — dependia da correção do item 1 pra funcionar de ponta a
   ponta.
3. **Texto "Teste" residual perto do nome do usuário.** Investigado via busca em todo o
   `src/frontend` (grep por `Teste`/`teste`/`Test`) — **não encontrado** nenhum resíduo na área
   do usuário/sidebar em código de produção. As únicas ocorrências são dados de teste em arquivos
   `__tests__` (ex.: `"ana@teste.com"`), que não aparecem na UI real. **Em aberto**: precisa de um
   print de tela ou a URL exata de onde esse texto aparece pra localizar com certeza — pode já ter
   sido corrigido, estar em código não commitado, ou ser algo visual que o grep não pega.

## Plano proposto (fases)

1. **Fase 1 — Breakpoint de tablet no `AppShell`.** Aplicar a Opção A acima (cap de largura no
   chrome mobile) e revalidar `/mapa` e `/ocorrencias` em 768×1024.
2. **Fase 2 — Auditoria das telas standalone.** `/tutorial`, `/recuperar-senha`,
   `/redefinir-senha` em mobile/tablet/desktop — hoje sem nenhuma verificação nesta rodada.
3. **Fase 3 — Re-skin de `/configuracoes`** pra usar os tokens de marca v3, já que está
   claramente fora do design system atual.
4. **Fase 4 — Resolver o mistério do texto "Teste"** assim que tivermos um print/URL de onde ele
   aparece.
5. **Fase 5 — Regressão fotográfica.** Screenshot em 375/768/1440px de cada tela alterada,
   antes/depois, mais rodar as suítes de teste (`pytest` no backend, `jest` no frontend) a cada
   fase — não faz sentido fechar uma fase com teste quebrado.

## Perguntas em aberto para quem revisar este documento

- Opção A ou B pro breakpoint de tablet (seção acima)?
- Prioridade das fases — seguimos a ordem sugerida ou algo é mais urgente?
- Print ou URL de onde aparece o texto "Teste", pra fechar o item 3 dos bugs.
