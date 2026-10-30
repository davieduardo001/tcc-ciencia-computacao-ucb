import {
  alternarTodasNotificacoes,
  atualizarTipoNotificacao,
  buscarPreferencias,
  PreferenciasError,
  salvarAntecedencia,
} from "../api";

const ID = "11111111-1111-1111-1111-111111111111";

const CORPO = {
  id: "p1",
  usuario_id: ID,
  antecedencia_minutos: 30,
  notificacoes_ativas: true,
  alerta_chegada: true,
  alerta_cancelamento: false,
};

function resposta(status: number, corpo: unknown = {}) {
  return { ok: status >= 200 && status < 300, status, json: async () => corpo };
}

function mockFetch(...respostas: unknown[]) {
  const fn = jest.fn();
  respostas.forEach((r) => fn.mockResolvedValueOnce(r));
  global.fetch = fn as unknown as typeof fetch;
  return fn;
}

describe("buscarPreferencias", () => {
  it("faz GET na rota do usuário e converte os campos", async () => {
    const fetchMock = mockFetch(resposta(200, CORPO));

    expect(await buscarPreferencias(ID)).toEqual({
      antecedenciaMinutos: 30,
      notificacoesAtivas: true,
      alertaChegada: true,
      alertaCancelamento: false,
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(new RegExp(`/api/colaboracao/preferencias/${ID}$`));
    expect(init.method).toBe("GET");
    expect(init.credentials).toBe("include");
    expect(init.body).toBeUndefined();
  });

  it("403 vira PreferenciasError com status", async () => {
    mockFetch(resposta(403));
    await expect(buscarPreferencias(ID)).rejects.toMatchObject({ status: 403 });
  });

  it("5xx vira PreferenciasError com mensagem amigável", async () => {
    mockFetch(resposta(500));
    const erro = await buscarPreferencias(ID).catch((e) => e);
    expect(erro).toBeInstanceOf(PreferenciasError);
    expect(erro.message).toMatch(/carregar suas preferências/);
  });

  it("falha de rede vira PreferenciasError", async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError("offline")) as unknown as typeof fetch;
    await expect(buscarPreferencias(ID)).rejects.toThrow(/Sem conexão/);
  });
});

describe("salvarAntecedencia", () => {
  it("faz PUT em /antecedencia com o corpo esperado", async () => {
    const fetchMock = mockFetch(resposta(200, { ...CORPO, antecedencia_minutos: 60 }));

    const salvo = await salvarAntecedencia(ID, 60);

    expect(salvo.antecedenciaMinutos).toBe(60);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(new RegExp(`/preferencias/${ID}/antecedencia$`));
    expect(init.method).toBe("PUT");
    expect(JSON.parse(init.body)).toEqual({ antecedencia_minutos: 60 });
  });

  it("400 do servidor vira erro de salvar", async () => {
    mockFetch(resposta(400));
    await expect(salvarAntecedencia(ID, 7)).rejects.toThrow(/salvar a antecedência/);
  });
});

describe("atualizarTipoNotificacao", () => {
  it("faz PUT em /tipo/cancelamento com ativo=false", async () => {
    const fetchMock = mockFetch(resposta(200, CORPO));

    const salvo = await atualizarTipoNotificacao(ID, "cancelamento", false);

    expect(salvo.alertaCancelamento).toBe(false);
    expect(salvo.alertaChegada).toBe(true);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(new RegExp(`/preferencias/${ID}/tipo/cancelamento$`));
    expect(JSON.parse(init.body)).toEqual({ ativo: false });
  });
});

describe("alternarTodasNotificacoes", () => {
  it("faz PUT em /desativar-todas com ativas", async () => {
    const fetchMock = mockFetch(resposta(200, { ...CORPO, notificacoes_ativas: false }));

    const salvo = await alternarTodasNotificacoes(ID, false);

    expect(salvo.notificacoesAtivas).toBe(false);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(new RegExp(`/preferencias/${ID}/desativar-todas$`));
    expect(JSON.parse(init.body)).toEqual({ ativas: false });
  });
});
