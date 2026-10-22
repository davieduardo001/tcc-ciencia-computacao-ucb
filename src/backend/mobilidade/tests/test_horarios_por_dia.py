"""Horários por dia da semana do /horario do SEMOB (US #173)."""

from mobilidade.semob_source import horarios_do_dia, horarios_por_dia

SEG_A_SEX = "SSSSSNN"
SABADO = "NNNNNSN"
DOMINGO = "NNNNNNS"


def _registro(sentido="I", tempo=90, **horarios):
    return {
        "numero": "0.100",
        "sentido": sentido,
        "tempo_percurso": tempo,
        "horarios": [
            {"horario": h, "dias_semana": dias} for dias, hs in horarios.items() for h in hs
        ],
    }


def test_separa_horarios_por_dia_da_semana():
    resultado = horarios_por_dia(
        [
            _registro(
                **{SEG_A_SEX: ["05:45", "06:45"], SABADO: ["07:00"], DOMINGO: ["08:00"]}
            )
        ]
    )

    por_dia = resultado[("0.100", "IDA")].por_dia
    assert por_dia["0"] == ["05:45", "06:45"]  # segunda
    assert por_dia["4"] == ["05:45", "06:45"]  # sexta
    assert por_dia["5"] == ["07:00"]  # sábado
    assert por_dia["6"] == ["08:00"]  # domingo


def test_horario_de_domingo_nao_aparece_na_segunda():
    resultado = horarios_por_dia([_registro(**{DOMINGO: ["08:00"]})])

    assert horarios_do_dia(resultado[("0.100", "IDA")].por_dia, 0) == []


def test_registro_sem_dias_semana_vale_para_todos_os_dias():
    bruto = [
        {"numero": "0.100", "sentido": "I", "horarios": [{"horario": "06:00"}]},
        {
            "numero": "0.101",
            "sentido": "I",
            "horarios": [{"horario": "07:00", "dias_semana": "formato-invalido"}],
        },
    ]

    resultado = horarios_por_dia(bruto)

    for chave, esperado in (("0.100", "06:00"), ("0.101", "07:00")):
        por_dia = resultado[(chave, "IDA")].por_dia
        assert all(por_dia[str(d)] == [esperado] for d in range(7))


def test_registros_do_mesmo_sentido_somam_sem_repetir():
    resultado = horarios_por_dia(
        [
            _registro(**{SEG_A_SEX: ["06:00", "07:00"]}),
            _registro(**{SEG_A_SEX: ["07:00", "08:00"]}),
        ]
    )

    assert resultado[("0.100", "IDA")].por_dia["1"] == ["06:00", "07:00", "08:00"]


def test_tempo_de_percurso_e_guardado_por_sentido():
    resultado = horarios_por_dia(
        [
            _registro(sentido="I", tempo=90, **{SEG_A_SEX: ["06:00"]}),
            _registro(sentido="V", tempo=75, **{SEG_A_SEX: ["06:30"]}),
        ]
    )

    assert resultado[("0.100", "IDA")].tempo_percurso_min == 90
    assert resultado[("0.100", "VOLTA")].tempo_percurso_min == 75


def test_tempo_de_percurso_ausente_ou_invalido_vira_none():
    resultado = horarios_por_dia(
        [_registro(tempo=None, **{SEG_A_SEX: ["06:00"]}), _registro(sentido="V", tempo=0, **{SEG_A_SEX: ["06:00"]})]
    )

    assert resultado[("0.100", "IDA")].tempo_percurso_min is None
    assert resultado[("0.100", "VOLTA")].tempo_percurso_min is None


def test_sentido_desconhecido_e_ignorado():
    assert horarios_por_dia([_registro(sentido="X", **{SEG_A_SEX: ["06:00"]})]) == {}


def test_horarios_do_dia_de_rota_sem_dado_devolve_vazio():
    assert horarios_do_dia(None, 2) == []
