---
name: gerenciar-commits
description: Garante que os commits do projeto sejam atômicos, sigam o padrão Conventional Commits e sejam agrupados logicamente por funcionalidade ou diretório.
---

# Skill: Gerenciar Commits Estruturados

Esta skill orienta o agente a realizar commits de forma organizada, evitando "commits gigantes" e garantindo que cada mudança tenha um propósito claro e documentado.

## <instructions>
1. **Análise de Alterações:** Antes de qualquer commit, execute `git status` e `git diff` para identificar todas as mudanças pendentes.
2. **Agrupamento Lógico (Curadoria):** Separe as mudanças em grupos lógicos. 
   - Exemplo: Mudanças em `/docs` não devem estar no mesmo commit que mudanças em `/src`, a menos que sejam estritamente interdependentes.
   - Funcionalidades distintas devem ter commits distintos.
3. **Padrão Conventional Commits:** Utilize obrigatoriamente os prefixos:
   - `feat:` Novas funcionalidades ou adições importantes.
   - `fix:` Correções de bugs.
   - `docs:` Alterações apenas em documentação.
   - `style:` Formatação, pontos e vírgulas, etc. (sem alteração de lógica).
   - `refactor:` Mudança de código que não corrige bug nem adiciona feature.
   - `chore:` Atualização de tarefas de build, configurações de ferramentas, etc.
   - `perf:` Mudanças de código focadas em performance.
4. **Verificação de Segurança:** Garanta que arquivos ignorados (como `settings.json`) ou tokens não foram incluídos acidentalmente.
5. **Proposta de Estrutura:** Antes de executar os commits, apresente ao usuário um plano:
   - "Commit 1 (docs): Descrição..."
   - "Commit 2 (feat): Descrição..."
6. **Idioma:** Mensagens de commit preferencialmente em inglês ou português (PT-BR), conforme padrão do projeto, mas a descrição da tarefa sempre em **Português (PT-BR)**.
</instructions>

## <available_resources>
- `git status`, `git diff`, `git log`: Ferramentas para análise do estado do repositório.
- `.gitignore`: Para validar o que deve ser mantido fora do controle de versão.
</available_resources>

## Exemplos de Uso
- "Agent, organize as mudanças atuais e faça os commits seguindo a skill de gerenciamento."
- "Prepare o commit da nova funcionalidade de busca separada da documentação."
