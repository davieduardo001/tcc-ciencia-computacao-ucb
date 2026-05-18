# US01. Realizar Autenticação de Usuário

**Descrição:**
- **Como** passageiro ou colaborador do Movecity
- **Quero** realizar login ou criar uma conta utilizando E-mail/Senha ou Provedores Sociais (Google)
- **Para** ter acesso a funcionalidades personalizadas, como salvar rotas favoritas e reportar ocorrências colaborativas

---

## 📋 Critérios de Aceite (Cenários BDD)

### Cenário 1: Cadastro com E-mail e Senha (Sucesso)
- **Dado** que eu estou na tela de "Criar Conta"
- **Quando** eu preencho um e-mail válido, uma senha forte e clico em "Cadastrar"
- **Então** o sistema deve criar meu perfil, enviar um e-mail de confirmação e me redirecionar para a Dashboard.

### Cenário 2: Login via Google (Sucesso)
- **Dado** que eu possuo uma conta Google ativa
- **Quando** eu clico no botão "Entrar com Google" e autorizo o acesso
- **Então** o sistema deve realizar meu login automaticamente, criando um perfil caso seja meu primeiro acesso.

### Cenário 3: Tentativa de login com credenciais inválidas
- **Dado** que eu insiro um e-mail não cadastrado ou senha incorreta
- **Quando** eu clico em "Entrar"
- **Então** o sistema deve exibir a mensagem: "Usuário ou senha inválidos" e manter os dados no campo de e-mail para correção.

---

## 🛠️ Detalhes Técnicos & Metadados
- **Prioridade:** Alta
- **Esforço Estimado:** M (Médio - utilizando Firebase Auth ou Supabase Auth)
- **Status:** Backlog
- **Requisitos Não Funcionais Relacionados:** RNF-Segurança (LGPD), RNF-Acessibilidade.
