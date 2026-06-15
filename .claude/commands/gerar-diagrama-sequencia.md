# Gerar Diagrama de Sequência UML (PlantUML)

Gera diagramas de sequência UML em PlantUML seguindo a arquitetura real do Movecity — microserviços com API Gateway (US #31) entre frontend e qualquer serviço de backend.

## Critérios obrigatórios (aplicar em TODOS os diagramas da sessão)

1. **API Gateway obrigatório** — toda requisição do frontend passa por `:GatewayAPI <<servico gateway>>` antes de qualquer serviço de backend. Nunca ignorar o Gateway.

2. **Estereótipos por tipo de participante:**
   - Frontend: `<<interface usuario>>`
   - Gateway: `<<servico gateway>>`
   - Serviços de domínio: `<<servico [dominio]>>`
   - Auth: `<<servico autenticacao>>`
   - Modelos: `<<modelo>>`
   - Notificação: `<<servico notificacao>>`

3. **Ator** inicia a partir da View (fora das lifelines de serviço).

4. **Nível de análise** — sem implementação, framework ou tecnologia.

5. **`activate` / `deactivate`** balanceados em toda lifeline ativa.

6. **`hide footbox`** — sempre presente.

7. **Validação de sessão via Gateway (US #31)** — obrigatória em recursos protegidos. O Gateway valida JWT localmente e o bloco `alt` tem 3 ramificações:
   - Token válido → encaminha ao serviço com `identidadeUsuario`
   - Token expirado → renova via `:ControladorAutenticacao` + `:ModeloSessao` → reencaminha (transparente)
   - Token inválido/refresh revogado → `401` → View redireciona para login com `"Sua sessao expirou. Faca login novamente."`

8. **Serviços de domínio NÃO validam sessão** — responsabilidade exclusiva do Gateway.

9. **Loops de tempo real** usam o caminho feliz via Gateway (sem repetir o bloco `alt` completo).

## Estrutura base PlantUML

```plantuml
@startuml
hide footbox
title Diagrama de Sequencia - [Titulo]

actor "[Ator]" as Ator

participant ":[TelaDominio]" as View <<interface usuario>>
participant ":GatewayAPI" as Gateway <<servico gateway>>
participant ":ControladorAutenticacao" as Auth <<servico autenticacao>>
participant ":ModeloSessao" as Sessao <<modelo>>
participant ":[ServicoDominio]" as Service <<servico [dominio]>>
participant ":[ModeloDominio]" as Model <<modelo>>

Ator -> View : acaoDoUsuario()
activate View

View -> Gateway : requisicao(token, [params])
activate Gateway

Gateway -> Gateway : verificarAssinaturaToken(token)

alt token valido
  Gateway -> Service : encaminharRequisicao(req, identidadeUsuario)
  activate Service
  Service -> Model : operacao([params])
  activate Model
  Model --> Service : dados
  deactivate Model
  Service --> Gateway : resposta(dados)
  deactivate Service
  Gateway --> View : retornarResposta(dados)
  View -> View : exibirConteudo(dados)

else token expirado
  Gateway -> Auth : renovarSessao(refreshToken)
  activate Auth
  Auth -> Sessao : verificarTokenRenovacao(refreshToken)
  activate Sessao
  Sessao --> Auth : tokenValido
  deactivate Sessao
  Auth -> Sessao : emitirNovoTokenAcesso(usuarioId)
  activate Sessao
  Sessao --> Auth : novoToken
  deactivate Sessao
  Auth --> Gateway : sessaoRenovada(novoToken)
  deactivate Auth
  Gateway -> Service : encaminharRequisicaoOriginal(req, identidadeUsuario)
  activate Service
  Service -> Model : operacao([params])
  activate Model
  Model --> Service : dados
  deactivate Model
  Service --> Gateway : resposta(dados)
  deactivate Service
  Gateway --> View : retornarResposta(dados)
  View -> View : exibirConteudo(dados)

else token invalido ou refresh revogado
  Gateway --> View : notificarNaoAutorizado(401)
  View -> View : redirecionarParaLogin("Sua sessao expirou. Faca login novamente.")
end

deactivate Gateway
deactivate View
@enduml
```

## Fluxo de execução

**Se o caso de uso não foi fornecido**, solicitar: nome, ator, pré-condição, fluxo principal, fluxos alternativos.

**Com o caso de uso em mãos**, substituir os placeholders `[...]` pelo domínio específico e adicionar a lógica de negócio dentro dos blocos `alt token valido` e `else token expirado`.

## Saída esperada

1. Bloco PlantUML completo e pronto para renderização
2. Descrição textual resumida do fluxo (2–4 linhas, PT-BR)
3. Pergunta sobre fluxos alternativos, se relevante

---

**Uso:** `/gerar-diagrama-sequencia [caso de uso opcional]`

**Referências:** `docs/diagramas/sequencia/` — padrão já aplicado em UC14–UC21. Issues #11 e #31 — fonte de verdade da arquitetura.
