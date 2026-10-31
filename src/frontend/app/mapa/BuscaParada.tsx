"use client";

import { useRef, useState } from "react";
import { ChevronRight, LoaderCircle, MapPin, Search, X } from "lucide-react";
import {
  buscarParadas,
  BuscarParadasError,
  ParadaBuscada,
  ResultadoBuscaParada,
} from "@/lib/api";

/** Mesmo mínimo do backend: com 1–2 letras quase toda parada casa. */
const MIN_CARACTERES = 3;

/** "120 m" / "1,2 km". */
export function formatarDistancia(metros: number): string {
  const arredondado = Math.round(metros);
  if (arredondado < 1000) return `${arredondado} m`;
  return `${(arredondado / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} km`;
}

function descreverParada(parada: ParadaBuscada): string {
  const linhas = `${parada.qtdLinhas} ${parada.qtdLinhas === 1 ? "linha" : "linhas"}`;
  return parada.distanciaM !== null
    ? `${formatarDistancia(parada.distanciaM)} · ${linhas}`
    : linhas;
}

interface BuscaParadaProps {
  onFechar: () => void;
  /** Resultado da busca, pra o mapa destacar as paradas (ou limpar, com null). */
  onResultado: (resultado: ResultadoBuscaParada | null) => void;
  /** Tocar numa parada da lista: o mapa centraliza e abre o painel da US #18. */
  onSelecionar: (parada: ParadaBuscada) => void;
}

/**
 * US #21 — Buscar Parada por Nome ou Endereço.
 *
 * A busca só dispara ao confirmar (Enter ou botão), e não a cada tecla:
 * quando o nome não casa, o backend consulta o Nominatim, que tem limite de
 * 1 requisição por segundo para a aplicação inteira.
 */
export default function BuscaParada({ onFechar, onResultado, onSelecionar }: BuscaParadaProps) {
  const [termo, setTermo] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [resultado, setResultado] = useState<ResultadoBuscaParada | null>(null);
  // Último termo buscado: enquanto o campo difere dele, a tela lembra que a
  // busca só sai ao confirmar (issue #236).
  const [termoBuscado, setTermoBuscado] = useState<string | null>(null);
  // Só vale a resposta da busca mais recente (mesma ideia da issue #174).
  const sequenciaRef = useRef(0);

  const termoValido = termo.trim().length >= MIN_CARACTERES;

  async function buscar() {
    if (!termoValido) return;
    const sequencia = ++sequenciaRef.current;
    setTermoBuscado(termo.trim());
    setCarregando(true);
    setErro(null);

    try {
      const encontrado = await buscarParadas(termo.trim());
      if (sequencia !== sequenciaRef.current) return;
      setResultado(encontrado);
      onResultado(encontrado.paradas.length > 0 ? encontrado : null);
    } catch (err) {
      if (sequencia !== sequenciaRef.current) return;
      setResultado(null);
      onResultado(null);
      setErro(
        err instanceof BuscarParadasError
          ? err.message
          : "Não foi possível buscar paradas. Tente novamente."
      );
    } finally {
      if (sequencia === sequenciaRef.current) setCarregando(false);
    }
  }

  function fechar() {
    sequenciaRef.current++;
    onResultado(null);
    onFechar();
  }

  const quantidade = resultado?.paradas.length ?? 0;

  return (
    <aside className="plan-painel bp-painel" aria-label="Buscar parada">
      <div className="plan-cabecalho">
        <span className="bp-cabecalho-titulo">
          <MapPin size={18} aria-hidden="true" />
          <strong>Buscar parada</strong>
        </span>
        <button
          type="button"
          className="mapa-botao-icone"
          title="Fechar"
          aria-label="Fechar busca de parada"
          onClick={fechar}
        >
          <X size={16} />
        </button>
      </div>

      {/* Como no protótipo: campo único com a lupa dentro, sem botão — a
          busca sai pelo Enter (ou pela tecla "buscar" do teclado do celular). */}
      <form
        className="bp-formulario"
        role="search"
        onSubmit={(e) => {
          e.preventDefault();
          buscar();
        }}
      >
        <label className="sr-only" htmlFor="bp-termo">
          Nome, referência ou endereço
        </label>
        <div className="bp-campo">
          <Search size={17} className="bp-campo-lupa" aria-hidden="true" />
          <input
            id="bp-termo"
            className="bp-input"
            name="busca-parada"
            type="search"
            enterKeyHint="search"
            placeholder="Nome, referência ou endereço"
            autoComplete="off"
            autoFocus
            value={termo}
            onChange={(e) => setTermo(e.target.value)}
          />
          {carregando && (
            <LoaderCircle
              size={17}
              className="bp-campo-carregando plan-girando"
              aria-label="Buscando"
            />
          )}
        </div>
        {termo.trim().length > 0 && !termoValido && (
          <p className="bp-dica">Digite pelo menos {MIN_CARACTERES} letras.</p>
        )}
        {termoValido && !carregando && termo.trim() !== termoBuscado && (
          <p className="bp-dica">Pressione Enter para buscar.</p>
        )}
      </form>

      <div className="bp-resultados" aria-live="polite">
        {erro && (
          <p className="bp-mensagem" role="alert">
            {erro}
          </p>
        )}

        {/* Cenário 3 */}
        {resultado && quantidade === 0 && (
          <p className="bp-mensagem">
            Nenhuma parada encontrada para “{termo.trim()}”. Tente outro nome, um bairro ou um
            ponto de referência próximo.
          </p>
        )}

        {resultado && quantidade > 0 && (
          <>
            <p className="bp-titulo">
              {quantidade} {quantidade === 1 ? "parada encontrada" : "paradas encontradas"}
              {/* Cenário 2: deixa claro que é "perto de", e não o nome da parada. */}
              {resultado.tipo === "endereco" && resultado.referencia && (
                <> perto de {resultado.referencia.nome}</>
              )}
            </p>
            <ul className="bp-lista">
              {resultado.paradas.map((parada) => (
                <li key={parada.codigo}>
                  <button
                    type="button"
                    className="bp-item"
                    onClick={() => onSelecionar(parada)}
                  >
                    <span className="bp-item-icone" aria-hidden="true">
                      <MapPin size={22} />
                    </span>
                    <span className="bp-item-texto">
                      <strong>{parada.nome || "Parada sem nome cadastrado"}</strong>
                      <span>{descreverParada(parada)}</span>
                    </span>
                    <ChevronRight size={16} className="bp-item-seta" aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </aside>
  );
}
