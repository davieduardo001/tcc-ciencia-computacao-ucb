# Template de Card de Sprint — Movecity

Use este template ao criar cards no GitHub Projects para cada sprint.

---

## Título
`[US #XX] Nome Curto da User Story`

## Descrição

### Objetivo
> O que esta US entrega ao usuário final?

### Critérios de Aceite
- [ ] Critério 1
- [ ] Critério 2
- [ ] Critério 3

### Dependências
- US #XX (nome) — precisa estar concluída antes

### Complexidade
- [ ] Baixa (1-2 dias)
- [ ] Média (3-5 dias)
- [ ] Alta (1 semana+)

### Responsável
@usuario

---

## Durante o Desenvolvimento

### Checklist
- [ ] Branch criada (`feat/issue-[numero]-[nome]`)
- [ ] Diagrama de sequência estudado
- [ ] Código desenvolvido seguindo o diagrama
- [ ] Testes unitários criados (mín. 1 passando)
- [ ] Commits com Conventional Commits
- [ ] PR aberto para `homolog`
- [ ] Comentário na issue com link do PR

### Bloqueios
> Anotar aqui se houver algum bloqueio durante o desenvolvimento.

---

## Após o Desenvolvimento

### Review
- [ ] 1 reviewer aprovou o PR (formal — botão "Approve", não comentário)
- [ ] Testes passando no CI
- [ ] Lint passando
- [ ] Branch naming correta

### DoD-Sprint (conta como feita na sprint)
- [ ] Merge para `homolog` → deploy automático
- [ ] Critérios de aceite (BDD) validados em homolog
- [ ] Comentário na issue registrando o DoD-Sprint

### DoD-Release (conta como entregue de verdade)
- [ ] PR `homolog` → `main` aprovado e mergeado → deploy (Vercel + Fly.io)
- [ ] Validado em produção (endpoint/tela real)
- [ ] Issue fechada
- [ ] Documentação atualizada (se aplicável)

---

## Notas
> Espaço livre para anotações, links úteis, decisões tomadas.
