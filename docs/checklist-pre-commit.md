# Checklist Pré-Commit

Antes de fazer `git commit`, verificar:

## Código

- [ ] Imports funcionam (`python -c "from X import Y"`)
- [ ] Requirements.txt está completo
- [ ] Testes passam localmente
- [ ] Lint não tem erros

## Deploy

- [ ] Health check funciona (`curl /health`)
- [ ] Rotas públicas funcionam
- [ ] Rotas protegidas retornam 401 sem token

## Migrations

- [ ] Migrations funcionam (se aplicável)
- [ ] Alembic upgrade head roda sem erro

## Como Usar

```bash
# Verificar imports
cd src/backend
python -c "from gateway.main import app; print('Gateway OK')"

# Rodar testes
pytest -v

# Verificar health check (com backend rodando)
curl http://localhost:8000/health
```
