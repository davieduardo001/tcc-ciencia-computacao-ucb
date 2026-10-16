# Casos de Teste Manuais — Movecity


> 📎 Ver este arquivo no GitHub: <https://github.com/davieduardo001/tcc-ciencia-computacao-ucb/blob/main/docs/qa/casos-de-teste.md>

Casos de aceitação manual, derivados dos cenários BDD das issues das USs entregues. Antes de executar, leia os pré-requisitos e a escala de severidade no [plano de testes](plano-de-testes.md). A rastreabilidade US → caso → PR → teste automatizado está na [matriz](matriz-rastreabilidade.md).

> **Estado de execução.** Estes casos foram **escritos, mas não executados**: todos estão como `Não executado` em 16/10/2026. O que foi executado e medido nesta data são as suítes automatizadas (ver o [relatório unitário](relatorio-testes-unitarios.md)). Ao executar, registre o estado, a data, o ambiente e o responsável.

**Legenda:** Sev. = severidade (C crítica, A alta, M média, B baixa) · Pri. = prioridade (P1 regressão mínima, P2, P3) · `<br>` separa passos.

## 1. Acesso (autenticação e sessão)

| ID | Cenário (US) | Pré-condição | Passos | Resultado esperado | Sev. | Pri. | Estado |
|---|---|---|---|---|---|---|---|
| CT-AUT-01 | Cadastro com todos os campos (#11 c1, c5) | Sem sessão; e-mail de teste não cadastrado | 1. Abrir a tela de cadastro<br>2. Preencher nome, e-mail e senha válida<br>3. Aceitar os termos<br>4. Enviar | Conta criada e usuário autenticado; sem o aceite dos termos o envio não é permitido | A | P1 | Não executado |
| CT-AUT-02 | Login com e-mail e senha (#10 c1, c2) | Conta de teste existente | 1. Abrir o login<br>2. Entrar com credenciais corretas<br>3. Sair e tentar de novo com senha errada | Com credenciais corretas redireciona ao mapa; com senha errada mostra "Usuário ou senha inválidos" e não autentica | A | P1 | Não executado |
| CT-AUT-03 | Sessão persiste e renova (#10 c3, #31 c1, c2) | Logado | 1. Recarregar a página<br>2. Fechar e reabrir a aba<br>3. Usar o app após a expiração do token de acesso | Continua logado, sem novo login, ao voltar em até 7 dias; o token é renovado sem pedir login (cookies httpOnly) | A | P1 | Não executado |
| CT-AUT-04 | Login com Google (#12 c1) | Conta Google disponível | 1. Tocar em entrar com Google<br>2. Concluir o consentimento | Entra no app; primeiro acesso cria a conta | M | P2 | Não executado |
| CT-AUT-05 | Esqueci a senha (#13, #133 c1 a c7) | Conta de teste existente | 1. Em "Esqueci a senha", informar o e-mail<br>2. Repetir com e-mail inexistente<br>3. Abrir o link recebido e definir nova senha<br>4. Usar link expirado ou inválido<br>5. Informar confirmação diferente | Mensagem igual para e-mail existente e inexistente (não revela quem tem conta); senha redefinida com token válido; token inválido/expirado e confirmação divergente são recusados; excesso de tentativas é limitado | A | P2 | Não executado |
| CT-AUT-06 | Logout (#31 c4) | Logado | 1. Sair pelo menu | Sessão encerrada; rotas protegidas voltam ao login | A | P1 | Não executado |
| CT-AUT-07 | Sessão inválida sem renovação (#31 c3) | Cookies apagados ou adulterados | 1. Apagar os cookies no DevTools<br>2. Acessar uma tela protegida | Redireciona ao login; sem erro técnico na tela | M | P2 | Não executado |

## 2. Mapa, linha e rastreamento

| ID | Cenário (US) | Pré-condição | Passos | Resultado esperado | Sev. | Pri. | Estado |
|---|---|---|---|---|---|---|---|
| CT-MAP-01 | Mapa com localização atual (#14 c1) | Logado; permissão de localização concedida | 1. Abrir o mapa | Mapa centrado na posição do usuário, com marcador | A | P1 | Não executado |
| CT-MAP-02 | Localização negada (#14 c2) | Logado; permissão negada no navegador | 1. Abrir o mapa | Aparece o aviso "Não foi possível obter sua localização"; o app não quebra | A | P1 | Não executado |
| CT-MAP-03 | Movimentação em tempo real (#14 c3) | Localização concedida; DevTools Sensors | 1. Alterar a localização simulada | O marcador do usuário se desloca suavemente até a nova posição | M | P2 | Não executado |
| CT-MAP-04 | Buscar linha com resultado (#15 c1, #17 c1, c2) | Linha existente (ex.: `0.110`) | 1. Digitar o número na busca do topo<br>2. Escolher a sugestão | Mostra nome, sentido, trajeto desenhado e paradas ao longo dele | A | P1 | Não executado |
| CT-MAP-05 | Linha não encontrada (#15 c2) | Logado | 1. Buscar um número inexistente | Mensagem de linha não encontrada; sem trajeto antigo na tela | A | P1 | Não executado |
| CT-MAP-06 | Sentido de operação (#17 c3) | Linha buscada | 1. Observar o trajeto | Seta indica o sentido; ao tocar numa parada abre o painel | M | P2 | Não executado |
| CT-MAP-07 | Ônibus no mapa e atualização (#16 c1, c2) | Linha com ônibus em operação | 1. Buscar a linha<br>2. Aguardar ~30 s sem recarregar | Ícones dos ônibus sobre o trajeto; posições se atualizam sozinhas | A | P2 | Não executado |
| CT-MAP-08 | Nenhum veículo em operação (#16 c3) | Linha sem ônibus (madrugada) | 1. Buscar a linha | Aviso de que não há ônibus em operação; mostra a próxima saída prevista do terminal | M | P2 | Não executado |
| CT-MAP-09 | Tutorial no primeiro acesso (#30 c1, c2, c3) | Conta nova (primeiro acesso) | 1. Entrar pela primeira vez<br>2. Tocar em "Pular"<br>3. Em Configurações, escolher "Ver tutorial novamente" | O tutorial em etapas (busca de linha, mapa, reporte de ocorrência, rota favorita) aparece sozinho no primeiro acesso; pular não o reabre no acesso seguinte; ao rever, recomeça do início | M | P3 | Não executado |

## 3. Parada e tempo de chegada

| ID | Cenário (US) | Pré-condição | Passos | Resultado esperado | Sev. | Pri. | Estado |
|---|---|---|---|---|---|---|---|
| CT-PAR-01 | Detalhes de uma parada (#18 c1, #174) | Linha buscada | 1. Tocar numa parada | Painel com nome, código e linhas que passam; seção "Chegando nesta parada"; saídas do terminal separadas por linha e no dia correto | A | P1 | Não executado |
| CT-PAR-02 | Parada sem horários (#18 c2) | Parada sem horário no dia | 1. Abrir a parada | Mensagem de que não há saída prevista; sem lista vazia quebrada | M | P2 | Não executado |
| CT-PAR-03 | Fechar painel e resposta atrasada (#18 c3, #174) | Linha com várias paradas | 1. Tocar na parada A e logo na B<br>2. Fechar o painel antes de carregar | O painel mostra só a B; fechar não o reabre depois | M | P2 | Não executado |
| CT-PAR-04 | "Chegando nesta parada" (#179/#185) | Parada com ônibus a caminho | 1. Abrir a parada | Por linha: tempo com selo (ao vivo ou previsto) ou "Sem previsão no momento"; nunca um número sem origem | A | P1 | Não executado |

## 4. Tempo estimado de chegada (ETA)

| ID | Cenário (US) | Pré-condição | Passos | Resultado esperado | Sev. | Pri. | Estado |
|---|---|---|---|---|---|---|---|
| CT-ETA-01 | ETA no marcador do ônibus (#19 c1, c4) | Localização concedida; ônibus em movimento | 1. Buscar a linha<br>2. Tocar no ônibus | Popup traz o tempo até a parada do usuário, com o nome da parada e o selo "ao vivo" | A | P1 | Não executado |
| CT-ETA-02 | ETA indisponível (#19 c3, c5) | Ônibus parado ou sem GPS | 1. Tocar no ônibus | "Sem previsão no momento"; não mostra tempo inventado | A | P1 | Não executado |
| CT-ETA-03 | ETA atualiza sozinho (#19 c2) | Ônibus em movimento | 1. Manter o popup aberto ~1 min | O tempo muda sem recarregar a página | M | P2 | Não executado |
| CT-ETA-04 | Rótulo de origem de cada tempo (#179) | Rota e parada abertas | 1. Comparar "Próximas saídas do terminal" e "Chegando nesta parada" | Saída do terminal nunca é apresentada como passagem na parada; cada tempo diz a origem | A | P2 | Não executado |

## 5. Rotas

| ID | Cenário (US) | Pré-condição | Passos | Resultado esperado | Sev. | Pri. | Estado |
|---|---|---|---|---|---|---|---|
| CT-ROT-01 | Rota simples (#20 c1) | Origem e destino atendidos por uma linha | 1. Tocar em "Para onde você vai?"<br>2. Informar origem e destino<br>3. Calcular | Opções de rota com a linha, duração e linha do tempo (caminhar, embarcar, viajar, descer) | A | P1 | Não executado |
| CT-ROT-02 | Rota com baldeação (#20 c2, #159) | Par origem e destino que exige duas linhas | 1. Calcular a rota | Mostra as duas linhas e o ponto de troca; a duração indica se é ao vivo, parcial ou estimada | A | P1 | Não executado |
| CT-ROT-03 | Nenhuma rota (#20 c3) | Destino sem atendimento | 1. Calcular | Mensagem de nenhuma rota disponível | M | P2 | Não executado |
| CT-ROT-04 | Destino por nome ou endereço (#20 c5) | Logado | 1. Digitar "Rodoviária" no destino | Sugestões de lugares; o escolhido vira destino | M | P2 | Não executado |
| CT-ROT-05 | Rota favorita (#25 c1, c2, c3) | Logado; rota calculada | 1. Salvar a rota como favorita<br>2. Abrir "Rotas Salvas" e tocar em "Ir"<br>3. Remover | Salva; ao abrir recalcula com origem e destino preenchidos; remove da lista | M | P2 | Não executado |
| CT-ROT-06 | Paradas de subir e descer com tempo (#190) | Rota calculada; ônibus da linha em operação | 1. Escolher uma opção<br>2. Ver o mapa e o card | Só as paradas de subir e descer de cada trecho aparecem, com o tempo do ônibus daquela linha e o selo de origem; sem dado vira "Sem previsão no momento" | A | P2 | Não executado |
| CT-ROT-07 | Menu sem duplicidade e contraste (#179) | Logado | 1. Abrir o menu e a tela de rotas | Não há "Linhas" nem "Rotas" duplicando busca e planejador; número da linha legível; botão de favorito estilizado | M | P3 | Não executado |

## 6. Colaboração (ocorrências)

| ID | Cenário (US) | Pré-condição | Passos | Resultado esperado | Sev. | Pri. | Estado |
|---|---|---|---|---|---|---|---|
| CT-COL-01 | Reportar ocorrência (#23 c1) | Logado; linha de teste | 1. Abrir Reportar<br>2. Escolher tipo, linha e local<br>3. Enviar | Ocorrência registrada e visível a outros passageiros | A | P2 | Não executado |
| CT-COL-02 | Reporte sem autenticação (#23 c2) | Sem sessão | 1. Tentar acessar a tela de reporte | Pede login | A | P2 | Não executado |
| CT-COL-03 | Limite de reportes (#23 c3) | Logado | 1. Enviar reportes repetidos até o limite | Aviso de limite atingido | M | P3 | Não executado |
| CT-COL-04 | Ver ocorrências de outros (#24 c1, c2) | Ocorrência criada por outra conta | 1. Abrir Ocorrências<br>2. Filtrar por linha | Lista ativa, da mais recente à mais antiga; selo "Confirmada" ou "Aguardando confirmação"; sem mostrar quem reportou | A | P2 | Não executado |
| CT-COL-05 | Expiração (#24 c3) | Ocorrência com mais de 60 min sem confirmação | 1. Abrir Ocorrências | Ocorrência expirada não aparece | M | P3 | Não executado |

## 7. Notificações e alertas

| ID | Cenário (US) | Pré-condição | Passos | Resultado esperado | Sev. | Pri. | Estado |
|---|---|---|---|---|---|---|---|
| CT-NOT-01 | Preferências de notificação (#29 c1, c2, c3) | Logado | 1. Abrir Configurações<br>2. Escolher a antecedência (5, 10, 30 ou 60 min)<br>3. Desativar um tipo e depois todos | Preferências salvas; os alertas respeitam a antecedência e os tipos ativos; com tudo desativado nada é enviado até reativar | M | P2 | Não executado |
| CT-NOT-02 | Alerta de atraso (#27) | Linha acompanhada com atraso | 1. Acompanhar a linha<br>2. Aguardar o ciclo do worker | Alerta de atraso disparado; atualizado se o atraso aumenta; cancelado quando normaliza | M | P3 | Não executado |

## 8. Viagem e aviso de proximidade

| ID | Cenário (US) | Pré-condição | Passos | Resultado esperado | Sev. | Pri. | Estado |
|---|---|---|---|---|---|---|---|
| CT-VIA-01 | Pegar o ônibus (#171 c1) | Localização simulada a até 100 m de um ônibus da linha | 1. Buscar a linha<br>2. Tocar no ônibus<br>3. Tocar em "Peguei este ônibus" | Viagem registrada; aparece a faixa "Em viagem · linha X" no topo; o tempo de espera some | A | P1 | Não executado |
| CT-VIA-02 | Acompanhar a viagem (#171 c2) | Em viagem, com destino | 1. Tocar numa parada<br>2. Tocar em "Descer nesta parada" | A faixa mostra a próxima parada e quantas faltam; "Tirar destino" desfaz | A | P1 | Não executado |
| CT-VIA-03 | Encerrar a viagem (#171 c3) | Em viagem | 1. Tocar em "Cheguei" | A faixa some e o app volta ao estado normal; tocar de novo não dá erro | A | P1 | Não executado |
| CT-VIA-04 | Sem veículo próximo (#171 c4) | Localização longe de qualquer ônibus da linha | 1. Tocar em "Peguei este ônibus" | Mensagem de que não foi possível confirmar o embarque; nenhuma viagem registrada | A | P2 | Não executado |
| CT-VIA-05 | Uma viagem por vez (#171) | Já em viagem | 1. Tentar embarcar em outro ônibus | Recusa informando que já há viagem ativa; a viagem atual não muda | M | P2 | Não executado |
| CT-VIA-06 | Embarque pela rota (#190) | Rota calculada; ônibus da linha a até 100 m | 1. Escolher a opção<br>2. No trecho, tocar em "Peguei este ônibus" | Viagem começa e a parada de desembarque do trecho já é o destino | A | P2 | Não executado |
| CT-VIA-07 | Embarque com o ônibus chegando (#191) | Localização a até 400 m de uma parada da linha; ônibus a até 2 min dela | 1. Tocar em "Peguei este ônibus" | Embarque aceito (regra a validar em campo); se nada vale, recusa como no CT-VIA-04 | M | P3 | Não executado |
| CT-VIA-08 | Aviso de proximidade no app (#172 c1 a c4) | Em viagem com destino; ônibus se aproximando | 1. Manter o app aberto<br>2. Aguardar o aviso<br>3. Tocar em "Entendi" | Aviso fixo no topo uma única vez por parada e viagem; respeita as preferências; sem posição do ônibus não avisa | M | P2 | Não executado |

## 9. Segurança e acesso às rotas

| ID | Cenário (US) | Pré-condição | Passos | Resultado esperado | Sev. | Pri. | Estado |
|---|---|---|---|---|---|---|---|
| CT-SEG-01 | `X-User-Id` do cliente é descartado (#188) | Logado; ferramenta de requisição (DevTools ou `curl`) | 1. Enviar um `POST` autenticado a uma rota de colaboração ou de viagem com o cabeçalho `X-User-Id` de outro usuário | O recurso é criado para o usuário da sessão, nunca para o do cabeçalho | C | P1 | Não executado |
| CT-SEG-02 | Rotas públicas (#149) | Sem sessão | 1. Abrir `/docs` do Gateway<br>2. Chamar uma rota protegida sem cookie | `/docs` responde; a rota protegida responde 401 | A | P2 | Não executado |
| CT-SEG-03 | LGPD na viagem (#171 RN-06) | Viagem encerrada | 1. Conferir a resposta de `GET /viagens/ativa` e os dados exibidos | Não há trilha de posição do usuário; a posição serve só para validar o embarque | A | P3 | Não executado |
