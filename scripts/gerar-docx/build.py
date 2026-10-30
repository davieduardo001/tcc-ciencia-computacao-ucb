#!/usr/bin/env python3
"""Encaixa um Markdown dentro de um template .docx/.dotx da disciplina.

Mantém capa, cabeçalho, rodapé, estilos e numeração de títulos do template;
remove os textos de orientação; preenche os campos (nome, grupo, data, versão).

Uso: build.py <tipo: visao|drs|arq|relatorio> <template> <markdown> <saida.docx> [data, ex.: 30/out/26]
"""
import sys, re, copy, zipfile, subprocess, tempfile, os, io
from lxml import etree

WNS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W = '{%s}' % WNS
XML = '{http://www.w3.org/XML/1998/namespace}'
NSMAP = {'w': WNS}


def q(t):
    return W + t


def el(tag, **attrs):
    e = etree.Element(q(tag))
    for k, v in attrs.items():
        e.set(q(k), str(v))
    return e


# ------------------------------------------------------------------ Markdown
def preprocess_md(md, tipo):
    """Limpa o Markdown para o encaixe. Retorna (md_limpo, linhas_do_historico)."""
    lines = md.split('\n')
    historico = []
    out = []
    in_code = False
    skip_section = False
    i = 0
    primeiro_h1_visto = False
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith('```'):
            in_code = not in_code
            if not skip_section:
                out.append(ln)
            i += 1
            continue
        if in_code:
            if not skip_section:
                out.append(ln)
            i += 1
            continue
        m = re.match(r'^(#{1,6})\s+(.*)$', ln)
        if m:
            nivel, titulo = len(m.group(1)), m.group(2).strip()
            if nivel == 1 and not primeiro_h1_visto:
                primeiro_h1_visto = True
                i += 1
                continue
            skip_section = False
            if tipo == 'arq' and nivel == 2 and re.match(r'(?i)^hist[óo]rico da revis', titulo):
                skip_section = True
                j = i + 1
                while j < len(lines) and not re.match(r'^## ', lines[j]):
                    row = lines[j].strip()
                    if row.startswith('|') and not re.match(r'^\|[\s:|-]+\|?$', row):
                        cells = [c.strip().replace('`', '') for c in row.strip('|').split('|')]
                        if cells and cells[0].lower() != 'data':
                            historico.append(cells)
                    j += 1
                i = j
                continue
            if tipo == 'arq' and nivel == 2 and re.match(r'(?i)^[íi]ndice anal', titulo):
                j = i + 1
                while j < len(lines) and not re.match(r'^## ', lines[j]):
                    j += 1
                i = j
                continue
            # tira a numeração manual: o template numera os títulos sozinho
            titulo = re.sub(r'^\d+(\.\d+)*\.?\s+', '', titulo)
            # sobe um nível: ## vira #, ### vira ##, ...
            novo = '#' * max(1, nivel - 1)
            out.append(f'{novo} {titulo}')
            i += 1
            continue
        if skip_section:
            i += 1
            continue
        s = ln.strip()
        if s.startswith('> 📎') or s.startswith('> Ver este arquivo'):
            i += 1
            continue
        if tipo == 'arq' and (s.startswith('**Grupo:**') or s.startswith('**Software:**') or s.startswith('**Versão:**')):
            i += 1
            continue
        if s == '---':
            i += 1
            continue
        out.append(ln)
        i += 1
    return '\n'.join(out), historico


def pandoc_docx(md_text, workdir):
    src = os.path.join(workdir, 'in.md')
    dst = os.path.join(workdir, 'pandoc.docx')
    with open(src, 'w', encoding='utf-8') as f:
        f.write(md_text)
    subprocess.run(['pandoc', '-f', 'gfm', '-t', 'docx', '--wrap=none', '--resource-path=' + MD_BASE, src, '-o', dst], check=True)
    z = zipfile.ZipFile(dst)
    rels = etree.fromstring(z.read('word/_rels/document.xml.rels'))
    imagens = {}
    for r in rels:
        if r.get('Type', '').endswith('/image'):
            imagens[r.get('Id')] = (r.get('Target'), z.read('word/' + r.get('Target')))
    return etree.fromstring(z.read('word/document.xml')), etree.fromstring(z.read('word/numbering.xml')), imagens


MD_BASE = '.'

# ------------------------------------------------- tradução para o template
def num_formats(numbering):
    abstract = {}
    for a in numbering.findall(q('abstractNum')):
        aid = a.get(q('abstractNumId'))
        for lvl in a.findall(q('lvl')):
            fmt = lvl.find(q('numFmt'))
            abstract[(aid, lvl.get(q('ilvl')))] = fmt.get(q('val')) if fmt is not None else 'bullet'
    nums = {}
    for n in numbering.findall(q('num')):
        aid = n.find(q('abstractNumId')).get(q('val'))
        nums[n.get(q('numId'))] = aid
    return abstract, nums


def pstyle(p):
    ps = p.find(q('pPr') + '/' + q('pStyle'))
    return ps.get(q('val')) if ps is not None else None


def set_pstyle(p, val):
    ppr = p.find(q('pPr'))
    if ppr is None:
        ppr = etree.Element(q('pPr'))
        p.insert(0, ppr)
    ps = ppr.find(q('pStyle'))
    if val is None:
        if ps is not None:
            ppr.remove(ps)
        return
    if ps is None:
        ps = etree.Element(q('pStyle'))
        ppr.insert(0, ps)
    ps.set(q('val'), val)


def ppr_of(p):
    ppr = p.find(q('pPr'))
    if ppr is None:
        ppr = etree.Element(q('pPr'))
        p.insert(0, ppr)
    return ppr


def ensure_rpr(r):
    rpr = r.find(q('rPr'))
    if rpr is None:
        rpr = etree.Element(q('rPr'))
        r.insert(0, rpr)
    return rpr


def mono(r, size=18):
    rpr = ensure_rpr(r)
    for old in rpr.findall(q('rStyle')):
        rpr.remove(old)
    f = el('rFonts', ascii='Consolas', hAnsi='Consolas', cs='Consolas')
    rpr.insert(0, f)
    if rpr.find(q('sz')) is None:
        rpr.append(el('sz', val=size))


def clean_inline(p):
    """Desfaz hyperlinks e marcadores, e traduz estilos de caractere do pandoc."""
    for hl in list(p.iter(q('hyperlink'))):
        parent = hl.getparent()
        idx = parent.index(hl)
        for child in list(hl):
            parent.insert(idx, child)
            idx += 1
        parent.remove(hl)
    for tag in ('bookmarkStart', 'bookmarkEnd'):
        for b in list(p.iter(q(tag))):
            b.getparent().remove(b)
    for r in p.iter(q('r')):
        rpr = r.find(q('rPr'))
        if rpr is None:
            continue
        rs = rpr.find(q('rStyle'))
        if rs is None:
            continue
        v = rs.get(q('val'))
        if v == 'VerbatimChar':
            mono(r)
        elif v in ('Hyperlink',):
            rpr.remove(rs)
        else:
            rpr.remove(rs)


def set_spacing(p, before=None, after=None):
    ppr = ppr_of(p)
    sp = ppr.find(q('spacing'))
    if sp is None:
        sp = etree.SubElement(ppr, q('spacing'))
    if before is not None:
        sp.set(q('before'), str(before))
    if after is not None:
        sp.set(q('after'), str(after))


def set_ind(p, left=None, hanging=None):
    ppr = ppr_of(p)
    ind = ppr.find(q('ind'))
    if ind is None:
        ind = etree.SubElement(ppr, q('ind'))
    if left is not None:
        ind.set(q('left'), str(left))
    if hanging is not None:
        ind.set(q('hanging'), str(hanging))


def reorder_ppr(ppr):
    """O Word exige a ordem dos filhos de pPr; reordena os que usamos."""
    ordem = ['pStyle', 'keepNext', 'keepLines', 'pageBreakBefore', 'numPr', 'pBdr', 'shd',
             'tabs', 'spacing', 'ind', 'jc', 'rPr']
    filhos = list(ppr)
    peso = {n: i for i, n in enumerate(ordem)}
    filhos.sort(key=lambda e: peso.get(etree.QName(e).localname, 99))
    for f in filhos:
        ppr.remove(f)
    for f in filhos:
        ppr.append(f)


def transform_table(tbl):
    tblpr = tbl.find(q('tblPr'))
    novo = etree.Element(q('tblPr'))
    novo.append(el('tblW', w=5000, type='pct'))
    b = etree.SubElement(novo, q('tblBorders'))
    for lado in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        b.append(el(lado, val='single', sz=4, space=0, color='808080'))
    novo.append(el('tblLayout', type='autofit'))
    cm = etree.SubElement(novo, q('tblCellMar'))
    cm.append(el('left', w=70, type='dxa'))
    cm.append(el('right', w=70, type='dxa'))
    if tblpr is not None:
        tbl.replace(tblpr, novo)
    else:
        tbl.insert(0, novo)
    for gc in tbl.iter(q('gridCol')):
        gc.set(q('w'), '0')
    rows = tbl.findall(q('tr'))
    for ri, tr in enumerate(rows):
        if ri == 0:
            trpr = tr.find(q('trPr'))
            if trpr is None:
                trpr = etree.Element(q('trPr'))
                tr.insert(0, trpr)
            trpr.append(etree.Element(q('tblHeader')))
        for tc in tr.findall(q('tc')):
            if ri == 0:
                tcpr = tc.find(q('tcPr'))
                if tcpr is None:
                    tcpr = etree.Element(q('tcPr'))
                    tc.insert(0, tcpr)
                tcpr.append(el('shd', val='clear', color='auto', fill='D9E2F3'))
            for p in tc.iter(q('p')):
                clean_inline(p)
                set_pstyle(p, None)
                set_spacing(p, before=20, after=20)
                for r in p.iter(q('r')):
                    rpr = ensure_rpr(r)
                    if rpr.find(q('sz')) is None:
                        rpr.append(el('sz', val=18))
                    if ri == 0 and rpr.find(q('b')) is None:
                        rpr.insert(0, etree.Element(q('b')))
                reorder_ppr(ppr_of(p))
    # pandoc põe um parágrafo vazio de legenda? (não em pipe tables)



EMU_LARG_MAX = 5943600   # 6,5 pol
EMU_ALT_MAX = 7315200    # 8 pol
WP = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'


def ajustar_figura(p):
    for ext in p.iter(WP + 'extent'):
        cx, cy = int(ext.get('cx')), int(ext.get('cy'))
        esc = min(EMU_LARG_MAX / cx, EMU_ALT_MAX / cy, 1.0)
        ncx, ncy = int(cx * esc), int(cy * esc)
        ext.set('cx', str(ncx)); ext.set('cy', str(ncy))
        for a in p.iter(A + 'ext'):
            a.set('cx', str(ncx)); a.set('cy', str(ncy))


def transform_body(root, numbering):
    abstract, nums = num_formats(numbering)
    body = root.find(q('body'))
    contadores = {}
    saida = []
    for ch in list(body):
        tag = etree.QName(ch).localname
        if tag == 'sectPr':
            continue
        if tag == 'tbl':
            transform_table(ch)
            saida.append(ch)
            # espaço depois da tabela
            sp = etree.Element(q('p'))
            set_spacing(sp, before=0, after=60)
            saida.append(sp)
            continue
        if tag != 'p':
            continue
        p = ch
        clean_inline(p)
        st = pstyle(p)
        numpr = p.find(q('pPr') + '/' + q('numPr'))
        if numpr is not None:
            ilvl = numpr.find(q('ilvl')).get(q('val'))
            numid = numpr.find(q('numId')).get(q('val'))
            fmt = abstract.get((nums.get(numid), ilvl), 'bullet')
            ppr = p.find(q('pPr'))
            ppr.remove(numpr)
            set_pstyle(p, None)
            n = int(ilvl)
            if fmt == 'bullet':
                marca = '•' if n == 0 else '–'
            else:
                chave = (numid, ilvl)
                contadores[chave] = contadores.get(chave, 0) + 1
                for k in list(contadores):
                    if k[0] == numid and int(k[1]) > n:
                        del contadores[k]
                marca = f'{contadores[chave]}.'
            set_ind(p, left=540 + n * 360, hanging=300)
            set_spacing(p, before=0, after=40)
            r1 = etree.Element(q('r'))
            t1 = etree.SubElement(r1, q('t'))
            t1.text = marca
            r2 = etree.Element(q('r'))
            etree.SubElement(r2, q('tab'))
            idx = 1 if p.find(q('pPr')) is not None else 0
            p.insert(idx, r1)
            p.insert(idx + 1, r2)
            reorder_ppr(ppr_of(p))
            saida.append(p)
            continue
        m = re.match(r'^Heading(\d)$', st or '')
        if m:
            nivel = min(int(m.group(1)), 6)
            set_pstyle(p, f'Ttulo{nivel}')
            reorder_ppr(ppr_of(p))
            saida.append(p)
            continue
        if st == 'SourceCode':
            set_pstyle(p, None)
            ppr = ppr_of(p)
            ppr.append(el('shd', val='clear', color='auto', fill='F2F2F2'))
            set_spacing(p, before=0, after=0)
            set_ind(p, left=240)
            for r in p.iter(q('r')):
                mono(r, 16)
            reorder_ppr(ppr)
            saida.append(p)
            continue
        if st == 'BlockText':
            set_pstyle(p, None)
            set_ind(p, left=360)
            set_spacing(p, before=60, after=120)
            for r in p.iter(q('r')):
                rpr = ensure_rpr(r)
                if rpr.find(q('i')) is None:
                    rpr.insert(0, etree.Element(q('i')))
            reorder_ppr(ppr_of(p))
            saida.append(p)
            continue
        if p.find('.//' + q('drawing')) is not None:
            set_pstyle(p, None)
            set_spacing(p, before=120, after=40)
            ppr = ppr_of(p)
            ppr.append(el('jc', val='center'))
            ppr.append(el('keepNext'))
            ajustar_figura(p)
            reorder_ppr(ppr)
            saida.append(p)
            continue
        if st == 'ImageCaption' or st == 'Caption':
            set_pstyle(p, None)
            set_spacing(p, before=0, after=160)
            ppr = ppr_of(p)
            ppr.append(el('jc', val='center'))
            for r in p.iter(q('r')):
                rpr = ensure_rpr(r)
                if rpr.find(q('i')) is None:
                    rpr.insert(0, etree.Element(q('i')))
            reorder_ppr(ppr)
            saida.append(p)
            continue
        # parágrafo comum
        set_pstyle(p, None)
        set_spacing(p, before=0, after=120)
        reorder_ppr(ppr_of(p))
        saida.append(p)
    return saida


# ----------------------------------------------------------- substituições
def replace_in_paragraph(p, old, new):
    ts = [t for t in p.iter(q('t'))]
    if not ts:
        return False
    total = ''.join(t.text or '' for t in ts)
    idx = total.find(old)
    if idx < 0:
        return False
    fim = idx + len(old)
    pos = 0
    primeiro = True
    for t in ts:
        txt = t.text or ''
        ini, f = pos, pos + len(txt)
        pos = f
        if f <= idx or ini >= fim:
            continue
        a = max(idx, ini) - ini
        b = min(fim, f) - ini
        if primeiro:
            t.text = txt[:a] + new + (txt[b:] if f >= fim else '')
            primeiro = False
        else:
            t.text = txt[b:] if f > fim else ''
        t.set(XML + 'space', 'preserve')
    return True


def replace_everywhere(root, pares):
    for p in root.iter(q('p')):
        for old, new in pares:
            while replace_in_paragraph(p, old, new) and old not in new:
                pass



RPR_ORDEM = ['rStyle','rFonts','b','bCs','i','iCs','caps','smallCaps','strike','dstrike','outline','shadow','emboss','imprint','noProof','snapToGrid','vanish','webHidden','color','spacing','w','kern','position','sz','szCs','highlight','u','effect','bdr','shd','fitText','vertAlign','rtl','cs','em','lang','eastAsianLayout','specVanish','oMath']
TCPR_ORDEM = ['cnfStyle','tcW','gridSpan','hMerge','vMerge','tcBorders','shd','noWrap','tcMar','textDirection','tcFitText','vAlign','hideMark']


def reordenar(root):
    for tag, ordem in (('rPr', RPR_ORDEM), ('tcPr', TCPR_ORDEM)):
        peso = {n: i for i, n in enumerate(ordem)}
        for e in root.iter(q(tag)):
            filhos = list(e)
            ordenados = sorted(filhos, key=lambda x: peso.get(etree.QName(x).localname, 99))
            if ordenados != filhos:
                for f in filhos:
                    e.remove(f)
                for f in ordenados:
                    e.append(f)
    for e in root.iter(q('pPr')):
        reorder_ppr(e)


# --------------------------------------------------------------- montagem
def texto(e):
    return ''.join(e.itertext())


def build_toc(entradas):
    """Sumário em campo TOC (o Word atualiza ao abrir) com entradas já preenchidas."""
    ps = []
    for i, (nivel, num, titulo) in enumerate(entradas):
        p = etree.Element(q('p'))
        ppr = etree.SubElement(p, q('pPr'))
        etree.SubElement(ppr, q('pStyle')).set(q('val'), 'Sumrio1' if nivel == 1 else 'Sumrio2')
        if i == 0:
            r = etree.SubElement(p, q('r'))
            fc = etree.SubElement(r, q('fldChar'))
            fc.set(q('fldCharType'), 'begin')
            fc.set(q('dirty'), 'true')
            r = etree.SubElement(p, q('r'))
            it = etree.SubElement(r, q('instrText'))
            it.set(XML + 'space', 'preserve')
            it.text = ' TOC \\h \\u \\z '
            r = etree.SubElement(p, q('r'))
            etree.SubElement(r, q('fldChar')).set(q('fldCharType'), 'separate')
        r = etree.SubElement(p, q('r'))
        t = etree.SubElement(r, q('t'))
        t.set(XML + 'space', 'preserve')
        t.text = f'{num}  {titulo}'
        if i == len(entradas) - 1:
            r = etree.SubElement(p, q('r'))
            etree.SubElement(r, q('fldChar')).set(q('fldCharType'), 'end')
        ps.append(p)
    return ps


def entradas_toc(saida):
    c1 = c2 = 0
    out = []
    for e in saida:
        if etree.QName(e).localname != 'p':
            continue
        st = pstyle(e)
        if st == 'Ttulo1':
            c1 += 1
            c2 = 0
            out.append((1, str(c1), texto(e)))
        elif st == 'Ttulo2':
            c2 += 1
            out.append((2, f'{c1}.{c2}', texto(e)))
    return out


def main(tipo, template, md_path, saida_path, hoje='28/out/26', versao='3.0'):
    md = open(md_path, encoding='utf-8').read()
    md_limpo, historico = preprocess_md(md, tipo)
    with tempfile.TemporaryDirectory() as tmp:
        root_p, numbering, imagens = pandoc_docx(md_limpo, tmp)
    conteudo = transform_body(root_p, numbering)

    zin = zipfile.ZipFile(template)
    doc = etree.fromstring(zin.read('word/document.xml'))
    body = doc.find(q('body'))
    sect = body.find(q('sectPr'))
    filhos = list(body)

    def idx_primeiro_ttulo1():
        for i, e in enumerate(filhos):
            if etree.QName(e).localname == 'p' and pstyle(e) == 'Ttulo1':
                return i
        raise SystemExit('Ttulo1 não encontrado no template')

    corte = idx_primeiro_ttulo1()
    for e in filhos[corte:]:
        if e is not sect:
            body.remove(e)

    pares = []
    if tipo == 'visao':
        pares = [('<Nome do Projeto>', 'Movecity'), ('Grupo: ', 'Grupo: Segurança no Transporte'),
                 ('<dd/mmm/aa>', hoje)]
    elif tipo == 'relatorio':
        pares = [('Documento de Visão', 'Relatório de Construção e Testes'), ('Visão', 'Construção e Testes'),
                 ('<Nome do Projeto>', 'Movecity'), ('Grupo: ', 'Grupo: Segurança no Transporte'), ('<dd/mmm/aa>', hoje)]
    elif tipo == 'drs':
        pares = [('<Project Name>', 'Movecity'), ('Grupo: ', 'Grupo: Segurança no Transporte'),
                 ('<dd/mmm/aa>', hoje)]
    elif tipo == 'arq':
        pares = [('<Nome do Software>', 'Movecity'), ('<Nome do grupo>', 'Grupo Segurança no Transporte (UCB)'),
                 ('Versão <1.0>', f'Versão {versao}')]
        # remove o aviso azul de orientação
        for p in list(body.iter(q('p'))):
            if '[Observação' in texto(p):
                p.getparent().remove(p)
        # preenche o histórico de revisão
        tbls = [e for e in body if etree.QName(e).localname == 'tbl']
        if tbls and historico:
            t = tbls[0]
            linhas = t.findall(q('tr'))
            modelo = copy.deepcopy(linhas[1])
            for l in linhas[1:]:
                t.remove(l)
            for reg in historico:
                nova = copy.deepcopy(modelo)
                tcs = nova.findall(q('tc'))
                for tc, val in zip(tcs, reg + [''] * 4):
                    ps = tc.findall(q('p'))
                    for extra in ps[1:]:
                        tc.remove(extra)
                    p0 = ps[0]
                    rs = p0.findall(q('r'))
                    for extra in rs[1:]:
                        p0.remove(extra)
                    if rs:
                        for tt in rs[0].findall(q('t')):
                            rs[0].remove(tt)
                        tnode = etree.SubElement(rs[0], q('t'))
                        tnode.text = val
                        tnode.set(XML + 'space', 'preserve')
                    else:
                        r = etree.SubElement(p0, q('r'))
                        tnode = etree.SubElement(r, q('t'))
                        tnode.text = val
                t.append(nova)
        # troca o sumário por um campo TOC atualizável
        for sdt in [e for e in body if etree.QName(e).localname == 'sdt']:
            idx = body.index(sdt)
            body.remove(sdt)
            for k, p in enumerate(build_toc(entradas_toc(conteudo))):
                body.insert(idx + k, p)
    replace_everywhere(doc, pares)

    for e in conteudo:
        sect.addprevious(e)
    reordenar(doc)

    # --- imagens: novas relações no pacote do template
    RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
    novas_rels = []
    novos_arquivos = {}
    id_para_novo = {}
    for k, (rid, (alvo, dados)) in enumerate(sorted(imagens.items()), 1):
        novo_id = f'rIdFig{k}'
        nome = f'media/fig_{k}{os.path.splitext(alvo)[1]}'
        id_para_novo[rid] = novo_id
        novas_rels.append((novo_id, nome))
        novos_arquivos['word/' + nome] = dados
    for blip in doc.iter(A + 'blip'):
        antigo = blip.get(RNS + 'embed')
        if antigo in id_para_novo:
            blip.set(RNS + 'embed', id_para_novo[antigo])
    # ids únicos para docPr
    for n, d in enumerate(doc.iter(WP + 'docPr'), 1000):
        d.set('id', str(n))

    # --- empacota
    zout = zipfile.ZipFile(saida_path, 'w', zipfile.ZIP_DEFLATED)
    for it in zin.infolist():
        data = zin.read(it.filename)
        if it.filename == 'word/document.xml':
            data = etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)
        elif re.match(r'word/(header|footer)\d*\.xml$', it.filename):
            r = etree.fromstring(data)
            replace_everywhere(r, pares)
            data = etree.tostring(r, xml_declaration=True, encoding='UTF-8', standalone=True)
        elif it.filename == 'docProps/core.xml':
            s = data.decode('utf-8')
            s = s.replace('&lt;Project Name&gt;', 'Movecity').replace('<dc:title>Vision</dc:title>', '<dc:title>Movecity</dc:title>')
            data = s.encode('utf-8')
        elif it.filename == 'word/_rels/document.xml.rels' and novas_rels:
            s = data.decode('utf-8')
            extra = ''.join(f'<Relationship Id="{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{t}"/>' for i, t in novas_rels)
            data = s.replace('</Relationships>', extra + '</Relationships>').encode('utf-8')
        elif it.filename == '[Content_Types].xml':
            s = data.decode('utf-8')
            if novas_rels and 'Extension="png"' not in s:
                s = s.replace('<Default ', '<Default Extension="png" ContentType="image/png"/><Default ', 1)
            s = s.replace('wordprocessingml.template.main+xml', 'wordprocessingml.document.main+xml')
            data = s.encode('utf-8')
        zout.writestr(it, data)
    for nome, dados in novos_arquivos.items():
        zout.writestr(nome, dados)
    zout.close()
    print('ok:', saida_path, '| elementos:', len(conteudo), '| histórico:', len(historico))


if __name__ == '__main__':
    tipo, template, md_path, saida = sys.argv[1:5]
    hoje = sys.argv[5] if len(sys.argv) > 5 else '28/out/26'
    versao = sys.argv[6] if len(sys.argv) > 6 else '3.0'
    MD_BASE = os.path.dirname(os.path.abspath(md_path))
    main(tipo, template, md_path, saida, hoje=hoje, versao=versao)
