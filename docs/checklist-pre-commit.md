# Checklist Pré-Commit

Antes de fazer `git commit`, verificar:

## Comando Rápido

```bash
./scripts/verificar-deploy.sh
```

## Verificações Manuais

### Código
- [ ] Imports funcionam (`python -c "from X import Y"`)
- [ ] `requirements.txt` do serviço alterado está completo (o `requirements.txt` da raiz de `src/backend` é um superset e esconde faltas)
- [ ] Testes passam localmente (`pytest -v` em `src/backend`, `npm test` em `src/frontend`)
- [ ] Mensagem de commit e título do PR seguem Conventional Commits (o CI valida os dois)

### Deploy
- [ ] Health check funciona (`curl /health`)
- [ ] Rotas públicas funcionam
- [ ] Rotas protegidas retornam 401 sem token

### Migrations
- [ ] Migrations funcionam (se aplicável)
- [ ] Alembic upgrade head roda sem erro

## Como Usar o Script

```bash
# Verificar tudo de uma vez
./scripts/verificar-deploy.sh

# O script verifica (scripts/verificar-deploy.sh):
# 1. Contêiner de cada serviço (gateway, auth, mobilidade, colaboracao):
#    venv limpo só com o requirements.txt do serviço + import de <serviço>.main
# 2. Health check do Gateway (GET /health deve retornar 200)
# 3. Rotas públicas (/health e /api/hello) e rota protegida
#    (/api/auth/me sem sessão deve retornar 401)

# Versão rápida: pula a criação dos venvs (passo 1)
./scripts/verificar-deploy.sh --rapido
```

O passo 1 é o mesmo que o job `Contêiner do serviço` do CI faz; rodar antes evita descobrir uma dependência faltando no `requirements.txt` de um serviço só depois do push. Não roda a suíte de testes: `pytest -v` (em `src/backend`) e `npm test` (em `src/frontend`) continuam sendo etapa separada.
