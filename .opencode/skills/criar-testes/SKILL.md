---
name: criar-testes
description: Guia para criar testes unitários com pytest (backend) e testes de componentes (frontend) no projeto Movecity.
---

# Criar Testes Unitários

Esta skill orienta a criação de testes unitários para o projeto Movecity.

## Pré-requisitos

- Banco local rodando (usar `@dev-environment` ou `docker compose up -d`)
- Migrations aplicadas (`alembic upgrade head`)

## Backend — pytest

### Estrutura

```
src/backend/[servico]/
├── tests/
│   ├── __init__.py
│   ├── test_[modelo].py
│   └── test_[servico].py
└── ...
```

### Convenções

- Arquivos: `test_[nome].py`
- Funções: `test_[acao]_[cenario]`
- Fixtures: `@pytest.fixture` para dados de teste

### Exemplo

```python
# tests/test_usuario.py
import pytest
from src.backend.auth.models import Usuario

def test_criar_usuario_sucesso():
    usuario = Usuario(email="teste@email.com", nome="Teste")
    assert usuario.email == "teste@email.com"

def test_criar_usuario_email_invalido():
    with pytest.raises(ValueError):
        Usuario(email="invalido", nome="Teste")
```

### Rodar testes

```bash
cd src/backend/[servico]
pytest -v
```

## Frontend — Jest/React Testing Library

### Estrutura

```
src/frontend/components/[componente]/
├── __tests__/
│   └── [componente].test.tsx
└── ...
```

### Convenções

- Arquivos: `[componente].test.tsx`
- Funções: `it('deve [acao] quando [cenario]', () => {})`

### Exemplo

```tsx
import { render, screen } from '@testing-library/react';
import { Botao } from '../Botao';

it('deve renderizar o texto do botão', () => {
  render(<Botao>Enviar</Botao>);
  expect(screen.getByText('Enviar')).toBeInTheDocument();
});
```

### Rodar testes

```bash
cd src/frontend
npm test
```

## Regras

| Regra | Detalhe |
|-------|---------|
| Mínimo | 1 teste passando por serviço/componente |
| Cobertura | Testar cenário principal + alternativos |
| Isolamento | Testes não devem depender de outros |
| Nomes | Descritivos: `test_[acao]_[cenario]` |

## Vincular à Issue

Testes não têm vínculo automático com a issue no GitHub — o vínculo é manual, via comentário.

Depois de criar e rodar os testes localmente com sucesso, comentar na issue da US:

> "Testes adicionados: [lista dos arquivos/serviços]. Rodando localmente: [N] passed."

Isso é além (não substitui) do comentário de PR aberto descrito em `desenvolver-us-backend` (passo 9) e do comentário de review descrito em `review-pr` (passo 4).
