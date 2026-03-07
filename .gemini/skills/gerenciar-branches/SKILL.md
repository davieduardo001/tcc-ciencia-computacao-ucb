---
name: gerenciar-branches
description: Garante que o projeto utilize branches de forma organizada, verificando com o usuário antes de qualquer commit se as mudanças devem ir para uma nova branch ou branch separada.
---

# Skill: Gerenciar Branches do Projeto

Esta skill orienta o agente a garantir que o desenvolvimento siga um fluxo de branches organizado, evitando commits diretos na branch principal sem confirmação.

## <instructions>
1. **Verificação de Estado:** Antes de realizar qualquer commit, execute `git branch` para listar as branches existentes e identificar a branch atual.
2. **Consulta ao Usuário:** Apresente ao usuário a lista de branches ativas e pergunte:
   - "Deseja criar uma nova branch para estas alterações?"
   - "Deseja commitar em uma das branches existentes? (Liste-as)"
   - "Deseja continuar na branch atual [nome da branch]?"
3. **Criação de Branch:** Se o usuário optar por uma nova branch, sugira um nome baseado no tipo de alteração (ex: `feat/nome-da-feature`, `fix/correcao-bug`, `docs/atualizacao-doc`) seguindo o padrão Git Flow simplificado.
4. **Execução:** Só proceda com o commit após a definição da branch de destino. Se uma nova branch for criada, mude para ela antes de commitar.
5. **Idioma:** Toda a interação com o usuário sobre branches deve ser em **Português (PT-BR)**.
</instructions>

## <available_resources>
- `git branch`: Para listar branches locais.
- `git checkout -b`: Para criar e mudar para uma nova branch.
- `git checkout`: Para alternar entre branches existentes.
</available_resources>

## Exemplos de Uso
- "Antes de commitar, verifique a estratégia de branch seguindo a skill."
- "Organize as branches para este novo desenvolvimento."
