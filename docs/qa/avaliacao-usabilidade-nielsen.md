# Avaliação de usabilidade (heurísticas de Nielsen) — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/avaliacao-usabilidade-nielsen.md>

Teste 4.3 do roteiro de software da disciplina (Projeto de Solução Computacional). Avaliação heurística da interface em produção (`movecity-frontend.vercel.app`), em 27 e 28/10/2026, feita durante a [execução dos casos de teste](execucao-casos-p1.md). Cada achado aponta a evidência (caso, imagem ou issue).

## Método e limites

- **Método:** inspeção da interface pelas 10 heurísticas de Nielsen, com severidade de 0 a 4 (0 = não é problema, 1 = cosmético, 2 = pequeno, 3 = grande, 4 = catastrófico).
- **Avaliador:** um só, durante a execução dos casos, em desktop (1366 px) e celular (390 px). A técnica pede **3 a 5 avaliadores independentes**, porque um só costuma achar menos da metade dos problemas.
- **Não houve teste com usuários reais** (trabalhadores de turno, estudantes). Esta avaliação não substitui isso.
- **Próximo passo recomendado:** 2 ou 3 pessoas do grupo repetirem o percurso abaixo, cada uma por conta própria, e depois comparar com esta tabela.
- **Percurso avaliado:** cadastro e login, tutorial, buscar linha, ver ônibus, abrir parada, planejar rota, pegar o ônibus, encerrar a viagem, reportar ocorrência, preferências de alerta.

## Resultado por heurística

| # | Heurística | Achado | Sev. | Evidência |
|---|---|---|---|---|
| 1 | Visibilidade do estado do sistema | **Bom:** a faixa "Em viagem · linha X" mostra a próxima parada e quantas faltam; o popup do ônibus diz "Posição de 59s atrás"; o selo separa "ao vivo" de "previsto". **Ruim:** o selo "ao vivo" já conviveu com posição de 2 min atrás; o embarque no card de rota mostra o selo mas não os minutos. | 2 | CT-VIA-02, CT-ETA-02, CT-ROT-06, #232 |
| 2 | Correspondência com o mundo real | **Bom:** textos como "Peguei este ônibus", "Cheguei", "Descer nesta parada". **Ruim:** "Parada sem nome" no embarque e no desembarque; o aviso de saídas do terminal precisou ser explicado ("não é a hora em que passa nesta parada"). | 3 | #232, CT-ETA-04 |
| 3 | Controle e liberdade do usuário | **Bom:** "Tirar destino" desfaz, "Cheguei" pode ser tocado de novo sem erro, "Pular" no tutorial e "Ver tutorial novamente" nas configurações. **Ruim:** não vi como desfazer ou apagar um reporte enviado. | 2 | CT-VIA-02, CT-VIA-03, CT-MAP-09, CT-COL-03 |
| 4 | Consistência e padrões | O painel de linha e a folha de rota se comportavam de modo diferente no celular (corrigido pela #217, não conferido em aparelho real); havia dois controles de usuário na barra de cima (corrigido pela #227); o menu já teve "Linhas" e "Rotas" duplicando busca e planejador (corrigido pela #179). | 2 | #217, #227, #179, CT-ROT-07 |
| 5 | Prevenção de erros | **Bom:** o limite de 3 reportes por hora avisa; o medidor de senha mostra os requisitos. **Ruim (corrigido):** o cadastro aceitava terminar sem aceitar os termos (#211). **Ruim:** "Buscar parada" só dispara com Enter e não tem botão (como no protótipo); no desktop não há dica, e só o teclado do celular mostra a tecla "buscar". | 2 | CT-COL-03, CT-AUT-01, #211, CT-PAR-02, #236 |
| 6 | Reconhecimento em vez de memorização | "Parada sem nome" obriga o usuário a lembrar onde fica a parada; o texto de acessibilidade do embarque traz só as coordenadas. O tutorial de 4 etapas ajuda, mas só aparece no primeiro acesso. | 3 | #232, CT-MAP-09 |
| 7 | Flexibilidade e eficiência de uso | **Bom:** "Minha localização" como origem, rotas salvas com "Ir", filtro por linha nas ocorrências. **Ruim:** "Ir" põe as coordenadas do usuário na URL (problema de privacidade, não de eficiência). | 2 | CT-ROT-05, CT-COL-04, #231 |
| 8 | Estética e design minimalista | **Bom:** o card de rota mostra só o embarque e o desembarque, sem as paradas do meio. **Ruim:** o painel da parada junta linhas, chegadas e saídas do terminal numa lista longa, e a diferença entre "chegando" e "saída do terminal" depende do aviso em texto pequeno. | 2 | CT-ROT-06, CT-PAR-01 |
| 9 | Ajudar a reconhecer, diagnosticar e corrigir erros | **Ruim (corrigido):** com a sessão expirada o app mostrava "Nenhum ônibus em operação" em vez de pedir novo login (#221). **Ruim (aberto):** "Nenhuma linha liga esses dois pontos" apareceu uma vez para um par que depois deu 5 opções, sem separar "sem linha" de "erro" (#233). **Bom:** "Você atingiu o limite de reportes" explica o motivo, mas não diz por quanto tempo. | 3 | #221, #233, CT-COL-03 |
| 10 | Ajuda e documentação | **Bom:** tutorial em 4 etapas e botão de ajuda. **Ruim:** as telas mandam "verificar o e-mail" ou dizem que o usuário "receberá um link", e o sistema não envia e-mails; a ajuda contradiz o comportamento. | 3 | CT-MAP-09, #230 |

## Síntese

- **Mais graves (severidade 3):** nomes de parada ausentes (#232), mensagens sobre e-mail que não existe (#230), erro de consulta confundido com "sem resultado" (#233).
- **Menores (severidade 2):** "Buscar parada" sem dica de que a busca sai pelo Enter no desktop.
- **Já corrigidos:** termos no cadastro (#211), sessão expirada (#221), controle duplicado (#227), menu duplicado (#179).
- **Pontos fortes:** vocabulário do dia a dia, estado da viagem sempre visível, honestidade sobre a origem do tempo ("ao vivo", "previsto", "Sem previsão no momento"), ações reversíveis.
- **Sem cobertura:** acessibilidade (leitor de tela, contraste medido, tamanho de toque), conexão lenta e usuários reais.
