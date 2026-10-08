"""Fusão de abrigos em paradas físicas e vínculo com a rota (US #173).

Lógica pura: sem banco, sem rede.
"""

from mobilidade.geometria import TrajetoMedido
from mobilidade.paradas_fisicas import (
    RAIO_FUSAO_M,
    PontoParada,
    _codigo_livre,
    codigo_da_parada,
    fundir_pontos,
    indexar_por_ponto,
    vincular,
)

# 0,00001° de latitude ≈ 1,1 m.
LAT, LNG = -15.8000, -47.9000


def _ponto(nome: str, dlat_m: float = 0.0, dlng_m: float = 0.0) -> PontoParada:
    return PontoParada(
        nome=nome, lat=LAT + dlat_m / 111_320, lng=LNG + dlng_m / 107_000
    )


def test_dois_abrigos_proximos_viram_uma_parada():
    paradas = fundir_pontos([_ponto("A"), _ponto("A bis", dlat_m=6)])

    assert len(paradas) == 1
    assert len(paradas[0].membros) == 2
    # Centróide, não um dos dois pontos.
    assert LAT < paradas[0].lat < LAT + 6 / 111_320


def test_abrigos_de_lados_opostos_da_rua_continuam_separados():
    # ~25 m: acima do raio de fusão. Ônibus de sentidos opostos.
    paradas = fundir_pontos([_ponto("Lado 1"), _ponto("Lado 2", dlat_m=25)])

    assert len(paradas) == 2


def test_fusao_encadeia_abrigos_em_fila():
    # A–B a 8 m e B–C a 8 m: A e C estão a 16 m, mas via B são a mesma parada.
    paradas = fundir_pontos(
        [_ponto("A"), _ponto("B", dlat_m=8), _ponto("C", dlat_m=16)]
    )

    assert len(paradas) == 1
    assert len(paradas[0].membros) == 3


def test_raio_de_fusao_e_de_10_metros():
    assert RAIO_FUSAO_M == 10.0


def test_resultado_nao_depende_da_ordem_de_entrada():
    entrada = [_ponto("A"), _ponto("B", dlat_m=5), _ponto("C", dlat_m=60), _ponto("D", dlat_m=65)]

    direto = fundir_pontos(entrada)
    invertido = fundir_pontos(list(reversed(entrada)))

    assert [(p.codigo, p.nome) for p in direto] == [(p.codigo, p.nome) for p in invertido]


def test_codigo_tem_formato_estavel():
    assert codigo_da_parada(LAT, LNG) == codigo_da_parada(LAT, LNG)
    assert codigo_da_parada(LAT, LNG).startswith("PR-")
    assert len(codigo_da_parada(LAT, LNG)) == len("PR-00000")


def test_colisao_de_codigo_e_desempatada():
    primeiro = codigo_da_parada(LAT, LNG)

    segundo = _codigo_livre(LAT, LNG, usados={primeiro})

    assert segundo != primeiro
    assert segundo == codigo_da_parada(LAT, LNG, tentativa=1)


def test_codigos_de_muitas_paradas_sao_todos_distintos():
    # ~1.500 paradas numa grade: num espaço de 100 mil códigos, colisão
    # por aniversário é esperada — a ingestão tem que desempatar.
    pontos = [
        PontoParada(nome="", lat=LAT + i * 0.0003, lng=LNG + j * 0.0003)
        for i in range(40)
        for j in range(40)
    ]

    paradas = fundir_pontos(pontos)

    assert len(paradas) == 1600
    assert len({p.codigo for p in paradas}) == 1600


def test_nome_vem_do_abrigo_mais_proximo_do_centroide_e_ignora_vazios():
    paradas = fundir_pontos([_ponto("", dlat_m=0), _ponto("Com nome", dlat_m=4)])

    assert paradas[0].nome == "Com nome"


# ---------------------------------------------------------------------------
# Vínculo parada ↔ rota
# ---------------------------------------------------------------------------

# Trajeto reto para leste: vértices a cada ~107 m.
TRAJETO = [(LAT, LNG + i * 0.001) for i in range(5)]


def _no_trajeto(indice: int, dlat_m: float = 0.0, nome: str = "") -> PontoParada:
    return PontoParada(nome=nome, lat=LAT + dlat_m / 111_320, lng=LNG + indice * 0.001)


def test_vinculo_sai_na_ordem_do_trajeto_nao_na_da_entrada():
    pontos = [_no_trajeto(3, nome="Terceira"), _no_trajeto(1, nome="Primeira")]
    mapa = indexar_por_ponto(fundir_pontos(pontos))

    vinculos = vincular(TrajetoMedido(TRAJETO), pontos, mapa)

    assert [v.parada.nome for v in vinculos] == ["Primeira", "Terceira"]
    assert [v.ordem for v in vinculos] == [0, 1]
    assert [v.indice_trajeto for v in vinculos] == [1, 3]


def test_vinculo_traz_distancia_acumulada_e_ao_trajeto():
    trajeto = TrajetoMedido(TRAJETO)
    pontos = [_no_trajeto(2, dlat_m=12)]
    mapa = indexar_por_ponto(fundir_pontos(pontos))

    (vinculo,) = vincular(trajeto, pontos, mapa)

    assert vinculo.distancia_acumulada_m == trajeto.acumulado[2]
    assert 11.0 <= vinculo.distancia_ao_trajeto_m <= 13.0


def test_dois_abrigos_da_mesma_parada_geram_um_vinculo_o_mais_proximo_do_trajeto():
    perto = _no_trajeto(2, dlat_m=1, nome="Perto")
    longe = _no_trajeto(2, dlat_m=8, nome="Longe")
    mapa = indexar_por_ponto(fundir_pontos([perto, longe]))

    vinculos = vincular(TrajetoMedido(TRAJETO), [longe, perto], mapa)

    assert len(vinculos) == 1
    assert vinculos[0].distancia_ao_trajeto_m < 3.0


def test_ponto_sem_parada_correspondente_e_ignorado():
    conhecido = _no_trajeto(1)
    mapa = indexar_por_ponto(fundir_pontos([conhecido]))

    vinculos = vincular(TrajetoMedido(TRAJETO), [conhecido, _no_trajeto(3)], mapa)

    assert len(vinculos) == 1
