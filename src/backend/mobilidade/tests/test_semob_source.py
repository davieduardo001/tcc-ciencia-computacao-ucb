"""Testes das transformações dos dados do SEMOB (sem tocar a rede).

Os payloads reais somam ~37 MB; aqui usamos amostras mínimas com a mesma
forma do que o SEMOB devolve (conferida contra a API real).
"""

from mobilidade.semob_source import (
    coordenadas_para_trajeto,
    escolher_sentido_principal,
    horarios_por_linha,
    indexar_pontos,
    nome_da_parada,
    paradas_ao_longo_do_trajeto,
    rotulo_do_sentido,
)


def test_coordenadas_invertem_de_lng_lat_para_lat_lng():
    # O GeoJSON do SEMOB vem [lng, lat]; o Leaflet e o resto do projeto
    # usam (lat, lng). Trocar isso põe o trajeto na China.
    geo = {"type": "LineString", "coordinates": [[-47.8826, -15.7944], [-47.88, -15.79]]}

    assert coordenadas_para_trajeto(geo) == [(-15.7944, -47.8826), (-15.79, -47.88)]


def test_coordenadas_sem_geometria_devolve_lista_vazia():
    assert coordenadas_para_trajeto(None) == []
    assert coordenadas_para_trajeto({}) == []


def test_nome_da_parada_tira_cep_e_cidade():
    assert nome_da_parada("W3 Sul, SQS 315, Brasília, CEP: 70384-000") == "W3 Sul, SQS 315"
    assert nome_da_parada("Terminal Ceilândia, Brasília") == "Terminal Ceilândia"
    assert nome_da_parada("Eixo Monumental") == "Eixo Monumental"


def test_horarios_agrupa_por_linha_e_sentido_sem_repetir():
    brutos = [
        {
            "numero": "0.110",
            "sentido": "C",
            "horarios": [
                {"horario": "05:55"},
                {"horario": "06:15"},
                {"horario": "05:55"},  # mesmo horário em outro dia
            ],
        },
        {"numero": "0.006", "sentido": "I", "horarios": [{"horario": "07:00"}]},
    ]

    indice = horarios_por_linha(brutos)

    assert indice[("0.110", "CIRCULAR")] == ["05:55", "06:15"]
    assert indice[("0.006", "IDA")] == ["07:00"]


def test_horarios_ignora_sentido_desconhecido():
    assert horarios_por_linha([{"numero": "9.999", "sentido": "X", "horarios": []}]) == {}


def test_sentido_principal_prefere_circular_depois_ida():
    assert escolher_sentido_principal(["VOLTA", "CIRCULAR", "IDA"]) == "CIRCULAR"
    assert escolher_sentido_principal(["VOLTA", "IDA"]) == "IDA"
    assert escolher_sentido_principal(["VOLTA"]) == "VOLTA"


def test_rotulo_do_sentido():
    from mobilidade.semob_source import ParadaProxima

    paradas = [
        ParadaProxima(nome="Terminal Ceilândia", lat=-15.81, lng=-48.10),
        ParadaProxima(nome="Rodoviária", lat=-15.79, lng=-47.88),
    ]

    assert rotulo_do_sentido("CIRCULAR", paradas) == "Circular"
    assert rotulo_do_sentido("IDA", paradas) == "Terminal Ceilândia → Rodoviária"
    # Sem paradas suficientes pra montar origem→destino, não inventa.
    assert rotulo_do_sentido("IDA", []) == "Ida"


# ---------------------------------------------------------------------------
# Junção espacial trajeto <-> abrigos de parada
# ---------------------------------------------------------------------------


def _ponto(lat, lng, endereco="Parada X, Brasília, CEP: 70000-000"):
    return {"latitude": lat, "longitude": lng, "endereco": endereco}


def test_paradas_encontra_abrigo_proximo_e_ignora_distante():
    perto = _ponto(-15.7944, -47.8826, "Rodoviária, Brasília, CEP: 70070-000")
    longe = _ponto(-15.9000, -48.2000, "Outro Lugar, Brasília, CEP: 72000-000")
    indice = indexar_pontos([perto, longe])

    paradas = paradas_ao_longo_do_trajeto([(-15.7944, -47.8826)], indice)

    assert [p.nome for p in paradas] == ["Rodoviária"]


def test_paradas_saem_na_ordem_em_que_a_linha_passa():
    primeira = _ponto(-15.8000, -47.9000, "Primeira, Brasília, CEP: 70000-000")
    segunda = _ponto(-15.7944, -47.8826, "Segunda, Brasília, CEP: 70000-000")
    indice = indexar_pontos([segunda, primeira])  # ordem de entrada invertida

    trajeto = [(-15.8000, -47.9000), (-15.7970, -47.8900), (-15.7944, -47.8826)]
    paradas = paradas_ao_longo_do_trajeto(trajeto, indice)

    assert [p.nome for p in paradas] == ["Primeira", "Segunda"]


def test_paradas_nao_repete_a_mesma_parada_quando_a_linha_passa_duas_vezes():
    # Circulares passam pelo mesmo ponto na ida e na volta.
    ponto = _ponto(-15.7944, -47.8826, "Rodoviária, Brasília, CEP: 70070-000")
    indice = indexar_pontos([ponto])

    trajeto = [(-15.7944, -47.8826), (-15.80, -47.90), (-15.7944, -47.8826)]
    paradas = paradas_ao_longo_do_trajeto(trajeto, indice)

    assert len(paradas) == 1


def test_paradas_respeita_o_raio_configurado():
    # ~100 m ao norte do traçado: fora do raio padrão (40 m).
    quase = _ponto(-15.7935, -47.8826, "Quase, Brasília, CEP: 70070-000")
    indice = indexar_pontos([quase])

    assert paradas_ao_longo_do_trajeto([(-15.7944, -47.8826)], indice) == []
    assert len(paradas_ao_longo_do_trajeto([(-15.7944, -47.8826)], indice, raio_metros=150)) == 1


def test_ponto_sem_coordenada_nao_quebra_o_indice():
    indice = indexar_pontos([{"endereco": "Sem coordenada"}, _ponto(-15.79, -47.88)])

    assert len(paradas_ao_longo_do_trajeto([(-15.79, -47.88)], indice)) == 1


# ---------------------------------------------------------------------------
# Denominação oficial (o SEMOB publica em CAIXA ALTA)
# ---------------------------------------------------------------------------


def test_nome_da_linha_mantem_siglas_e_abaixa_preposicoes():
    from mobilidade.semob_source import formatar_nome_linha

    assert (
        formatar_nome_linha("CIRCULAR - RODOVIÁRIA DO PLANO PILOTO / UNB")
        == "Circular - Rodoviária do Plano Piloto / UNB"
    )
    assert (
        formatar_nome_linha("CRUZEIRO / SUDOESTE / W3 SUL / OCTOGONAL")
        == "Cruzeiro / Sudoeste / W3 Sul / Octogonal"
    )


def test_nome_da_linha_preserva_separador_interno_e_numeros():
    from mobilidade.semob_source import formatar_nome_linha

    # "N-S" não pode virar "N-s"; "DF-128" não pode virar "Df-128".
    assert formatar_nome_linha("EIXO N-S") == "Eixo N-S"
    assert formatar_nome_linha("PLANALTINA (DF-128)") == "Planaltina (DF-128)"
    assert formatar_nome_linha("GUARÁ I E II") == "Guará I e II"


def test_nome_da_linha_nao_abaixa_preposicao_no_comeco():
    from mobilidade.semob_source import formatar_nome_linha

    assert formatar_nome_linha("DO SOL / TAGUATINGA").startswith("Do Sol")
