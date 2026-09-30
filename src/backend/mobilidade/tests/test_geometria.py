"""Geometria de trajeto compartilhada (US #19/#159)."""

from mobilidade.geometria import TrajetoMedido, mais_proximo

# Trecho reto leste-oeste, ~111 m entre pontos (0.001° de longitude).
LAT = -15.80
PASSO = 0.001
TRAJETO = [(LAT, -48.10 + PASSO * i) for i in range(10)]


def test_mais_proximo_encontra_o_indice_certo():
    indice, distancia = mais_proximo(TRAJETO, TRAJETO[4])
    assert indice == 4
    assert distancia < 1.0


def test_mais_proximo_respeita_o_inicio():
    # Pedindo a partir do índice 5, não pode "voltar" para o 2.
    indice, _ = mais_proximo(TRAJETO, TRAJETO[2], inicio=5)
    assert indice >= 5


def test_trajeto_medido_metros_entre_bate_com_a_soma_manual():
    from mobilidade.geometria import distancia_metros

    medido = TrajetoMedido(TRAJETO)
    # Soma segmento a segmento entre os índices 2 e 6, pro mesmo par de
    # pontos que TrajetoMedido usa internamente.
    manual = sum(distancia_metros(*TRAJETO[i], *TRAJETO[i + 1]) for i in range(2, 6))
    assert abs(medido.metros_entre(2, 6) - manual) < 1e-6


def test_trajeto_medido_metros_entre_e_negativo_quando_alvo_vem_antes():
    medido = TrajetoMedido(TRAJETO)
    assert medido.metros_entre(6, 2) < 0


def test_indice_mais_proximo_respeita_tolerancia():
    medido = TrajetoMedido(TRAJETO)
    ponto_no_trajeto = TRAJETO[3]
    ponto_longe = (LAT + 1.0, -48.10)

    assert medido.indice_mais_proximo(ponto_no_trajeto, tolerancia_m=50.0) == 3
    assert medido.indice_mais_proximo(ponto_longe, tolerancia_m=50.0) is None
