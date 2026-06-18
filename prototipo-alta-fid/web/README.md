# Protótipo de Alta Fidelidade — Movecity (Web)

Protótipo **navegável e estático** (HTML + CSS + JavaScript puro, **sem backend**), feito apenas
para demonstração de telas. Cobre as funcionalidades principais do backlog do Movecity
(issue [#33](https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/issues/33)).

> O mapa não é plotado de verdade — é usado um **background** estático (recorte do Figma) com
> marcadores ilustrativos, conforme combinado. O foco é a demonstração das interfaces web.

## Como abrir

Basta abrir `index.html` no navegador (funciona via `file://`, sem servidor):

```bash
xdg-open prototipo-alta-fid/web/index.html
```

A página inicial (`index.html`) é um índice de todas as telas. O fluxo "real" começa em
`login.html`.

## Telas e User Stories cobertas

| Tela | Arquivo | US |
|---|---|---|
| Login (e-mail/senha + Google) | `login.html` | #10, #12 |
| Criar conta (+ LGPD) | `criar-conta.html` | #11 |
| Recuperar senha | `recuperar-senha.html` | #13 |
| Link enviado | `link-enviado.html` | #13 |
| Redefinir senha | `redefinir-senha.html` | #13 |
| Mapa / localização atual | `mapa.html` | #14 |
| Buscar linha por número | `buscar-linha.html` | #15 |
| Linha em tempo real (posição, trajeto, paradas, ETA) | `linha.html` | #16, #17, #19 |
| Detalhes da parada (próximas linhas + ETA) | `parada.html` | #18, #19 |
| Buscar parada por nome/endereço | `buscar-parada.html` | #21 |
| Calcular rota origem → destino | `calcular-rota.html` | #20 |
| Reportar ocorrência | `reportar.html` | #23 |
| Ocorrências da comunidade + confirmar | `ocorrencias.html` | #24, #26 |
| Rotas/linhas/paradas favoritas | `favoritos.html` | #25 |
| Central de alertas | `alertas.html` | #22, #27, #28 |
| Preferências de notificação | `preferencias.html` | #29 |
| Tutorial / onboarding | `tutorial.html` | #30 |
| Termos e privacidade | `termos.html` | #32 |
| Perfil / conta (logout) | `perfil.html` | #31 (parcial) |

## Estrutura

```
web/
├── index.html              # índice navegável de todas as telas
├── login.html ...          # uma tela por arquivo
├── assets/
│   ├── css/style.css       # design system (cores, componentes)
│   ├── js/app.js           # injeta sidebar/topbar + interações (tabs, modais, toggles)
│   └── img/                # backgrounds de mapa (recortes do Figma)
└── README.md
```

## Decisões

- **Sem framework / sem build:** HTML/CSS/JS puro para rodar direto no navegador.
- **Shell compartilhado:** `app.js` injeta a barra lateral e a topbar nas telas internas
  (páginas com `class="app-shell"`), evitando duplicação. As telas de autenticação são
  full-screen.
- **Design** extraído do arquivo `../Movecity.fig` (cores, gradientes e layout). As telas do
  épico Colaboração ainda não existiam no Figma e foram desenhadas seguindo a mesma linguagem.
- **Foco web (desktop)**; o layout é responsivo o suficiente para telas menores.
