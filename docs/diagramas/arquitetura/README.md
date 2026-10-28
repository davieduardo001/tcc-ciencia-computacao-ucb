# Figuras UML da Arquitetura

Figuras do `docs/documento_arquitetura.md`, geradas a partir de fatos conferidos no código de `homolog` (tabelas e colunas dos modelos SQLAlchemy, serviços e workflows).

| Figura | Arquivo | Fonte editável |
|---|---|---|
| 1. Diagrama de classes do domínio | `fig1-classes.png` | `fig1-classes.dot` |
| 2. Diagrama de pacotes da arquitetura lógica | `fig2-pacotes.png` | `fig2-pacotes.dot` |
| 3. Diagrama de sequência do UC16 | `fig3-sequencia-uc16.png` | `fig3-sequencia-uc16.svg` |
| 4. Diagrama de implantação | `fig4-implantacao.png` | `fig4-implantacao.dot` |
| 5. Modelo entidade-relacionamento (MER) | `fig5-mer.png` | `fig5-mer.dot` |

Para regerar (precisa de Graphviz e do pacote Python `cairosvg`):

```bash
python3 docs/diagramas/arquitetura/gerar-figuras.py docs/diagramas/arquitetura
```

Os diagramas de sequência dos demais casos de uso continuam em `docs/diagramas/sequencia/` (PlantUML).
