# US02. Visualizar Ônibus em Tempo Real (Exemplo Movecity)

**Descrição:**
- **Como** passageiro aguardando em uma parada de ônibus em Ceilândia
- **Quero** visualizar a localização exata do ônibus da linha selecionada no mapa em tempo real
- **Para** reduzir a ansiedade da espera e decidir se busco um meio de transporte alternativo caso haja atraso

---

## 📋 Critérios de Aceite (Cenários BDD)

### Cenário 1: Veículo com sinal de GPS ativo
- **Dado** que eu selecionei a linha "0.330" e estou na tela de visualização do mapa
- **Quando** o veículo estiver transmitindo dados de geolocalização
- **Então** o sistema deve exibir um ícone representativo do ônibus movendo-se no mapa
- **E** a posição deve ser atualizada em intervalos de, no máximo, 10 segundos.

### Cenário 2: Veículo sem sinal de GPS (Ônibus Fantasma)
- **Dado** que eu selecionei uma linha cujo veículo não está transmitindo sinal de GPS
- **Quando** eu acessar o mapa da linha
- **Então** o sistema deve exibir uma mensagem: "Localização em tempo real indisponível para este veículo"
- **E** mostrar apenas o horário teórico da tabela oficial.

### Cenário 3: Falha de conectividade do usuário
- **Dado** que minha conexão de internet (4G/Wi-Fi) caiu enquanto eu observava o mapa
- **Quando** o sistema tentar buscar a próxima atualização de posição
- **Então** deve exibir um alerta discreto de "Problemas de conexão. Tentando reconectar..." sem travar a interface.

---

## 🛠️ Detalhes Técnicos & Metadados
- **Prioridade:** Alta (Core Business)
- **Esforço Estimado:** G (Grande - envolve integração com API de terceiros e WebSockets/Polling)
- **Status:** Backlog
- **Requisitos Não Funcionais Relacionados:** RNF-Desempenho (3s de carga), RNF-Disponibilidade.
