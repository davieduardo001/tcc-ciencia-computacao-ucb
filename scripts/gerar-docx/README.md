# Gerar os documentos .docx da entrega

Encaixa um documento em Markdown (`docs/`) dentro de um template `.docx` ou `.dotx` da disciplina, mantendo capa, cabeçalho, rodapé, estilos e numeração de títulos do template. Remove os textos de orientação do template e preenche os campos (nome do projeto, grupo, data, versão e histórico de revisão).

## Requisitos

- Python 3 com `lxml`
- `pandoc`
- Os templates da disciplina (não estão no repositório)

## Uso

```bash
python3 scripts/gerar-docx/build.py <tipo> <template> <markdown> <saida.docx> [data] [versao]
```

Os dois últimos argumentos, opcionais, são a data da capa e do cabeçalho (padrão `28/out/26`; exemplo: `30/out/26`) e a versão da capa do documento de arquitetura (padrão `3.0`).

| Tipo | Template | Markdown |
|---|---|---|
| `visao` | `Template_Documento_Visao.dotx` | `docs/documento_visao.md` |
| `drs` | `Template_DRS.docx` | `docs/drs.md` |
| `arq` | `Template_DocumentoArquiteturaSoftware_v2.docx` | `docs/documento_arquitetura.md` |
| `relatorio` | `Template_Documento_Visao.dotx` | `docs/relatorio-construcao-e-testes.md` |

Exemplo:

```bash
python3 scripts/gerar-docx/build.py arq ~/Downloads/Template_DocumentoArquiteturaSoftware_v2.docx \
  docs/documento_arquitetura.md Documento_de_Arquitetura_Movecity_v3.docx
```

## O que a ferramenta faz

- Tira do Markdown o título duplicado e a numeração manual dos títulos (o template numera sozinho).
- Converte com o `pandoc` e traduz para os estilos do template (`Título 1`, `Título 2`...), com tabelas de largura total e bordas.
- Troca os campos do cabeçalho e da capa; no documento de arquitetura, preenche a tabela de histórico de revisão e cria o sumário.
- Copia as imagens (`![...](caminho)`) para dentro do `.docx`, relativas à pasta do Markdown.

## Depois de gerar

- Abra no Word e atualize os campos (Ctrl+A, F9) para o sumário do documento de arquitetura ganhar os números de página.
- O ano do rodapé é um campo do template (mostra o ano corrente).
- Diagramas PlantUML dos casos de uso (`docs/diagramas/sequencia/`) não são renderizados pela ferramenta.
