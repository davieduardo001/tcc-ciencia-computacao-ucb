from unittest.mock import MagicMock, patch

from mobilidade.workers.monitoramento import criar_worker


def _ids_dos_jobs(scheduler_mock):
    return [
        chamada.kwargs["id"]
        for chamada in scheduler_mock.add_job.call_args_list
    ]


def _criar_com_patch(servico_proximidade=None, servico_cancelamento=None):
    with patch("mobilidade.workers.monitoramento.BackgroundScheduler") as classe:
        scheduler = criar_worker(
            MagicMock(),
            intervalo_minutos=5,
            servico_proximidade=servico_proximidade,
            servico_cancelamento=servico_cancelamento,
        )
    return scheduler, classe.return_value


def test_criar_worker_sem_proximidade_so_monitora_atrasos():
    _, scheduler = _criar_com_patch()

    assert _ids_dos_jobs(scheduler) == ["monitoramento-atrasos"]


def test_criar_worker_com_proximidade_cria_os_dois_jobs():
    _, scheduler = _criar_com_patch(servico_proximidade=MagicMock())

    assert _ids_dos_jobs(scheduler) == [
        "monitoramento-atrasos",
        "monitoramento-proximidade",
    ]


def test_job_de_proximidade_chama_o_servico_com_sessao_propria():
    servico_proximidade = MagicMock()
    _, scheduler = _criar_com_patch(servico_proximidade=servico_proximidade)
    job = scheduler.add_job.call_args_list[1].kwargs["func"]

    sessao = MagicMock()
    with patch(
        "mobilidade.workers.monitoramento.SessionLocal", return_value=sessao
    ):
        job()

    servico_proximidade.verificar_proximidades.assert_called_once_with(sessao)
    sessao.close.assert_called_once()


def test_job_de_proximidade_nao_propaga_excecao():
    servico_proximidade = MagicMock()
    servico_proximidade.verificar_proximidades.side_effect = RuntimeError("boom")
    _, scheduler = _criar_com_patch(servico_proximidade=servico_proximidade)
    job = scheduler.add_job.call_args_list[1].kwargs["func"]

    sessao = MagicMock()
    with patch(
        "mobilidade.workers.monitoramento.SessionLocal", return_value=sessao
    ):
        job()  # não pode lançar: quem chama é o executor do APScheduler

    sessao.rollback.assert_called_once()
    sessao.close.assert_called_once()


def test_jobs_usam_o_mesmo_intervalo():
    _, scheduler = _criar_com_patch(servico_proximidade=MagicMock())

    intervalos = [
        chamada.kwargs["minutes"] for chamada in scheduler.add_job.call_args_list
    ]
    assert intervalos == [5, 5]


# ---------------------------------------------------------------------------
# US #28 — job de cancelamento de viagem
# ---------------------------------------------------------------------------


def test_criar_worker_com_cancelamento_cria_os_tres_jobs():
    _, scheduler = _criar_com_patch(
        servico_proximidade=MagicMock(),
        servico_cancelamento=MagicMock(),
    )

    assert _ids_dos_jobs(scheduler) == [
        "monitoramento-atrasos",
        "monitoramento-proximidade",
        "monitoramento-cancelamento",
    ]


def test_criar_worker_so_com_cancelamento_cria_os_dois_jobs():
    _, scheduler = _criar_com_patch(servico_cancelamento=MagicMock())

    assert _ids_dos_jobs(scheduler) == [
        "monitoramento-atrasos",
        "monitoramento-cancelamento",
    ]


def test_job_de_cancelamento_chama_o_servico_com_sessao_propria():
    servico_cancelamento = MagicMock()
    _, scheduler = _criar_com_patch(
        servico_proximidade=MagicMock(),
        servico_cancelamento=servico_cancelamento,
    )
    job = scheduler.add_job.call_args_list[2].kwargs["func"]

    sessao = MagicMock()
    with patch(
        "mobilidade.workers.monitoramento.SessionLocal", return_value=sessao
    ):
        job()

    servico_cancelamento.verificar_ciclo.assert_called_once_with(sessao)
    sessao.close.assert_called_once()


def test_job_de_cancelamento_nao_propaga_excecao():
    servico_cancelamento = MagicMock()
    servico_cancelamento.verificar_ciclo.side_effect = RuntimeError("boom")
    _, scheduler = _criar_com_patch(servico_cancelamento=servico_cancelamento)
    job = scheduler.add_job.call_args_list[1].kwargs["func"]

    sessao = MagicMock()
    with patch(
        "mobilidade.workers.monitoramento.SessionLocal", return_value=sessao
    ):
        job()  # não pode lançar: quem chama é o executor do APScheduler

    sessao.rollback.assert_called_once()
    sessao.close.assert_called_once()


def test_job_de_cancelamento_usa_o_mesmo_intervalo_do_de_atrasos():
    _, scheduler = _criar_com_patch(servico_cancelamento=MagicMock())

    chamadas = {
        chamada.kwargs["id"]: chamada.kwargs["minutes"]
        for chamada in scheduler.add_job.call_args_list
    }
    assert chamadas["monitoramento-cancelamento"] == chamadas["monitoramento-atrasos"]
