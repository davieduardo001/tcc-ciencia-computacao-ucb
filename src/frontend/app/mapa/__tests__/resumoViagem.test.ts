import { OpcaoViagem, PernaViagem } from "@/lib/api";
import { corDaLinha, CORES_TRAJETO } from "../corDaLinha";
import { destaquesDasOpcoes, duracaoDaOpcao, minutosAPe, passosDaOpcao } from "../resumoViagem";

function perna(numero: string, embarqueM = 0, desembarqueM = 0): PernaViagem {
  return {
    numero,
    sentido: "IDA",
    nome: `Linha ${numero}`,
    embarque: { lat: 0, lng: 0, parada_nome: "A", caminhada_metros: embarqueM },
    desembarque: { lat: 0, lng: 0, parada_nome: "B", caminhada_metros: desembarqueM },
    distancia_km: 5,
    paradas_no_trecho: 4,
    trajeto: [],
  };
}

function opcao(parcial: Partial<OpcaoViagem> = {}): OpcaoViagem {
  return {
    pernas: [perna("0.110")],
    baldeacoes: 0,
    distancia_km: 5,
    caminhada_metros: 300,
    duracao_estimada_min: 40,
    ...parcial,
  };
}

describe("corDaLinha", () => {
  it("é determinística: o mesmo número sempre dá a mesma cor", () => {
    expect(corDaLinha("875A")).toBe(corDaLinha("875A"));
    expect(corDaLinha("0.110")).toBe(corDaLinha("0.110"));
  });

  it("sempre devolve uma cor da paleta do mapa", () => {
    ["0.110", "875A", "106.2", "0.900", "B27"].forEach((n) => {
      expect(CORES_TRAJETO).toContain(corDaLinha(n));
    });
  });

  it("usa mais de uma cor (linhas diferentes não ficam todas iguais)", () => {
    const cores = new Set(["0.110", "875A", "106.2", "0.900", "B27", "812", "0.313"].map(corDaLinha));
    expect(cores.size).toBeGreaterThan(1);
  });
});

describe("minutosAPe", () => {
  it("usa 5 km/h, a mesma conta do backend", () => {
    expect(minutosAPe(400)).toBe(5); // 400 m ÷ 83,3 m/min
    expect(minutosAPe(1000)).toBe(12);
  });

  it("zero metros = zero minutos; qualquer caminhada conta pelo menos 1", () => {
    expect(minutosAPe(0)).toBe(0);
    expect(minutosAPe(-5)).toBe(0);
    expect(minutosAPe(10)).toBe(1);
  });
});

describe("duracaoDaOpcao", () => {
  it("sem ETA real, usa a estimativa por velocidade média", () => {
    expect(duracaoDaOpcao(opcao({ duracao_estimada_min: 52 }))).toEqual({ minutos: 52, aoVivo: false });
  });

  it("com ETA real (tempo_real ou parcial), usa a duração ao vivo", () => {
    const real = opcao({ duracao_estimada_min: 46, duracao_real_min: 41, tipo_estimativa: "tempo_real" });
    expect(duracaoDaOpcao(real)).toEqual({ minutos: 41, aoVivo: true });
    expect(duracaoDaOpcao({ ...real, tipo_estimativa: "parcial" }).aoVivo).toBe(true);
  });

  it("tipo 'teorica' ou duração real ausente não conta como ao vivo", () => {
    expect(
      duracaoDaOpcao(opcao({ duracao_real_min: 30, tipo_estimativa: "teorica" })).aoVivo
    ).toBe(false);
    expect(
      duracaoDaOpcao(opcao({ duracao_real_min: null, tipo_estimativa: "tempo_real" })).aoVivo
    ).toBe(false);
  });

  it("arredonda minutos fracionados", () => {
    expect(duracaoDaOpcao(opcao({ duracao_estimada_min: 40.6 })).minutos).toBe(41);
  });
});

describe("destaquesDasOpcoes", () => {
  it("opção única não recebe destaque nenhum", () => {
    expect(destaquesDasOpcoes([opcao()])).toEqual([[]]);
  });

  it("marca a mais rápida, a de menos baldeações e a de menos caminhada", () => {
    const rapida = opcao({ duracao_estimada_min: 30, baldeacoes: 1, caminhada_metros: 600 });
    const direta = opcao({ duracao_estimada_min: 45, baldeacoes: 0, caminhada_metros: 600 });
    const perto = opcao({ duracao_estimada_min: 50, baldeacoes: 1, caminhada_metros: 100 });

    expect(destaquesDasOpcoes([rapida, direta, perto])).toEqual([
      ["mais_rapida"],
      ["menos_baldeacoes"],
      ["menos_caminhada"],
    ]);
  });

  it("uma opção pode acumular vários destaques", () => {
    const melhor = opcao({ duracao_estimada_min: 30, baldeacoes: 0, caminhada_metros: 100 });
    const pior = opcao({ duracao_estimada_min: 50, baldeacoes: 1, caminhada_metros: 700 });

    expect(destaquesDasOpcoes([melhor, pior])).toEqual([
      ["mais_rapida", "menos_baldeacoes", "menos_caminhada"],
      [],
    ]);
  });

  it("empate no critério não destaca ninguém", () => {
    const a = opcao({ duracao_estimada_min: 40, baldeacoes: 0 });
    const b = opcao({ duracao_estimada_min: 40, baldeacoes: 0 });

    expect(destaquesDasOpcoes([a, b])).toEqual([[], []]);
  });

  it("diferença de poucos metros a pé é empate (compara em minutos)", () => {
    const a = opcao({ caminhada_metros: 400, duracao_estimada_min: 30 });
    const b = opcao({ caminhada_metros: 410, duracao_estimada_min: 45 });

    const [destA, destB] = destaquesDasOpcoes([a, b]);
    expect(destA).not.toContain("menos_caminhada");
    expect(destB).not.toContain("menos_caminhada");
  });

  it("compara a duração exibida (ao vivo), não só a estimada", () => {
    const aoVivo = opcao({ duracao_estimada_min: 60, duracao_real_min: 25, tipo_estimativa: "tempo_real" });
    const teorica = opcao({ duracao_estimada_min: 40 });

    expect(destaquesDasOpcoes([aoVivo, teorica])[0]).toContain("mais_rapida");
  });
});

describe("passosDaOpcao", () => {
  it("viagem direta: caminhar → embarcar → viajar → descer → caminhar", () => {
    const passos = passosDaOpcao(opcao({ pernas: [perna("0.110", 120, 280)] }));

    expect(passos.map((p) => p.tipo)).toEqual(["caminhar", "embarcar", "viajar", "descer", "caminhar"]);
    expect(passos[0]).toMatchObject({ tipo: "caminhar", metros: 120 });
    expect(passos[4]).toMatchObject({ tipo: "caminhar", metros: 280 });
  });

  it("sem caminhada nas pontas, não cria passo de caminhar", () => {
    const passos = passosDaOpcao(opcao({ pernas: [perna("0.110", 0, 0)] }));

    expect(passos.map((p) => p.tipo)).toEqual(["embarcar", "viajar", "descer"]);
  });

  it("com baldeação: troca explícita entre as pernas, somando a caminhada das duas pontas", () => {
    const passos = passosDaOpcao(
      opcao({
        pernas: [perna("0.110", 60, 90), perna("106.2", 150, 40)],
        baldeacoes: 1,
      })
    );

    expect(passos.map((p) => p.tipo)).toEqual([
      "caminhar",
      "embarcar",
      "viajar",
      "descer",
      "baldear",
      "embarcar",
      "viajar",
      "descer",
      "caminhar",
    ]);

    const baldear = passos.find((p) => p.tipo === "baldear");
    // desembarque da 1ª (90) + embarque da 2ª (150): a mesma soma do backend
    expect(baldear).toMatchObject({ metros: 240, para: "106.2" });
  });

  it("numera os embarques como os marcadores do mapa (1, 2, …)", () => {
    const passos = passosDaOpcao(
      opcao({ pernas: [perna("A"), perna("B"), perna("C")], baldeacoes: 2 })
    );

    const numeros = passos.flatMap((p) => (p.tipo === "embarcar" ? [p.numeroDoPasso] : []));
    expect(numeros).toEqual([1, 2, 3]);
  });

  it("baldeação sem caminhada ainda aparece (a troca existe mesmo com 0 m)", () => {
    const passos = passosDaOpcao(opcao({ pernas: [perna("A"), perna("B")], baldeacoes: 1 }));

    expect(passos.find((p) => p.tipo === "baldear")).toMatchObject({ metros: 0, para: "B" });
  });

  it("as chaves dos passos são únicas (usadas como key no React)", () => {
    const passos = passosDaOpcao(
      opcao({ pernas: [perna("A", 10, 10), perna("A", 10, 10)], baldeacoes: 1 })
    );

    const chaves = passos.map((p) => p.chave);
    expect(new Set(chaves).size).toBe(chaves.length);
  });
});
