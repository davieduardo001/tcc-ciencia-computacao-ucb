# Secrets por Plataforma — Movecity

Guia de quais secrets configurar em cada plataforma. **NUNCA** commit valores reais no repositório.

**Status:** Todos os secrets já foram configurados em 15/08/2026.

---

## Neon (Banco de Dados PostgreSQL)

**Projeto:** `movecity`
**ID:** `sweet-bonus-49355838`
**Região:** `aws-sa-east-1` (São Paulo)

| Campo | Valor |
|-------|-------|
| Host | `ep-shiny-term-acc2b3yz.sa-east-1.aws.neon.tech` |
| Database | `movecity` |
| User | `movecity_owner` |
| Port | `5432` |

**DATABASE_URL (para usar no Fly.io):**
```
postgresql://movecity_owner:SENHA_AQUI@ep-shiny-term-acc2b3yz.sa-east-1.aws.neon.tech/movecity?sslmode=require
```

**Como pegar a senha:**
1. Acesse https://console.neon.tech
2. Selecione o projeto `movecity`
3. Vá em **Connection Details**
4. Copie a **Connection string** completa

---

## Fly.io (Backend — FastAPI)

**App:** `movecity-backend`
**Região:** `gru` (São Paulo)

| Secret | Status | Descrição |
|--------|--------|-----------|
| `DATABASE_URL` | ✅ Configurado | String de conexão do Neon |
| `JWT_SECRET` | ✅ Configurado | Chave para assinar tokens JWT |
| `JWT_ALGORITHM` | ✅ Configurado | Fixo: `HS256` |
| `JWT_EXPIRATION_MINUTES` | ✅ Configurado | Fixo: `60` |
| `ENVIRONMENT` | ✅ Configurado | Fixo: `production` |

**URL do backend:** `https://movecity-backend.fly.dev`

**Comandos úteis:**
```bash
# Listar secrets
fly secrets list --app movecity-backend

# Atualizar secret
fly secrets set JWT_SECRET="novo-valor" --app movecity-backend

# Deploy (aplica secrets staged)
fly secrets deploy --app movecity-backend
```

---

## Vercel (Frontend — Next.js)

**Projeto:** `movecity-frontend`
**Repo:** `davieduardo001/tcc-ciencia-computacao-ucb`

| Secret | Status | Descrição |
|--------|--------|-----------|
| `NEXT_PUBLIC_API_URL` | ✅ Configurado | URL do backend Fly.io |
| `NEXT_PUBLIC_MAP_TILES` | ✅ Configurado | URL dos tiles OpenStreetMap |
| `NEXT_PUBLIC_APP_NAME` | ✅ Configurado | Nome do app |

**Comandos úteis:**
```bash
# Listar env vars
vercel env ls

# Adicionar nova env var
vercel env add NOME_VARIAVEL production
```

---

## Regras de Segurança

| Regra | Detalhe |
|-------|---------|
| **NUNCA** commitar secrets | Arquivos `.env` estão no `.gitignore` |
| **NUNCA** escrever na issue | Secrets vão direto para a plataforma |
| **NUNCA** logar secrets | Não usar `print()` ou `console.log` com valores sensíveis |
| **USAR** `.env.example` | Apenas com nomes das chaves, sem valores |
| **GERAR** JWT_SECRET | Usar `openssl rand -base64 32` (mín. 32 caracteres) |

---

## Checklist de Configuração

- [x] Conta criada no Neon
- [x] Projeto criado no Neon (`movecity`)
- [x] `DATABASE_URL` copiado do Neon
- [x] Conta criada no Fly.io
- [x] `fly auth login` executado
- [x] Secrets adicionados no Fly.io (5 secrets)
- [x] Conta criada no Vercel
- [x] Repo conectado no Vercel
- [x] Secrets adicionados no Vercel (3 secrets)
- [ ] Deploy automático funcionando no Vercel (pendente do primeiro push)
- [ ] Backend deployado no Fly.io (pendente do primeiro push)
