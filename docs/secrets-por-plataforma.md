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

**Variáveis opcionais de ajuste do embarque (serviço de mobilidade, issue #190)** — não são secrets e todas têm padrão no código; só configure se precisar mudar o comportamento:

| Variável | Padrão | O que faz |
|----------|--------|-----------|
| `RAIO_EMBARQUE_M` | `100` | Distância máxima (m) entre o usuário e o ônibus para confirmar "Peguei este ônibus". |
| `RAIO_PARADA_EMBARQUE_M` | `400` | Embarque "com o ônibus chegando": distância máxima (m) do usuário a uma parada da linha. **A validar em campo.** |
| `ETA_MAXIMO_EMBARQUE_MIN` | `2` | Embarque "com o ônibus chegando": tempo máximo (min) até o ônibus chegar à parada. **A validar em campo.** |

Valor ausente, em branco, não numérico ou menor ou igual a zero usa o padrão (os inválidos registram um aviso no log). Como o backend não separa homolog de produção (issue #42), o valor definido no Fly vale para os dois ambientes. O raio é uma checagem de bom senso, não uma barreira de segurança: a posição do usuário vem do cliente.

### Web Push (VAPID) — alerta de proximidade com a tela bloqueada (issue #195)

O aviso de "sua parada está chegando" já aparece dentro do app. Para chegar com a tela bloqueada, o serviço de **mobilidade** (app `movecity-mobilidade` no Fly) precisa de um par de chaves VAPID. **Sem as três variáveis abaixo o recurso fica desligado** e tudo continua como antes: o servidor sobe normalmente, a tela de Configurações mostra "indisponível" e o aviso segue só dentro do app.

| Variável | Secret? | O que é |
|----------|---------|---------|
| `VAPID_PRIVATE_KEY` | **Sim** | Chave privada (43 caracteres, base64url). Assina cada push. Nunca vai para o repositório, para log ou para a conversa. |
| `VAPID_PUBLIC_KEY` | Não | Chave pública correspondente (87 caracteres, base64url). O navegador a recebe pela API e a usa para se inscrever. |
| `VAPID_SUBJECT` | Não | Contato do responsável pelo serviço, que os serviços de push exigem: `mailto:alguem@exemplo.com` ou um `https://...`. |
| `WORKER_PROXIMIDADE_INTERVAL_SECONDS` | Não | **Opcional.** Intervalo, em segundos, do ciclo que verifica os alertas de proximidade (mínimo 20). Ausente, vale o intervalo geral de 5 min. Ver "Atraso do aviso" abaixo. |

As três primeiras precisam estar **todas** presentes e **combinar entre si**. Se faltar uma, o `VAPID_SUBJECT` for inválido, a privada não for uma chave válida ou a pública não corresponder à privada, o push fica desligado e o log registra o motivo (só o nome da variável, nunca o valor).

**Quem configura:** quem tem acesso ao Fly (o time, não o agente). As chaves não são geradas nem guardadas pelo código.

**1. Gerar o par de chaves** (numa máquina com o ambiente do backend instalado, para ter a biblioteca `cryptography`):

```bash
cd src/backend
python - <<'EOF'
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
k = ec.generate_private_key(ec.SECP256R1())
print("VAPID_PRIVATE_KEY=" + b64(k.private_numbers().private_value.to_bytes(32, "big")))
print("VAPID_PUBLIC_KEY=" + b64(k.public_key().public_bytes(
    serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)))
EOF
```

Guarde a privada no gerenciador de senhas do time. **Gere o par uma vez só:** trocar as chaves depois invalida todas as inscrições existentes, e cada pessoa precisa ativar de novo em Configurações.

**2. Configurar no Fly** (o `set` reinicia as máquinas do serviço; faça com o par já gerado):

```bash
fly secrets set \
  VAPID_PRIVATE_KEY="<privada>" \
  VAPID_PUBLIC_KEY="<publica>" \
  VAPID_SUBJECT="mailto:contato-do-time@exemplo.com" \
  --app movecity-mobilidade
```

**3. Validar:**
1. Logado no app, abra `GET /api/mobilidade/push/chave` (ou a tela de Configurações): deve responder `"disponivel": true` e a chave pública.
2. Em **Configurações → Avisos com a tela bloqueada**, toque em **Ativar** e aceite a permissão do navegador.
3. Pegue um ônibus com destino definido e uma antecedência grande (60 min, nas preferências) para o alerta disparar logo; bloqueie a tela e aguarde o ciclo do worker.
4. Se não chegar: veja `fly logs --app movecity-mobilidade` (procure "Web Push") e confira se a inscrição existe (tabela `inscricao_push`).

**Atenção:**
- **Backend compartilhado.** Homologação e produção usam o mesmo backend (issue #42): as variáveis e as inscrições valem para os dois ambientes.
- **O service worker só é registrado em produção** (`RegistrarServiceWorker`). Em `next dev` o push não funciona; teste no deploy.
- **iPhone:** só recebe push com o Movecity instalado na tela inicial (PWA) e iOS 16.4 ou superior. A tela de Configurações explica isso.
- **Atraso do aviso.** O worker verifica a cada 5 min por padrão. Quem escolhe avisar com 5 min de antecedência recebe, em média, 2,5 min antes. Se isso se confirmar em campo, defina `WORKER_PROXIMIDADE_INTERVAL_SECONDS=60`: o feed de posições é cacheado por 20 s, então não adianta ir abaixo disso. O padrão não foi alterado sem medição.
- **LGPD.** A tabela `inscricao_push` guarda só endpoint, chaves da inscrição e dono. A mensagem não leva coordenadas nem identificadores. A inscrição é apagada quando a pessoa desativa, sai da conta ou o serviço de push informa que ela expirou.

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
