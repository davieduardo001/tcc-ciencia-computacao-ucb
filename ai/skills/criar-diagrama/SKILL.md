---
name: criar-diagrama
description: Guia para criar e validar diagramas de sequência PlantUML no projeto Movecity, seguindo os padrões do CLAUDE.md.
---

# Criar Diagrama de Sequência

Esta skill orienta a criação de diagramas de sequência em PlantUML para o projeto Movecity.

## Localização

- Diagramas ficam em `docs/diagramas/sequencia/`
- Nome: `UC[numero]-[nome-curto].puml`

## Estrutura Padrão

```plantuml
@startuml UC[numero]_[NomeDiagrama]
hide footbox
title Diagrama de Sequencia - [Nome do Caso de Uso] (US #numero)

actor "Passageiro" as Passageiro
interface "TelaX" as TelaX <<interface usuario>>
:GatewayAPI <<servico gateway>>
:ControladorX <<servico [dominio]>>
:ModeloX <<modelo>>

Passageiro -> TelaX : acao
activate TelaX

TelaX -> GatewayAPI : requisicao(token, dados)
activate GatewayAPI

GatewayAPI -> GatewayAPI : verificarAssinaturaToken(token)

alt token valido
    GatewayAPI -> ControladorX : metodo(identidadeUsuario, dados)
    activate ControladorX

    ControladorX -> ModeloX : buscar/criar/atualizar(dados)
    activate ModeloX
    ModeloX --> ControladorX : resultado
    deactivate ModeloX

    ControladorX --> GatewayAPI : resposta(dados)
    deactivate ControladorX

    GatewayAPI --> TelaX : resposta(dados)
    deactivate GatewayAPI

    TelaX --> Passageiro : exibirresultado
    deactivate TelaX

else token expirado
    GatewayAPI --> TelaX : respostaErro(tokenExpirado)
    deactivate GatewayAPI

    TelaX -> TelaX : redirecionarParaLogin
    TelaX --> Passageiro : exibirAviso
    deactivate TelaX
end
```

## Participantes e Estereótipos

| Camada | Nomenclatura | Estereótipo |
|--------|--------------|-------------|
| Usuário | `actor "Passageiro"` | (nenhum) |
| Interface | `:TelaX` | `<<interface usuario>>` |
| Gateway | `:GatewayAPI` | `<<servico gateway>>` |
| Autenticação | `:ControladorAutenticacao` | `<<servico autenticacao>>` |
| Serviço | `:ServicoX` ou `:ControladorX` | `<<servico [dominio]>>` |
| Modelo | `:ModeloX` | `<<modelo>>` |

## Regras

| Regra | Detalhe |
|-------|---------|
| Gateway | Sempre presente entre frontend e backend |
| JWT | Gateway valida localmente (sem round-trip) |
| Identidade | Serviços recebem `identidadeUsuario` já validado |
| Controle | Usar `alt`/`else` para cenários alternativos |
| Lifecycle | Usar `activate`/`deactivate` em todos participantes |

## Validação

Para validar o diagrama:
1. Copiar o conteúdo do arquivo `.puml`
2. Colar em https://www.plantuml.com/plantuml/uml/
3. Verificar se renderiza corretamente
4. Conferir se todos os participantes estão presentes

## Referência

- Diagramas existentes: `docs/diagramas/sequencia/`
- Padrões: `CLAUDE.md` (seção Arquitetura de Diagramas de Sequência)
