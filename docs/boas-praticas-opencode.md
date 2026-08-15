# Boas Práticas com o opencode — Movecity

Guia completo de como usar o opencode no projeto Movecity, incluindo workflow agentico, spec programming, e dicas práticas para a equipe.

---

## O que é o opencode?

O opencode é uma ferramenta de IA para desenvolvimento de software. Ele funciona como um assistente de código que pode:
- Ler e escrever arquivos
- Executar comandos no terminal
- Buscar na web
- Trabalhar com agentes especializados
- Usar skills (instruções reutilizáveis)

---

## Plan Mode vs Build Mode

O opencode possui dois modos principais de operação:

### Plan Mode (Planejamento)
- **Atalho:** `Shift + Tab` para alternar
- **O que faz:** Apenas leitura e análise. Nenhuma alteração é feita no código.
- **Para que serve:** Entender o código, planejar mudanças, discutir abordagens
- **Ferramentas disponíveis:** Leitura, busca, web search, web fetch
- **Ferramentas bloqueadas:** Edição, execução de comandos

### Build Mode (Construção)
- **Atalho:** `Shift + Tab` para alternar
- **O que faz:** Alterações reais no código. Executa comandos, cria arquivos, etc.
- **Para que serve:** Implementar funcionalidades, corrigir bugs, criar testes
- **Ferramentas disponíveis:** Todas (leitura, edição, bash, git, etc.)

### Quando usar cada modo

| Situação | Modo |
|----------|------|
| "Quero entender como funciona o módulo X" | **Plan** |
| "Preciso planejar como implementar a US Y" | **Plan** |
| "Vou implementar o endpoint de login" | **Build** |
| "Vou criar os testes unitários" | **Build** |
| "Preciso revisar o código de alguém" | **Plan** |
| "Vou abrir o PR e commitar" | **Build** |

### Dica: Comece sempre em Plan

> Antes de implementar qualquer coisa, comece em **Plan Mode** para:
> 1. Ler a issue da US
> 2. Entender o diagrama de sequência
> 3. Planejar a abordagem
> 4. Só depois, mude para **Build Mode** para implementar

---

## Workflow Agentico

O workflow agentico é o ciclo de trabalho com agentes de IA. No Movecity, seguimos este ciclo:

```
┌─────────────┐
│  1. PLANEJAR │  ← Plan Mode: ler US, diagrama, entender o contexto
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  2. EXECUTAR │  ← Build Mode: implementar código, criar testes
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  3. VALIDAR  │  ← Rodar testes, lint, verificar se funciona
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  4. ITERAR   │  ← Se algo deu errado, volte para Planejar
└─────────────┘
```

### Passo a passo detalhado

#### 1. Planejar
- Mude para **Plan Mode** (`Shift + Tab`)
- Carregue a skill relevante: `desenvolver-us-backend` ou `desenvolver-us-frontend`
- Leia a issue da US no GitHub
- Leia o diagrama de sequência em `docs/diagramas/sequencia/`
- Entenda: quem são os atores, quais services participam, quais models são usados
- Defina a abordagem: o que vai criar, onde vai criar, como vai testar

#### 2. Executar
- Mude para **Build Mode** (`Shift + Tab`)
- Crie a branch: `feat/issue-[numero]-[nome]`
- Implemente o código seguindo o diagrama
- Crie os testes unitários
- Commit com Conventional Commits

#### 3. Validar
- Rodar testes: `pytest -v` (backend) ou `npm test` (frontend)
- Verificar se não há erros de lint
- Testar manualmente se possível

#### 4. Iterar
- Se tudo passou: abra o PR e comente na issue
- Se algo falhou: volte para Planejar e corrija

---

## Spec Programming

Spec Programming é a prática de escrever uma especificação (spec) antes de escrever código. No Movecity, isso é feito através das User Stories e diagramas de sequência.

### Por que Spec Programming?

1. **Claridade:** Todo mundo entende o que precisa ser feito antes de começar
2. **Redução de retrabalho:** Menos mudanças durante a implementação
3. **Qualidade:** O código segue um padrão definido
4. **Revisão:** O reviewer pode comparar o código com a spec

### Como aplicar no Movecity

#### Antes de codar
1. **Leia a US completa** — critérios de aceite, descrição, dependências
2. **Estude o diagrama de sequência** — ele é a spec técnica
3. **Identifique os participantes** — Gateway, Services, Models
4. **Planeje a estrutura** — onde criar os arquivos, quais functions criar

#### Enquanto codar
1. **Siga o diagrama fielmente** — cada seta é uma chamada
2. **Trate os cenários alternativos** — os blocos `alt`/`else`
3. **Mantenha a coesão** — cada service tem uma responsabilidade

#### Depois de codar
1. **Compare com a spec** — o código faz tudo que o diagrama pede?
2. **Teste os cenários** — principal e alternativos
3. **Documente decisões** — se algo divergiu da spec, documente por quê

---

## Agentes Disponíveis

| Agente | Modo | Para que usar |
|--------|------|---------------|
| `build` | primary | Desenvolvimento padrão (usa este por padrão) |
| `plan` | primary | Planejamento e análise sem alterações |
| `backend` | subagent | FastAPI, modelos, endpoints, testes pytest |
| `frontend` | subagent | Next.js, React, componentes, telas |
| `reviewer` | subagent | Review de código (read-only, nunca faz merge) |
| `tester` | subagent | Criar e rodar testes unitários |

### Como usar agentes

#### Diretamente
Mude para o agente desejado usando `Shift + Tab` (entre `build` e `plan`).

#### Via menção
Em qualquer mensagem, mencione o agente:
```
@backend Crie o endpoint de login seguindo o diagrama UC10
@reviewer Revise o PR #42
@tester Crie testes para o service de autenticação
```

#### Via task
O agente `build` pode delegar tarefas para subagentes:
```
Use a skill desenvolver-us-backend para implementar a US #15
```

---

## Skills Disponíveis

| Skill | Quando carregar |
|-------|-----------------|
| `desenvolver-us-backend` | Vai criar endpoint FastAPI, model, ou service |
| `desenvolver-us-frontend` | Vai criar tela, componente, ou integração React |
| `criar-testes` | Vai criar testes unitários pytest ou Jest |
| `review-pr` | Vai revisar um Pull Request |
| `criar-diagrama` | Vai criar ou validar diagrama PlantUML |

### Como carregar uma skill

O opencode lista as skills disponíveis. Quando você iniciar uma tarefa, ele pode sugerir a skill correta. Você também pode pedir explicitamente:

```
Carregue a skill desenvolver-us-backend
```

ou

```
Use a skill review-pr para revisar este PR
```

---

## Boas Práticas

### Commits
- Sempre usar Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- Uma intenção por commit
- Max 72 caracteres na primeira linha
- **NUNCA** incluir `Co-Authored-By` ou referência a IA

### Branches
- `feat/issue-[numero]-[nome]` a partir de `homolog`
- `fix/issue-[numero]-[nome]` a partir de `homolog`
- `docs/[nome]` ou `chore/[nome]` a partir de `main`

### PRs
- Descrição completa com o que foi feito
- Checklist preenchido
- **Requer aprovação de 1 reviewer** antes do merge
- Comentar na issue com link do PR

### Reviews
- Usar o agente `reviewer` ou a skill `review-pr`
- Comentar positivos e negativos
- Aprovar ou solicitar alterações
- **NUNCA fazer merge** — isso é responsabilidade do dev após aprovação

### Testes
- Cada serviço deve ter pelo menos 1 teste passando
- Testar cenário principal e alternativos
- Rodar testes antes de abrir o PR

---

## Atalhos Úteis

| Atalho | Ação |
|--------|------|
| `Shift + Tab` | Alternar entre Plan e Build mode |
| `@agente` | Mencionar um agente para delegar tarefa |
| `/skill` | Listar e carregar skills |

---

## Referências

- Documentação do opencode: https://opencode.ai/docs/
- Configuração: `opencode.json`
- Skills: `.opencode/skills/`
- Agentes: `.opencode/agents/`
- Workflow: `AGENT.md`
- Gitflow: `docs/guia-contribuicao.md`
