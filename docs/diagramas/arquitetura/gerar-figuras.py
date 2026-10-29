#!/usr/bin/env python3
"""Gera as figuras UML da Arquitetura (Graphviz + SVG) a partir de fatos conferidos no código."""
import os, subprocess, sys, html
import cairosvg

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
FONT = 'Liberation Sans'


def dot(nome, src, dpi=170):
    p = os.path.join(OUT, nome + '.dot')
    open(p, 'w', encoding='utf-8').write(src)
    subprocess.run(['dot', '-Tpng', f'-Gdpi={dpi}', p, '-o', os.path.join(OUT, nome + '.png')], check=True)


# ------------------------------------------------------------------ Figura 1
def classe(nome, attrs, estereotipo=None, cor='#FFFFFF', tracejada=False):
    cab = f'&lt;&lt;{estereotipo}&gt;&gt;<br/>' if estereotipo else ''
    linhas = ''.join(f'<tr><td align="left" balign="left"><font point-size="9">{html.escape(a)}</font></td></tr>' for a in attrs)
    estilo = ' style="dashed"' if tracejada else ''
    return (f'{nome} [shape=plain label=<<table border="1" cellborder="0" cellspacing="0" cellpadding="3" bgcolor="{cor}"{estilo}>'
            f'<tr><td bgcolor="#D9E2F3"><b>{cab}{nome}</b></td></tr><hr/>{linhas}</table>>];\n')


def fig1():
    s = f'digraph G {{\n graph [rankdir=LR, nodesep=0.45, ranksep=1.1, fontname="{FONT}", pad=0.3];\n'
    s += f' node [fontname="{FONT}"]; edge [fontname="{FONT}", fontsize=9, arrowhead=none, labeldistance=2.2];\n'
    s += classe('Usuario', ['id', 'nome', 'email', 'senha_hash', 'provider (email | google)', 'google_id', 'lgpd_accepted_at', 'first_access', 'status'])
    s += classe('Sessao', ['id', 'access_token', 'refresh_token', 'expires_at'])
    s += classe('TokenResetSenha', ['id', 'token (hash SHA-256)', 'expira_em', 'usado'])
    s += classe('PreferenciaNotificacao', ['antecedencia_minutos', 'notificacoes_ativas', 'alerta_chegada', 'alerta_cancelamento'])
    s += classe('RotaFavorita', ['numero_linha', 'label', 'origem_lat / origem_lng', 'destino_lat / destino_lng'])
    s += classe('Ocorrencia', ['linha_numero', 'tipo', 'descricao', 'status (pendente | confirmada | expirada)', 'contador_confirmacoes', 'expira_em'])
    s += classe('ConfirmacaoOcorrencia', ['ocorrencia_id', 'usuario_id', 'criado_em'])
    s += classe('Viagem', ['numero_linha', 'sentido', 'veiculo_prefixo', 'parada_destino_codigo', 'embarcou_em', 'encerrada_em'])
    s += classe('AlertaProximidade', ['parada_destino_codigo', 'status', 'eta_minutos', 'disparado_em'])
    s += classe('InscricaoPush', ['endpoint', 'p256dh', 'auth', 'ultima_falha_em'])
    s += classe('Linha', ['numero', 'nome', 'sentido', 'trajeto (JSON)', 'paradas (JSON)'])
    s += classe('Rota', ['numero', 'sentido', 'trajeto (JSON)', 'horarios_por_dia', 'tempo_percurso_min'])
    s += classe('Parada', ['codigo (estável)', 'nome', 'lat / lng'])
    s += classe('PosicaoOnibus', ['prefixo', 'linha', 'sentido', 'lat / lng', 'atualizado_em'], estereotipo='não persistida', cor='#F2F2F2', tracejada=True)
    e = [
        ('Usuario', 'Sessao', '1', '0..*', None), ('Usuario', 'TokenResetSenha', '1', '0..*', None),
        ('Usuario', 'PreferenciaNotificacao', '1', '1', None), ('Usuario', 'RotaFavorita', '1', '0..20', None),
        ('Usuario', 'Ocorrencia', '1', '0..*', None), ('Ocorrencia', 'ConfirmacaoOcorrencia', '1', '0..*', None),
        ('Usuario', 'ConfirmacaoOcorrencia', '1', '0..*', None), ('Usuario', 'Viagem', '1', '0..1 ativa', None),
        ('Viagem', 'AlertaProximidade', '1', '0..*', None), ('Usuario', 'InscricaoPush', '1', '0..*', None),
        ('Linha', 'Rota', '1', '1..*', None), ('Rota', 'Parada', '*', '*', 'rota_parada'),
    ]
    for a, b, ta, tb, lab in e:
        l = f', label="{lab}"' if lab else ''
        s += f' {a} -> {b} [taillabel="{ta}", headlabel="{tb}"{l}];\n'
    # referências por número (sem chave estrangeira)
    for a, b in (('Ocorrencia', 'Linha'), ('Viagem', 'Linha'), ('RotaFavorita', 'Linha')):
        s += f' {a} -> {b} [style=dashed, label="por número", fontcolor="#555555"];\n'
    s += ' PosicaoOnibus -> Linha [style=dashed, label="feed SEMOB", fontcolor="#555555"];\n}\n'
    dot('fig1-classes', s)


# ------------------------------------------------------------------ Figura 2
def fig2():
    s = f'''digraph G {{
 graph [rankdir=TB, compound=true, nodesep=0.35, ranksep=0.6, fontname="{FONT}", pad=0.3];
 node [shape=box, style="rounded,filled", fillcolor="#FFFFFF", fontname="{FONT}", fontsize=10];
 edge [fontname="{FONT}", fontsize=9, arrowhead=vee];
 subgraph cluster_ap {{ label="Apresentação (Next.js, Vercel)"; style="filled"; fillcolor="#E8F1FB"; color="#6C8EBF";
   app [label="app/\\ntelas: mapa, rotas, ocorrências,\\nfavoritos, alertas, login, tutorial"];
   lib [label="lib/\\napi.ts (chamadas ao Gateway)\\nrenovação da sessão, navegacao.ts"];
   pwa [label="PWA\\nmanifest.ts, sw.js"]; }}
 subgraph cluster_gw {{ label="API Gateway (FastAPI)"; style="filled"; fillcolor="#FFF4D6"; color="#D6B656";
   gw [label="middleware.py · jwt_validator.py\\nproxy.py · routes.py · cookies.py"]; }}
 subgraph cluster_sv {{ label="Serviços de domínio (FastAPI, um app por serviço)"; style="filled"; fillcolor="#E6F4E6"; color="#82B366";
   auth [label="auth\\nsecurity.py · google_auth.py\\nemail_service.py · routes.py"];
   mob [label="mobilidade\\nposicao_service · viagem_service\\nchegada_service · rota_service\\npush · agendadores"];
   col [label="colaboracao\\nocorrências · favoritos\\npreferências · monitoring_worker"];
   shared [label="shared\\ndatabase.py · settings"]; }}
 subgraph cluster_da {{ label="Dados"; style="filled"; fillcolor="#F3E5F5"; color="#9673A6";
   db [label="PostgreSQL (Neon)\\n21 tabelas · 20 migrations", shape=cylinder]; }}
 subgraph cluster_ex {{ label="Serviços externos"; style="filled"; fillcolor="#F2F2F2"; color="#999999";
   semob [label="API SEMOB/GDF"]; osrm [label="OSRM · Nominatim"]; gg [label="Google OAuth · Gmail SMTP"]; wp [label="Web Push (VAPID)"]; carto [label="CARTO / OSM tiles"]; }}
 app -> lib; lib -> gw [label="HTTPS + cookies httpOnly"]; pwa -> gw [style=dashed];
 gw -> auth; gw -> mob; gw -> col;
 auth -> shared; mob -> shared; col -> shared; shared -> db;
 mob -> semob; mob -> osrm; mob -> wp; auth -> gg; app -> carto [style=dashed];
}}
'''
    dot('fig2-pacotes', s)


# ------------------------------------------------------------------ Figura 4
def fig4():
    s = f'''digraph G {{
 graph [rankdir=LR, nodesep=0.4, ranksep=0.9, fontname="{FONT}", pad=0.3];
 node [shape=box3d, style=filled, fillcolor="#FFFFFF", fontname="{FONT}", fontsize=10];
 edge [fontname="{FONT}", fontsize=9, arrowhead=vee];
 cli [label="«dispositivo»\\nNavegador / PWA\\n(Android, iOS, desktop)", fillcolor="#F2F2F2"];
 subgraph cluster_v {{ label="Vercel"; style=filled; fillcolor="#E8F1FB"; color="#6C8EBF";
   fe [label="«ambiente de execução»\\nFrontend Next.js\\nmovecity-frontend.vercel.app", fillcolor="#FFFFFF"]; }}
 subgraph cluster_f {{ label="Fly.io · região gru (São Paulo)"; style=filled; fillcolor="#E6F4E6"; color="#82B366";
   gw [label="movecity-gateway\\n(API Gateway)"]; au [label="movecity-auth"]; mo [label="movecity-mobilidade"]; co [label="movecity-colaboracao"]; }}
 subgraph cluster_n {{ label="Neon"; style=filled; fillcolor="#F3E5F5"; color="#9673A6";
   pg [label="PostgreSQL serverless\\n(um banco compartilhado)", shape=cylinder]; }}
 subgraph cluster_g {{ label="GitHub"; style=filled; fillcolor="#FFF4D6"; color="#D6B656";
   gha [label="GitHub Actions\\nci · deploy-fly · deploy-vercel\\ningestao-semob (mensal)"]; gp [label="GitHub Pages\\nprotótipo de alta fidelidade"]; }}
 ext [label="Serviços externos\\nSEMOB/GDF · OSRM · Nominatim\\nGoogle OAuth · Gmail · Web Push · CARTO", fillcolor="#F2F2F2"];
 cli -> fe [label="HTTPS"]; cli -> gw [label="HTTPS · cookies httpOnly"];
 gw -> au [label="HTTPS"]; gw -> mo; gw -> co;
 au -> pg [label="TCP/TLS"]; mo -> pg; co -> pg;
 mo -> ext; au -> ext [style=dashed];
 gha -> fe [label="deploy (push em homolog)", style=dashed]; gha -> gw [label="deploy (push em homolog e main)", style=dashed];
}}
'''
    dot('fig4-implantacao', s)


# ------------------------------------------------------------------ Figura 5 (MER)
TABELAS = {
    'usuarios': ['id PK', 'nome', 'email', 'senha_hash', 'avatar_url', 'provider', 'google_id', 'lgpd_accepted_at', 'status', 'tentativas_falhas', 'bloqueado_ate', 'account_linking_pending', 'first_access', 'created_at'],
    'sessoes': ['id PK', 'usuario_id FK', 'access_token', 'refresh_token', 'expires_at'],
    'tokens_reset_senha': ['id PK', 'usuario_id FK', 'token', 'usado', 'expira_em'],
    'preferencias_notificacao': ['id PK', 'usuario_id', 'antecedencia_minutos', 'notificacoes_ativas', 'alerta_chegada', 'alerta_cancelamento'],
    'rotas_favoritas': ['id PK', 'usuario_id', 'numero_linha', 'label', 'origem_lat', 'origem_lng', 'destino_lat', 'destino_lng'],
    'ocorrencia': ['id PK', 'usuario_id', 'linha_numero', 'tipo', 'descricao', 'local', 'lat', 'lng', 'status', 'contador_confirmacoes', 'expira_em'],
    'confirmacoes_ocorrencia': ['id PK', 'ocorrencia_id FK', 'usuario_id', 'UNIQUE (ocorrencia_id, usuario_id)'],
    'viagem': ['id PK', 'usuario_id', 'numero_linha', 'sentido', 'veiculo_prefixo', 'parada_destino_codigo', 'embarcou_em', 'encerrada_em', 'motivo_encerramento', 'origem_embarque'],
    'alertas_proximidade': ['id PK', 'usuario_id', 'viagem_id', 'linha_id', 'parada_destino_codigo', 'status', 'eta_minutos', 'disparado_em'],
    'inscricao_push': ['id PK', 'usuario_id', 'endpoint', 'p256dh', 'auth', 'ultima_falha_em'],
    'linha': ['id PK', 'numero', 'nome', 'sentido', 'paradas (JSON)', 'trajeto (JSON)', 'horarios_previstos'],
    'rota': ['id PK', 'numero', 'sentido', 'nome', 'trajeto (JSON)', 'paradas (JSON)', 'horarios_por_dia', 'tempo_percurso_min'],
    'rota_parada': ['id PK', 'numero', 'sentido', 'parada_id FK', 'ordem', 'indice_trajeto', 'distancia_acumulada_m', 'distancia_ao_trajeto_m'],
    'parada': ['id PK', 'codigo', 'nome', 'lat', 'lng'],
    'alertas': ['id PK', 'usuario_id', 'linha_id', 'status', 'atraso_inicio_minutos', 'cancelado_em'],
    'linhas_acompanhadas': ['id PK', 'usuario_id', 'linha_id', 'ativo'],
}
SERVICO = {'usuarios': 'auth', 'sessoes': 'auth', 'tokens_reset_senha': 'auth', 'preferencias_notificacao': 'colaboracao', 'rotas_favoritas': 'colaboracao',
           'ocorrencia': 'colaboracao', 'confirmacoes_ocorrencia': 'colaboracao', 'viagem': 'mobilidade', 'alertas_proximidade': 'mobilidade',
           'inscricao_push': 'mobilidade', 'linha': 'mobilidade', 'rota': 'mobilidade', 'rota_parada': 'mobilidade', 'parada': 'mobilidade',
           'alertas': 'mobilidade', 'linhas_acompanhadas': 'mobilidade'}
COR = {'auth': '#E8F1FB', 'colaboracao': '#E6F4E6', 'mobilidade': '#FFF4D6'}


def tabela(nome):
    linhas = ''
    for c in TABELAS[nome]:
        negrito = c.endswith(' PK') or c.endswith(' FK')
        txt = html.escape(c)
        linhas += f'<tr><td align="left" balign="left"><font point-size="9">{"<b>" + txt + "</b>" if negrito else txt}</font></td></tr>'
    return (f'{nome} [shape=plain label=<<table border="1" cellborder="0" cellspacing="0" cellpadding="2" bgcolor="white">'
            f'<tr><td bgcolor="{COR[SERVICO[nome]]}"><b>{nome}</b></td></tr><hr/>{linhas}</table>>];\n')


def fig5():
    s = f'digraph G {{\n graph [rankdir=LR, nodesep=0.35, ranksep=1.2, fontname="{FONT}", pad=0.3];\n'
    s += f' node [fontname="{FONT}"]; edge [fontname="{FONT}", fontsize=9, arrowhead=crow, arrowtail=tee, dir=both];\n'
    for t in TABELAS:
        s += ' ' + tabela(t)
    fk = [('usuarios', 'sessoes'), ('usuarios', 'tokens_reset_senha'), ('ocorrencia', 'confirmacoes_ocorrencia'), ('parada', 'rota_parada')]
    for a, b in fk:
        s += f' {a} -> {b};\n'
    # chave criada só na migration, sem declarar no ORM (entre serviços)
    for b in ('preferencias_notificacao', 'rotas_favoritas'):
        s += f' usuarios -> {b} [style=dashed, label="FK só na migration"];\n'
    # referências lógicas, sem chave estrangeira
    for a, b, lab in [('usuarios', 'ocorrencia', ''), ('usuarios', 'viagem', ''), ('viagem', 'alertas_proximidade', ''),
                      ('usuarios', 'inscricao_push', ''), ('usuarios', 'confirmacoes_ocorrencia', '')]:
        s += f' {a} -> {b} [style=dotted, color="#777777"];\n'
    s += ' linha -> rota [style=dotted, color="#777777", label="por número"];\n rota -> rota_parada [style=dotted, color="#777777", label="por número e sentido"];\n'
    s += ' ocorrencia -> linha [style=dotted, color="#777777", label="linha_numero"];\n'
    s += ' subgraph cluster_leg { label="Legenda"; style=dashed; fontsize=9; leg [shape=plain label=<<table border="0" cellspacing="0"><tr><td align="left"><font point-size="9">linha contínua: chave estrangeira no banco</font></td></tr><tr><td align="left"><font point-size="9">tracejada: chave criada só na migration</font></td></tr><tr><td align="left"><font point-size="9">pontilhada: referência lógica, sem chave estrangeira</font></td></tr><tr><td align="left"><font point-size="9">cor do título: serviço dono (azul auth, verde colaboração, amarelo mobilidade)</font></td></tr></table>>]; }\n}\n'
    dot('fig5-mer', s)


# ------------------------------------------------------------------ Figura 3 (sequência UC16)
def fig3():
    parts = ['Passageiro', 'Tela do mapa\n(Next.js)', 'API Gateway', 'Serviço de\nMobilidade', 'Serviço de\nAutenticação', 'Feed SEMOB']
    larg, x0, dx, topo = 1060, 90, 165, 70
    xs = [x0 + i * dx for i in range(len(parts))]
    msgs = []  # (de, para, texto, tracejada)
    y = topo + 70
    svg = []
    cmds = [
        ('msg', 0, 1, '1: selecionarLinha(numero)', False),
        ('msg', 1, 2, '2: GET /api/mobilidade/linhas/{n}/posicoes (cookie)', False),
        ('self', 2, None, '3: valida o JWT localmente', False),
        ('alt', 'token válido'),
        ('msg', 2, 3, '4: encaminha com a identidade do usuário', False),
        ('self', 3, None, '5: lê o feed em cache (20 s)', False),
        ('msg', 3, 5, '6: GET posições (se o cache venceu)', False),
        ('msg', 5, 3, '7: feed de posições', True),
        ('msg', 3, 2, '8: posições da linha', True),
        ('msg', 2, 1, '9: 200 + posições', True),
        ('self', 1, None, '10: desenha os ônibus; repete a cada 20 s', False),
        ('else', 'token expirado ou ausente'),
        ('msg', 2, 1, '4: 401 Não autenticado', True),
        ('msg', 1, 2, '5: POST /api/auth/refresh (cookie de refresh)', False),
        ('msg', 2, 4, '6: renova a sessão', False),
        ('msg', 4, 2, '7: novos tokens', True),
        ('msg', 2, 1, '8: 200 + novos cookies', True),
        ('msg', 1, 2, '9: refaz a chamada do passo 2', False),
        ('end',),
    ]
    alt_ini = None
    altura = 30
    for c in cmds:
        if c[0] in ('msg', 'self'):
            altura += 34
        else:
            altura += 30
    H = topo + 70 + altura + 40
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{larg}" height="{H}" viewBox="0 0 {larg} {H}" font-family="Liberation Sans, Arial, sans-serif">')
    svg.append(f'<rect width="{larg}" height="{H}" fill="white"/>')
    svg.append(f'<text x="{larg/2}" y="28" text-anchor="middle" font-size="15" font-weight="bold">UC16 — Rastrear posição do ônibus em tempo real (US #16)</text>')
    for x, p in zip(xs, parts):
        linhas = p.split('\n')
        svg.append(f'<rect x="{x-62}" y="{topo-34}" width="124" height="{20+16*len(linhas)}" rx="4" fill="#D9E2F3" stroke="#6C8EBF"/>')
        for k, t in enumerate(linhas):
            svg.append(f'<text x="{x}" y="{topo-14+16*k}" text-anchor="middle" font-size="12">{html.escape(t)}</text>')
        svg.append(f'<line x1="{x}" y1="{topo+8+16*(len(linhas)-1)}" x2="{x}" y2="{H-20}" stroke="#999" stroke-dasharray="5,4"/>')
    y = topo + 60
    alt_y = None
    marcador = '<defs><marker id="a" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="#333"/></marker></defs>'
    svg.append(marcador)
    for c in cmds:
        if c[0] == 'msg':
            _, a, b, txt, tr = c
            xa, xb = xs[a], xs[b]
            y += 34
            dash = ' stroke-dasharray="6,4"' if tr else ''
            svg.append(f'<line x1="{xa}" y1="{y}" x2="{xb + (-4 if xb > xa else 4)}" y2="{y}" stroke="#333"{dash} marker-end="url(#a)"/>')
            tx = (xa + xb) / 2
            svg.append(f'<text x="{tx}" y="{y-6}" text-anchor="middle" font-size="11">{html.escape(txt)}</text>')
        elif c[0] == 'self':
            _, a, _, txt, _ = c
            xa = xs[a]
            y += 34
            svg.append(f'<path d="M{xa},{y-8} h38 v16 h-38" fill="none" stroke="#333" marker-end="url(#a)"/>')
            svg.append(f'<text x="{xa+46}" y="{y+4}" font-size="11">{html.escape(txt)}</text>')
        elif c[0] == 'alt':
            y += 30
            alt_y = y - 16
            svg.append(f'<text x="{x0-70}" y="{y-2}" font-size="11" font-weight="bold">alt</text>')
            svg.append(f'<text x="{x0-30}" y="{y-2}" font-size="11">[{html.escape(c[1])}]</text>')
        elif c[0] == 'else':
            y += 30
            svg.append(f'<line x1="{x0-80}" y1="{y-14}" x2="{xs[-1]+90}" y2="{y-14}" stroke="#6C8EBF" stroke-dasharray="4,3"/>')
            svg.append(f'<text x="{x0-30}" y="{y+2}" font-size="11">[{html.escape(c[1])}]</text>')
        elif c[0] == 'end':
            y += 30
            svg.append(f'<rect x="{x0-80}" y="{alt_y}" width="{xs[-1]+170-x0}" height="{y-alt_y-10}" fill="none" stroke="#6C8EBF"/>')
    svg.append('</svg>')
    s = '\n'.join(svg)
    open(os.path.join(OUT, 'fig3-sequencia-uc16.svg'), 'w', encoding='utf-8').write(s)
    cairosvg.svg2png(bytestring=s.encode('utf-8'), write_to=os.path.join(OUT, 'fig3-sequencia-uc16.png'), scale=1.6)


for f in (fig1, fig2, fig3, fig4, fig5):
    f()
print(sorted(os.listdir(OUT)))
