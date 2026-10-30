# Secrets por Plataforma — Movecity

Guia de quais secrets configurar em cada plataforma. **NUNCA** commit valores reais no repositório.

**Última revisão:** 28/10/2026. O quadro de secrets abaixo foi conferido contra `.github/workflows/*.yml` e `gh secret list`; os valores configurados diretamente no Fly (por exemplo `JWT_SECRET`) não são verificáveis pelo repositório, confira com `fly secrets list --app <app>`.

---

## Onde cada secret vive

| Plataforma | O que guarda |
|------------|--------------|
| **GitHub Actions** (secrets do repositório) | `DATABASE_URL` (usado pelo job `migrate` e pela ingestão do SEMOB), `FLY_DEPLOY_TOKEN_GATEWAY`, `_AUTH`, `_MOBILIDADE`, `_COLABORACAO` (um por app, escopo mínimo), `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `GOOGLE_CLIENT_ID`, `CARTO_API_KEY`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `FRONTEND_URL`, `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` |
| **Fly.io** (secrets de cada app) | Os do próprio serviço (ver tabela por app). `GOOGLE_CLIENT_ID`, os `SMTP_*`/`FRONTEND_URL` (no `movecity-auth`) e os `VAPID_*` (no `movecity-mobilidade`) são **empurrados pelo workflow `deploy-fly.yml`** a cada deploy, a partir dos secrets do GitHub |
| **Vercel** | Variáveis do projeto `movecity-frontend` (o build de produção é feito pelo workflow, que injeta `NEXT_PUBLIC_GOOGLE_CLIENT_ID` e `NEXT_PUBLIC_CARTO_API_KEY`) |

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

**Apps:** `movecity-gateway`, `movecity-auth`, `movecity-mobilidade`, `movecity-colaboracao` (4 apps independentes)
**Região:** `gru` (São Paulo)

Secrets por app (o que o código de cada serviço lê):

| Secret | Gateway | Auth | Mobilidade | Colaboracao | Descrição |
|--------|---------|------|------------|-------------|-----------|
| `DATABASE_URL` | não usa | sim | sim | sim | String de conexão do Neon |
| `JWT_SECRET` | sim | sim | não | não | Chave para assinar/validar tokens JWT |
| `JWT_ALGORITHM` | sim | sim | não | não | Fixo: `HS256` |
| `JWT_EXPIRATION_MINUTES` | sim | sim | não | não | Fixo: `60` |
| `ENVIRONMENT` | sim | sim | sim | sim | Fixo: `production` |
| `CORS_ORIGINS` | sim | lê | lê | lê | Origens permitidas, separadas por vírgula; o padrão do código é `http://localhost:3000`, então o Gateway precisa da URL do frontend |
| `GOOGLE_CLIENT_ID` | não | sim | não | não | Aplicado pelo job `deploy-auth` (login via Google, US #12) |
| `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `FRONTEND_URL` | não | sim | não | não | E-mail de recuperação de senha (issue #237). Aplicados pelo job `deploy-auth`; se faltar qualquer um dos quatro no GitHub, o job avisa, segue o deploy e o e-mail não é enviado. O envio usa `smtp.gmail.com:587` (`auth/email_service.py`) |
| `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` | não | não | sim | não | Web Push (issue #200). Aplicados pelo job `deploy-mobilidade`; se faltar qualquer um, Web Push fica desligado |

**Variáveis opcionais de ajuste do embarque (serviço de mobilidade, issue #190)** — não são secrets e todas têm padrão no código; só configure se precisar mudar o comportamento:

| Variável | Padrão | O que faz |
|----------|--------|-----------|
| `RAIO_EMBARQUE_M` | `100` | Distância máxima (m) entre o usuário e o ônibus para confirmar "Peguei este ônibus". **Em produção está em `100000` (100 km)**, por decisão do grupo de 27/10/2026 (issue #216), somente para demonstrar o embarque de qualquer lugar até a defesa; com esse valor a regra de 100 m não é exercitada. Para voltar ao padrão: `flyctl secrets set RAIO_EMBARQUE_M=100 --app movecity-mobilidade` e retestar a recusa a mais de 100 m. |
| `RAIO_PARADA_EMBARQUE_M` | `400` | Embarque "com o ônibus chegando": distância máxima (m) do usuário a uma parada da linha. **A validar em campo.** |
| `ETA_MAXIMO_EMBARQUE_MIN` | `2` | Embarque "com o ônibus chegando": tempo máximo (min) até o ônibus chegar à parada. **A validar em campo.** |

Valor ausente, em branco, não numérico ou menor ou igual a zero usa o padrão (os inválidos registram um aviso no log). Como o backend não separa homolog de produção (issue #42) e `homolog` publica direto na produção, o valor definido no Fly vale para os dois. O raio é uma checagem de bom senso, não uma barreira de segurança: a posição do usuário vem do cliente.

### Web Push (VAPID) — alerta de proximidade com a tela bloqueada (issue #195)

O aviso de "sua parada está chegando" já aparece dentro do app. Para chegar com a tela bloqueada, o serviço de **mobilidade** (app `movecity-mobilidade` no Fly) precisa de um par de chaves VAPID. **Sem as três variáveis abaixo o recurso fica desligado** e tudo continua como antes: o servidor sobe normalmente, a tela de Configurações mostra "indisponível" e o aviso segue só dentro do app.

| Variável | Secret? | O que é |
|----------|---------|---------|
| `VAPID_PRIVATE_KEY` | **Sim** | Chave privada (43 caracteres, base64url). Assina cada push. Nunca vai para o repositório, para log ou para a conversa. |
| `VAPID_PUBLIC_KEY` | Não | Chave pública correspondente (87 caracteres, base64url). O navegador a recebe pela API e a usa para se inscrever. |
| `VAPID_SUBJECT` | Não | Contato do responsável pelo serviço, que os serviços de push exigem: `mailto:alguem@exemplo.com` ou um `https://...`. |
| `WORKER_PROXIMIDADE_INTERVAL_SECONDS` | Não | **Opcional.** Intervalo, em segundos, do ciclo que verifica os alertas de proximidade (mínimo 20). Ausente, vale o intervalo geral de 5 min. Ver "Atraso do aviso" abaixo. |

As três primeiras precisam estar **todas** presentes e **combinar entre si**. Se faltar uma, o `VAPID_SUBJECT` for inválido, a privada não for uma chave válida ou a pública não corresponder à privada, o push fica desligado e o log registra o motivo (só o nome da variável, nunca o valor).

**Quem configura:** quem tem acesso ao Fly e ao GitHub (o time, não o agente). As chaves não são geradas nem guardadas pelo código. Hoje os três valores estão como secrets do repositório no GitHub e o job `deploy-mobilidade` os aplica no Fly a cada deploy (`flyctl secrets set ... --stage`), então o passo 2 abaixo é a alternativa manual.

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

**2. Cadastrar no GitHub** (o pipeline aplica no Fly; não use `fly secrets set` na mão). Sem imprimir o valor, direto do gerador:

```bash
gh secret set VAPID_PRIVATE_KEY   # cole a privada no prompt
gh secret set VAPID_PUBLIC_KEY
gh secret set VAPID_SUBJECT       # mailto:contato-do-time@exemplo.com
```

O job `deploy-mobilidade` do `deploy-fly.yml` roda `flyctl secrets set --stage` com os três antes do `flyctl deploy`, então as chaves entram no mesmo release. O passo só roda se **os três** secrets existirem; se faltar algum, ele é pulado, o deploy conclui e o push segue desligado. Os valores não aparecem nos logs (ficam em variáveis de ambiente mascaradas e a saída do `flyctl` é descartada). Para trocar o contato ou as chaves, atualize o secret no GitHub e dispare o workflow (`workflow_dispatch`).

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

### E-mail de recuperação de senha (SMTP, issue #237)

O serviço de **autenticação** (app `movecity-auth` no Fly) envia o e-mail de "Esqueci minha senha" por SMTP (`smtp.gmail.com`, porta 587, STARTTLS). São quatro secrets do GitHub, repassados ao Fly pelo job `deploy-auth` do `deploy-fly.yml`:

| Secret | Secret? | Para que serve |
|--------|---------|----------------|
| `SMTP_USER` | Não (mas não publique) | Conta Gmail usada para autenticar no SMTP. |
| `SMTP_PASSWORD` | **Sim** | **Senha de app** do Google (16 caracteres) dessa conta. Nunca a senha normal da conta. |
| `SMTP_FROM` | Não | Remetente exibido, por exemplo `Movecity <conta@gmail.com>`. |
| `FRONTEND_URL` | Não | URL do frontend em produção, sem barra final (`https://movecity-frontend.vercel.app`). Compõe o link `FRONTEND_URL/redefinir-senha?token=...`. |

**Como gerar a senha de app:**
1. Na conta Google que enviará os e-mails, ative a **verificação em duas etapas** (necessária para criar senhas de app).
2. Acesse https://myaccount.google.com/apppasswords, dê um nome (por exemplo `movecity`) e gere a senha.
3. Copie a senha na hora: o Google não a mostra de novo.

**Como cadastrar:** cada pessoa digita o valor no próprio terminal, com `gh secret set SMTP_PASSWORD` (o `gh` pede o valor de forma oculta). Repita para `SMTP_USER`, `SMTP_FROM` e `FRONTEND_URL`. O valor da senha **nunca** vai para chat, issue, PR, arquivo ou histórico do shell.

**Comportamento:** o passo do deploy só roda se **os quatro** secrets existirem; se faltar algum, é pulado e o serviço apenas registra no log que o e-mail não foi enviado (o endpoint continua respondendo normalmente). Os valores não aparecem nos logs. O link do e-mail expira em 60 minutos. Para trocar a senha de app, gere outra, atualize o secret e dispare o workflow (`workflow_dispatch`).

**URLs dos apps:** `https://movecity-gateway.fly.dev` (única que o navegador acessa), `https://movecity-auth.fly.dev`, `https://movecity-mobilidade.fly.dev`, `https://movecity-colaboracao.fly.dev`

**Comandos úteis** (troque `<app>` por um dos 4 apps):
```bash
# Listar secrets
fly secrets list --app <app>

# Atualizar secret
fly secrets set JWT_SECRET="novo-valor" --app <app>

# Deploy (aplica secrets staged)
fly secrets deploy --app <app>
```

---

## Vercel (Frontend — Next.js)

**Projeto:** `movecity-frontend`
**Repo:** `davieduardo001/tcc-ciencia-computacao-ucb`
**Deploy:** workflow `deploy-vercel.yml`, em push para `homolog` (modo `--prod`).

Variáveis lidas pelo código do frontend:

| Variável | Onde é definida | Descrição |
|----------|-----------------|-----------|
| `NEXT_PUBLIC_API_URL` | Projeto Vercel | URL do Gateway (`https://movecity-gateway.fly.dev`); sem ela, o código usa `http://localhost:8000` (`lib/api.ts`) |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Workflow (secret `GOOGLE_CLIENT_ID`) | Login via Google |
| `NEXT_PUBLIC_CARTO_API_KEY` | Workflow (secret `CARTO_API_KEY`) | Base do mapa CARTO Voyager; sem ela o mapa usa o tile padrão do OpenStreetMap |

`NEXT_PUBLIC_MAP_TILES` e `NEXT_PUBLIC_APP_NAME`, que constavam de versões anteriores deste documento, **não são lidas por nenhum código** do frontend hoje.

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

- [x] Conta e projeto `movecity` no Neon; `DATABASE_URL` nos secrets do GitHub (migrations e ingestão) e nos apps `auth`, `mobilidade` e `colaboracao`
- [x] Conta no Fly.io; 4 apps criados (`movecity-gateway`, `-auth`, `-mobilidade`, `-colaboracao`)
- [x] Tokens de deploy do Fly (1 por app) como `FLY_DEPLOY_TOKEN_*` no GitHub
- [x] Projeto `movecity-frontend` na Vercel e `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` no GitHub
- [x] `GOOGLE_CLIENT_ID` e `CARTO_API_KEY` no GitHub
- [x] `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` e `FRONTEND_URL` no GitHub (28/10/2026)
- [x] `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY` e `VAPID_SUBJECT` no GitHub (27/10/2026)
- [x] Deploy automático do backend (push em `homolog`/`main`) e do frontend (push em `homolog`) funcionando
- [ ] `RAIO_EMBARQUE_M` de volta a `100` em produção (hoje `100000`, decisão de demonstração; issue #216)
