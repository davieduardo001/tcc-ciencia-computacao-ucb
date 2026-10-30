/**
 * Repassa origem/destino de "Rotas Salvas" (/favoritos) para o mapa sem
 * colocar coordenadas na URL (LGPD, RN-06: a posição do usuário não pode
 * ficar no histórico do navegador, em links copiados ou em logs).
 *
 * O valor vive em sessionStorage (só a aba atual) e é apagado na primeira
 * leitura.
 */
const CHAVE = "movecity:rota-pendente";

export interface PontoRotaPendente {
  nome: string;
  lat: number;
  lng: number;
}

export interface RotaPendente {
  origem: PontoRotaPendente;
  destino: PontoRotaPendente;
}

export function guardarRotaPendente(rota: RotaPendente): void {
  try {
    sessionStorage.setItem(CHAVE, JSON.stringify(rota));
  } catch {
    // Sem sessionStorage: o mapa abre sem pré-preencher.
  }
}

function ponto(v: unknown): PontoRotaPendente | null {
  if (!v || typeof v !== "object") return null;
  const { nome, lat, lng } = v as Record<string, unknown>;
  if (
    typeof nome !== "string" ||
    typeof lat !== "number" ||
    typeof lng !== "number" ||
    !Number.isFinite(lat) ||
    !Number.isFinite(lng)
  ) {
    return null;
  }
  return { nome, lat, lng };
}

/** Lê e apaga a rota pendente. Retorna null se não houver ou for inválida. */
export function consumirRotaPendente(): RotaPendente | null {
  try {
    const bruto = sessionStorage.getItem(CHAVE);
    if (bruto === null) return null;
    sessionStorage.removeItem(CHAVE);
    const dados = JSON.parse(bruto) as Record<string, unknown>;
    const origem = ponto(dados?.origem);
    const destino = ponto(dados?.destino);
    return origem && destino ? { origem, destino } : null;
  } catch {
    return null;
  }
}
