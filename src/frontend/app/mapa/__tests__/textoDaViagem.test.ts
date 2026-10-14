import type { ParadaDaViagem, ViagemAtiva } from "@/lib/api";
import { textoDaViagem } from "../textoDaViagem";

const parada = (codigo: string, nome: string): ParadaDaViagem => ({ codigo, nome, lat: 0, lng: 0 });

function viagem(sobre: Partial<ViagemAtiva> = {}): ViagemAtiva {
  return {
    id: "v-1",
    numeroLinha: "0.110",
    sentido: "IDA",
    veiculoPrefixo: "440001",
    paradaDestinoCodigo: null,
    embarcouEm: "2026-10-14T15:00:00Z",
    sinal: "ao_vivo",
    veiculo: null,
    destino: null,
    proximaParada: parada("PR-B", "W3 Sul 502"),
    paradasRestantes: [],
    ...sobre,
  };
}

describe("textoDaViagem", () => {
  it("sem sinal do ônibus, não estima nada e avisa", () => {
    const t = textoDaViagem(viagem({ sinal: "sem_sinal" }));
    expect(t).toEqual({ principal: "Sem sinal do ônibus no momento", tom: "alerta" });
  });

  it("sem sinal vale mais que qualquer parada que ainda esteja no estado", () => {
    // Dado velho de uma consulta anterior não pode virar "Próxima: X".
    const t = textoDaViagem(viagem({ sinal: "sem_sinal", proximaParada: parada("PR-B", "Velha") }));
    expect(t.principal).not.toContain("Velha");
  });

  it("destino ultrapassado avisa, em tom de alerta", () => {
    const t = textoDaViagem(
      viagem({ destino: { ...parada("PR-A", "Parada A"), ultrapassado: true } })
    );
    expect(t).toEqual({ principal: "O ônibus já passou de Parada A", tom: "alerta" });
  });

  it("sem trajeto conhecido, só diz que acompanha — não inventa parada", () => {
    const t = textoDaViagem(viagem({ proximaParada: null }));
    expect(t).toEqual({ principal: "Acompanhando o ônibus", tom: "normal" });
  });

  it("sem destino, mostra só a próxima parada", () => {
    const t = textoDaViagem(viagem());
    expect(t).toEqual({ principal: "Próxima parada: W3 Sul 502", tom: "normal" });
  });

  it("a parada do usuário é a próxima", () => {
    const destino = { ...parada("PR-B", "W3 Sul 502"), ultrapassado: false };
    const t = textoDaViagem(viagem({ destino, paradasRestantes: [parada("PR-B", "W3 Sul 502")] }));
    expect(t.principal).toBe("Sua parada, W3 Sul 502, é a próxima");
  });

  it("com várias paradas até o destino, diz quantas faltam (plural)", () => {
    const destino = { ...parada("PR-C", "Terminal"), ultrapassado: false };
    const t = textoDaViagem(
      viagem({
        destino,
        paradasRestantes: [parada("PR-B", "W3 Sul 502"), parada("PR-X", "Meio"), parada("PR-C", "Terminal")],
      })
    );
    expect(t.principal).toBe("Próxima: W3 Sul 502 · faltam 3 paradas até Terminal");
  });

  it("com destino mas sem a lista (ex.: trajeto indisponível), cai na próxima parada", () => {
    const destino = { ...parada("PR-C", "Terminal"), ultrapassado: false };
    const t = textoDaViagem(viagem({ destino, paradasRestantes: [] }));
    expect(t.principal).toBe("Próxima parada: W3 Sul 502");
  });
});
