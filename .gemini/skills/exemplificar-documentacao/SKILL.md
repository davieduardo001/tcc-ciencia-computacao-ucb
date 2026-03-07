---
name: resumir-documentacao
description: Esta skill permite ao agente de IA ler, analisar e resumir a documentação existente do projeto (docs/ e AGENT.md), fornecendo uma visão geral clara e concisa do status e requisitos.
---

# Skill: Resumir Documentação

Esta skill permite ao agente de IA ler, analisar e resumir a documentação existente do projeto, extraindo os pontos principais, arquitetura e requisitos definidos sem criar novo conteúdo.

## <instructions>
1. **Explore a Documentação:** Navegue recursivamente pelo diretório `docs/` e leia o arquivo `AGENT.md` para capturar todo o contexto disponível.
2. **Sintetize Informações:** Identifique de forma objetiva o tema central, objetivos, requisitos (funcionais e não-funcionais) e as decisões arquiteturais já tomadas.
3. **Gere Resumos Estruturados:** Organize o output em seções claras, como: "Visão Geral do Projeto", "Principais Requisitos", "Arquitetura Definida" e "Status de Documentação".
4. **Apenas Leitura:** Limite-se a reportar o que já existe nos documentos. Não gere exemplos fictícios ou novos modelos de documento.
5. **Idioma:** Sempre produza o resumo em **Português (PT-BR)**.
</instructions>

## <available_resources>
- `docs/`: Repositório de requisitos, templates e decisões arquiteturais.
- `AGENT.md`: Fonte da verdade sobre o status do projeto e histórico de avanços.
</available_resources>

## Exemplos de Uso
- "Agent, use a skill de resumo para me dar um panorama de como está a documentação do TCC até agora."
- "Resuma quais requisitos já foram validados nos documentos da pasta docs/."
- "O que o AGENT.md diz sobre o estado atual do projeto?"
