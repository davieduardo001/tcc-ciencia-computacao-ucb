# Rascunhos ASCII — Diagramas do Documento de Arquitetura

Arquivo de rascunho para conversão futura dos diagramas para Mermaid, PlantUML ou ferramenta similar.
Cada seção identifica a figura correspondente no `documento_arquitetura.md`.

---

## Figura 1 — Diagrama de Classes do Domínio (Seção 4.1)

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    Usuario      │       │     Sessao      │       │  LinhaNibus    │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id: UUID        │1     *│ id: UUID        │       │ id: UUID        │
│ nome: String    ├───────┤ usuarioId: UUID  │       │ numero: String  │
│ email: String   │       │ token: String   │       │ nome: String    │
│ senhaHash: String│      │ criadaEm: DateTime│      │ empresa: String │
│ criadoEm: DateTime│     │ expiraEm: DateTime│      │ ativa: Boolean  │
│ ativo: Boolean  │       └─────────────────┘       └────────┬────────┘
└────────┬────────┘                                          │1
         │1                                                  │
         │*                                          ┌───────┴────────┐
┌────────┴────────┐                                 │    Parada      │
│ RotaFavorita    │       ┌─────────────────┐        ├────────────────┤
├─────────────────┤       │   Ocorrencia    │        │ id: UUID       │
│ id: UUID        │       ├─────────────────┤       *│ nome: String   │
│ usuarioId: UUID  │      │ id: UUID        │        │ latitude: Float │
│ linhaId: UUID   │       │ usuarioId: UUID  │       │ longitude: Float│
│ criadaEm: DateTime│     │ linhaId: UUID   │        │ linhaId: UUID  │
└─────────────────┘       │ tipo: Enum      │        └────────────────┘
                          │ descricao: String│
                          │ latitude: Float │       ┌─────────────────┐
                          │ longitude: Float│       │  PosicaoOnibus  │
                          │ confirmacoes: Int│       ├─────────────────┤
                          │ criadaEm: DateTime│     │ id: UUID        │
                          │ status: Enum    │       │ linhaId: UUID   │
                          └─────────────────┘       │ latitude: Float │
                                                    │ longitude: Float│
                                                    │ velocidade: Float│
                                                    │ atualizadaEm: DateTime│
                                                    └─────────────────┘
```

---

## Figura 2 — Diagrama de Pacotes da Arquitetura Lógica (Seção 4.3)

```
┌──────────────────────────────────────────────────────────────────┐
│                    <<interface usuario>>                          │
│                    Camada de Apresentação                         │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Páginas    │  │ Componentes │  │    Módulo de Mapa        │  │
│  │ (App Router)│  │    React    │  │  (Leaflet JS + OSM)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└──────────────────────────────────────┬───────────────────────────┘
                                       │ HTTPS / WebSocket
┌──────────────────────────────────────▼───────────────────────────┐
│                    <<servico gateway>>                             │
│                       API Gateway                                  │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐                      │
│  │ Roteamento       │  │ Validação JWT     │                      │
│  │ de Requisições   │  │ (local, sem       │                      │
│  │                  │  │  round-trip)      │                      │
│  └──────────────────┘  └──────────────────┘                      │
└──────┬───────────────────────┬──────────────────┬────────────────┘
       │                       │                  │
┌──────▼──────┐   ┌────────────▼────────┐   ┌────▼──────────────────┐
│<<servico    │   │<<servico            │   │<<servico              │
│autenticacao>>│  │mobilidade>>         │   │colaboracao>>          │
│             │   │                     │   │                       │
│ Autenticacao│   │ Mapa / GPS          │   │ Reportes /            │
│ de Usuarios │   │ Linhas / Paradas    │   │ Notificacoes          │
│ Sessoes     │   │ Rotas / ETA         │   │ Alertas               │
└──────┬──────┘   └──────────┬──────────┘   └──────────┬────────────┘
       │                     │                          │
┌──────▼─────────────────────▼──────────────────────────▼────────────┐
│                        <<modelo>>                                    │
│                   Camada de Dados / Persistência                     │
│                                                                      │
│  ┌──────────────────────────┐    ┌──────────────────────────────┐  │
│  │  PostgreSQL + PostGIS    │    │  API Externa: SEMOB/GDF      │  │
│  │  (Neon serverless)       │    │  (GeoJSON — GPS em tempo     │  │
│  │                          │    │   real)                      │  │
│  └──────────────────────────┘    └──────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Figura 4 — Diagrama de Implantação (Seção 7)

```
┌───────────────────────────────────────────────────────────────────┐
│                         INTERNET                                   │
└────────────────────────┬───────────────────────────────────────────┘
                         │ HTTPS
          ┌──────────────▼──────────────┐
          │    CDN / Vercel Edge         │
          │  (Frontend Next.js — SSR)    │
          │  Nó: Vercel ou Fly.io        │
          └──────────────┬──────────────┘
                         │ HTTPS / REST
          ┌──────────────▼──────────────┐
          │    Fly.io — Backend          │
          │  (FastAPI via Docker)        │
          │  ┌────────────────────────┐ │
          │  │    API Gateway         │ │
          │  ├────────────────────────┤ │
          │  │ Serviço Autenticação   │ │
          │  ├────────────────────────┤ │
          │  │ Serviço Mobilidade     │ │
          │  ├────────────────────────┤ │
          │  │ Serviço Colaboração    │ │
          │  └────────────────────────┘ │
          └────────────┬──────┬─────────┘
                       │      │
         ┌─────────────▼─┐  ┌─▼──────────────────────────┐
         │ Neon (PaaS)   │  │  API SEMOB/GDF (externa)    │
         │ PostgreSQL    │  │  GPS GeoJSON em tempo real  │
         │ + PostGIS     │  └─────────────────────────────┘
         └───────────────┘
```

---

## MER — Modelo Entidade-Relacionamento (Seção 8)

```
USUARIO (id PK, nome, email UNIQUE, senha_hash, criado_em, ativo)
    |
    |--[1:N]--> SESSAO (id PK, usuario_id FK, token UNIQUE, criada_em, expira_em)
    |
    |--[1:N]--> ROTA_FAVORITA (id PK, usuario_id FK, linha_id FK, criada_em)
    |
    |--[1:N]--> OCORRENCIA (id PK, usuario_id FK, linha_id FK, tipo, descricao,
    |                        geom POINT, confirmacoes, criada_em, status)

LINHA_ONIBUS (id PK, numero UNIQUE, nome, empresa, ativa)
    |
    |--[1:N]--> PARADA (id PK, linha_id FK, nome, sequencia, geom POINT)
    |
    |--[1:N]--> POSICAO_ONIBUS (id PK, linha_id FK, geom POINT,
                                 velocidade, atualizada_em)
```
