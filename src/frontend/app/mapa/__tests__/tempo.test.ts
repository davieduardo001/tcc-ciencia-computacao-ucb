import { formatarMinutos, minutosInteiros } from "../tempo";

describe("formatarMinutos", () => {
  it("arredonda para minutos inteiros — o dado não tem precisão de décimo de minuto", () => {
    expect(formatarMinutos(4.3)).toBe("4 min");
    expect(formatarMinutos(4.6)).toBe("5 min");
    expect(formatarMinutos(17.5)).toBe("18 min");
  });

  it("menos de meio minuto não vira '0 min', que parece erro", () => {
    expect(formatarMinutos(0)).toBe("menos de 1 min");
    expect(formatarMinutos(0.4)).toBe("menos de 1 min");
  });

  it("meio minuto já conta como 1", () => {
    expect(formatarMinutos(0.5)).toBe("1 min");
  });

  it("minutos grandes seguem em minutos", () => {
    expect(formatarMinutos(90)).toBe("90 min");
  });
});

describe("minutosInteiros (a pílula já leva a unidade no rótulo)", () => {
  it("devolve só o número", () => {
    expect(minutosInteiros(4.3)).toBe("4");
    expect(minutosInteiros(12)).toBe("12");
  });

  it("menos de 1 minuto vira '<1'", () => {
    expect(minutosInteiros(0.2)).toBe("<1");
    expect(minutosInteiros(0)).toBe("<1");
  });
});
