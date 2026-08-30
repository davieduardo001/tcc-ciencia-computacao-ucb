# Checklist Pré-Commit

Antes de fazer `git commit`, verificar:

## Comando Rápido

```bash
./scripts/verificar-deploy.sh
```

## Verificações Manuais

### Código
- [ ] Imports funcionam (`python -c "from X import Y"`)
- [ ] Requirements.txt está completo
- [ ] Testes passam localmente
- [ ] Lint não tem erros

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

# O script verifica:
# 1. Dependências do requirements.txt
# 2. Imports do Gateway e Auth
# 3. Health check (deve retornar 200)
# 4. Rotas públicas
# 5. Rota protegida (deve retornar 401)
```
