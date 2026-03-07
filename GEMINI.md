# Diretrizes do Projeto: TCC Ciência da Computação UCB

Este arquivo define as regras fundamentais para a atuação da IA neste repositório.

## Contexto do Projeto
- **Objetivo:** Trabalho de Conclusão de Curso (TCC) em Ciência da Computação na UCB.
- **Fase Atual:** Exploração inicial e definição de tema.
- **Metodologia:** Desenvolvimento focado em "Agentic Workflow" (Fluxo Agêntico).

## Regras de Atuação
1. **Idioma:** Toda a documentação, comentários de código e interações devem ser preferencialmente em **Português (PT-BR)**, a menos que a linguagem de programação ou padrões técnicos exijam inglês.
2. **Proatividade Agêntica:** A IA deve atuar como um colaborador sênior, sugerindo arquiteturas, temas de pesquisa e metodologias que se alinhem ao estado da arte da computação.
3. **Documentação Contínua:** Cada avanço no código ou na pesquisa deve ser refletido no `AGENT.md` e em arquivos de documentação específicos.
4. **Rigor Acadêmico:** Como se trata de um TCC, as sugestões devem manter um alto padrão acadêmico e técnico.

## Fluxo de Trabalho
- Antes de implementar grandes mudanças, proponha uma estratégia de execução.
- Mantenha o arquivo `AGENT.md` sempre atualizado como a "fonte da verdade" para outros agentes que venham a trabalhar no projeto.

## Sincronização de Contexto (Skill)
- **Leitura de Documentação:** Sempre que iniciar uma nova tarefa complexa, o agente deve ler os arquivos em `docs/**` para se atualizar sobre a arquitetura, requisitos e decisões de design.
- **Templates:** Utilize os modelos em `docs/templates/` para manter a consistência acadêmica e técnica exigida pela UCB.
- **Evolução:** Conforme novos documentos forem adicionados, a base de conhecimento do agente deve ser expandida automaticamente através da leitura recursiva deste diretório.
