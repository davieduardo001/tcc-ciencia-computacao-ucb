from mobilidade.providers.polyline_decoder import decodificar_polyline


def test_decodifica_exemplo_oficial_do_google():
    # Exemplo da própria documentação do Google:
    # https://developers.google.com/maps/documentation/utilities/polylinealgorithm
    pontos = decodificar_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@")

    assert pontos == [
        (38.5, -120.2),
        (40.7, -120.95),
        (43.252, -126.453),
    ]


def test_string_vazia_retorna_lista_vazia():
    assert decodificar_polyline("") == []
