# Dados estáticos do mobilidade

## `nomes_linhas.json`

Mapa `numero da linha -> denominação oficial`, extraído dos relatórios de
linhas do SEMOB:

```
https://sismob.semob.df.gov.br/flq/linhas/{codigo_operadora}
```

Os códigos das 5 operadoras de ônibus do DF são `PR` (Viação Piracicabana,
Bacia 01), `PI` (Viação Pioneira, Bacia 02), `HP` (Urbi Mobilidade Urbana,
Bacia 03 — o grupo se chama HP Transportes), `VM` (Auto Viação Marechal,
Bacia 04) e `SJ` (Expresso São José, Bacia 05).

O relatório vem em **PDF**, por isso a extração é feita uma vez, offline, e o
resultado fica versionado aqui — evita depender de `pdftotext` (ou de uma
biblioteca de PDF) dentro do container em produção. Denominação de linha é
dado estável, muda raramente.

Cobertura atual: **823 das 923 linhas** que aparecem em `/espaciais`. As 100
restantes não constam nos relatórios de "SERVIÇO: SB" e recebem um nome
genérico (`Linha <numero>`) na ingestão.

### Como regerar

```bash
cd /tmp && mkdir -p pdfs
for c in PR PI VM SJ HP; do
  curl -s "https://sismob.semob.df.gov.br/flq/linhas/$c" -o "pdfs/$c.pdf"
  pdftotext -layout "pdfs/$c.pdf" "pdfs/$c.txt"
done
python3 - <<'PY'
import re, json, glob
pat = re.compile(r'^\s*([0-9]{1,3}\.[0-9]{1,3})\s\s+(.+?)\s\s+([A-Z]{2}\s-\s.+?)\s\s+\d')
nomes = {}
for f in sorted(glob.glob('/tmp/pdfs/*.txt')):
    for ln in open(f, encoding='utf-8'):
        m = pat.match(ln)
        if m:
            nomes[m.group(1)] = ' '.join(m.group(2).split())
json.dump(dict(sorted(nomes.items())), open('nomes_linhas.json', 'w'),
          ensure_ascii=False, indent=0, sort_keys=True)
print(len(nomes), 'linhas')
PY
```
