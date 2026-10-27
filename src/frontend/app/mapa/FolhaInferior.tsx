"use client";

import {
  KeyboardEvent,
  PointerEvent as ReactPointerEvent,
  ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { X } from "lucide-react";

/**
 * Folha inferior com três alturas (issue #217).
 *
 * É a mesma folha para a rota, a linha e a parada. No celular ela encosta
 * na barra de baixo e fica em uma de três alturas; no desktop (> 920 px) é
 * a coluna lateral de sempre — a alça some e as classes de altura não têm
 * efeito (o CSS delas vive dentro do media query do mobile).
 *
 * A altura em que o usuário solta é o estado: não há "volta para o meio".
 */
export type SnapFolha = "minimo" | "medio" | "maximo";

/** Faixa visível no mínimo: alça mais o cabeçalho. */
export const ALTURA_MINIMA = 96;
/** Mínimo quando há rodapé fixo (Cheguei e Reportar): alça + cabeçalho +
 *  ações + folga do botão "+". Espelha .com-rodape.snap-minimo no CSS. */
export const ALTURA_MINIMA_COM_RODAPE = 200;
/** Altura média, em fração da janela (62vh no CSS). */
const FRACAO_MEDIA = 0.62;
/** Folga do máximo em relação ao topo da área do mapa (8 px). */
const FOLGA_MAXIMA = 8;
/** Quanto do gesto "continua" depois de soltar, em ms, para a velocidade. */
const INERCIA_MS = 120;
/** Intervalos menores que isto não dão velocidade confiável. */
const INTERVALO_MIN_VELOCIDADE_MS = 16;
const ORDEM: SnapFolha[] = ["minimo", "medio", "maximo"];
const QUERY_MOBILE = "(max-width: 920px)";

function ehMobileAgora(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return true;
  }
  return window.matchMedia(QUERY_MOBILE).matches;
}

/** Alturas, em px, dos três encaixes para uma área útil de `area` px. */
export function alturasDaFolha(
  area: number,
  minimo: number = ALTURA_MINIMA
): Record<SnapFolha, number> {
  const maximo = Math.max(minimo, area - FOLGA_MAXIMA);
  const medio = Math.min(maximo, Math.max(minimo, window.innerHeight * FRACAO_MEDIA));
  return { minimo, medio, maximo };
}

/** Encaixe mais próximo de `altura`. */
export function snapMaisProximo(
  altura: number,
  alturas: Record<SnapFolha, number>
): SnapFolha {
  let melhor: SnapFolha = "minimo";
  let menor = Infinity;
  for (const snap of ORDEM) {
    const distancia = Math.abs(alturas[snap] - altura);
    if (distancia < menor) {
      menor = distancia;
      melhor = snap;
    }
  }
  return melhor;
}

interface OpcoesDoHook {
  snap?: SnapFolha;
  onSnapChange?: (snap: SnapFolha) => void;
  snapInicial?: SnapFolha;
  /** Falso = folha escondida: não publica a própria altura na área do mapa. */
  ativa?: boolean;
  /** Altura do encaixe mínimo, em px. */
  minimo?: number;
}

export function useFolhaTresAlturas({
  snap: snapControlado,
  onSnapChange,
  snapInicial = "medio",
  ativa = true,
  minimo = ALTURA_MINIMA,
}: OpcoesDoHook) {
  const ref = useRef<HTMLElement>(null);
  const [snapInterno, setSnapInterno] = useState<SnapFolha>(snapInicial);
  const snap = snapControlado ?? snapInterno;
  const [altura, setAltura] = useState<number | null>(null);
  const [arrastando, setArrastando] = useState(false);

  const minimoRef = useRef(minimo);
  minimoRef.current = minimo;
  const snapRef = useRef(snap);
  snapRef.current = snap;
  const onSnapChangeRef = useRef(onSnapChange);
  onSnapChangeRef.current = onSnapChange;

  const arrasto = useRef<{
    y0: number;
    altura0: number;
    atual: number;
    moveu: boolean;
    amostraY: number;
    amostraT: number;
    velocidade: number;
    alturas: Record<SnapFolha, number>;
  } | null>(null);
  const suprimirClique = useRef(false);

  const mudar = useCallback((proximo: SnapFolha) => {
    setSnapInterno(proximo);
    onSnapChangeRef.current?.(proximo);
  }, []);

  const aoMover = useCallback((evento: PointerEvent) => {
    const atual = arrasto.current;
    if (!atual) return;

    const dy = evento.clientY - atual.y0;
    if (Math.abs(dy) > 3) atual.moveu = true;

    const dt = performance.now() - atual.amostraT;
    if (dt >= INTERVALO_MIN_VELOCIDADE_MS) {
      // px/ms, positivo = subindo (a folha cresce).
      atual.velocidade = (atual.amostraY - evento.clientY) / dt;
      atual.amostraY = evento.clientY;
      atual.amostraT = performance.now();
    }

    atual.atual = Math.max(
      atual.alturas.minimo,
      Math.min(atual.alturas.maximo, atual.altura0 - dy)
    );
    setAltura(atual.atual);
  }, []);

  const aoSoltar = useCallback(() => {
    const atual = arrasto.current;
    window.removeEventListener("pointermove", aoMover);
    window.removeEventListener("pointerup", aoSoltar);
    window.removeEventListener("pointercancel", aoSoltar);
    arrasto.current = null;
    setArrastando(false);
    setAltura(null);

    if (!atual || !atual.moveu) return;

    // Projeta onde a folha chegaria se o gesto continuasse um instante:
    // um peteleco curto para cima leva ao encaixe de cima.
    const projetada = Math.max(
      atual.alturas.minimo,
      Math.min(atual.alturas.maximo, atual.atual + atual.velocidade * INERCIA_MS)
    );
    mudar(snapMaisProximo(projetada, atual.alturas));

    // O pointerup dispara um clique logo em seguida; sem isto, arrastar
    // também alternaria o estado, desfazendo o que o arrasto decidiu.
    suprimirClique.current = true;
    window.setTimeout(() => {
      suprimirClique.current = false;
    }, 60);
  }, [aoMover, mudar]);

  const aoPressionar = useCallback(
    (evento: ReactPointerEvent) => {
      if (!ref.current || !ehMobileAgora()) return;
      // Botões dentro do cabeçalho (fechar) não iniciam arrasto.
      if ((evento.target as HTMLElement).closest?.("button:not(.plan-alca)")) return;

      const area =
        ref.current.parentElement?.clientHeight || window.innerHeight;
      const alturas = alturasDaFolha(area, minimoRef.current);
      const altura0 = ref.current.offsetHeight || alturas[snapRef.current];
      arrasto.current = {
        y0: evento.clientY,
        altura0,
        atual: altura0,
        moveu: false,
        amostraY: evento.clientY,
        amostraT: performance.now(),
        velocidade: 0,
        alturas,
      };
      setArrastando(true);
      window.addEventListener("pointermove", aoMover);
      window.addEventListener("pointerup", aoSoltar);
      window.addEventListener("pointercancel", aoSoltar);
    },
    [aoMover, aoSoltar]
  );

  // Clique (ou Enter/Espaço) na alça: abre ou recolhe. O máximo desce ao médio.
  const aoClicar = useCallback(() => {
    if (suprimirClique.current) return;
    const atual = snapRef.current;
    mudar(atual === "minimo" ? "medio" : atual === "medio" ? "minimo" : "medio");
  }, [mudar]);

  // Setas na alça sobem e descem um encaixe por vez.
  const aoTeclar = useCallback(
    (evento: KeyboardEvent) => {
      const indice = ORDEM.indexOf(snapRef.current);
      if (evento.key === "ArrowUp" && indice < ORDEM.length - 1) {
        evento.preventDefault();
        mudar(ORDEM[indice + 1]);
      } else if (evento.key === "ArrowDown" && indice > 0) {
        evento.preventDefault();
        mudar(ORDEM[indice - 1]);
      }
    },
    [mudar]
  );

  useEffect(
    () => () => {
      window.removeEventListener("pointermove", aoMover);
      window.removeEventListener("pointerup", aoSoltar);
      window.removeEventListener("pointercancel", aoSoltar);
    },
    [aoMover, aoSoltar]
  );

  // Publica a altura da folha na área do mapa, para os botões flutuantes
  // (centralizar, camadas) ficarem acima dela e não por baixo.
  useEffect(() => {
    const folha = ref.current;
    const area = folha?.closest<HTMLElement>(".ms-content") ?? null;
    if (!ativa || !folha || !area || !ehMobileAgora()) return;
    const alturas = alturasDaFolha(
      area.clientHeight || window.innerHeight,
      minimoRef.current
    );
    area.style.setProperty("--folha-altura", `${altura ?? alturas[snap]}px`);
    area.dataset.folha = snap;
    return () => {
      area.style.removeProperty("--folha-altura");
      delete area.dataset.folha;
    };
  }, [snap, altura, ativa]);

  return { ref, snap, altura, arrastando, aoPressionar, aoClicar, aoTeclar, mudar };
}

interface FolhaInferiorProps {
  /** Encaixe controlado; sem ele a folha guarda o próprio. */
  snap?: SnapFolha;
  onSnapChange?: (snap: SnapFolha) => void;
  snapInicial?: SnapFolha;
  titulo: ReactNode;
  /** Classe do cabeçalho (cada consumidor já tem o seu visual). */
  classeCabecalho?: string;
  /** Classes do painel: define o visual no desktop (plan-painel, etc.). */
  className?: string;
  /** Nome do conteúdo na alça: "Abrir {rotuloAlca}" / "Recolher {rotuloAlca}". */
  rotuloAlca: string;
  rotuloFechar: string;
  onFechar: () => void;
  /** Ação fixa no pé da folha (ex.: Cheguei durante a viagem). */
  rodape?: ReactNode;
  /** Escondida, mas montada: preserva estado e efeitos de quem está dentro. */
  oculta?: boolean;
  children: ReactNode;
}

export default function FolhaInferior({
  snap,
  onSnapChange,
  snapInicial,
  titulo,
  classeCabecalho = "plan-cabecalho",
  className = "",
  rotuloAlca,
  rotuloFechar,
  onFechar,
  rodape,
  oculta = false,
  children,
}: FolhaInferiorProps) {
  const folha = useFolhaTresAlturas({
    snap,
    onSnapChange,
    snapInicial,
    ativa: !oculta,
    minimo: rodape ? ALTURA_MINIMA_COM_RODAPE : ALTURA_MINIMA,
  });
  const recolhida = folha.snap === "minimo";

  return (
    <aside
      ref={folha.ref}
      hidden={oculta}
      className={`folha-inferior snap-${folha.snap}${rodape ? " com-rodape" : ""}${folha.arrastando ? " arrastando" : ""}${
        className ? ` ${className}` : ""
      }`}
      style={folha.altura !== null ? { height: `${folha.altura}px` } : undefined}
    >
      {/* Alça (mobile). O botão existe porque arrastar não é acessível por
          teclado: Enter/Espaço abrem e recolhem, e as setas sobem e descem
          um encaixe por vez. */}
      <button
        type="button"
        className="plan-alca"
        aria-expanded={!recolhida}
        aria-label={`${recolhida ? "Abrir" : "Recolher"} ${rotuloAlca}`}
        onPointerDown={folha.aoPressionar}
        onClick={folha.aoClicar}
        onKeyDown={folha.aoTeclar}
      >
        <span className="plan-alca-traco" aria-hidden="true" />
      </button>

      {/* O cabeçalho também arrasta: a rolagem da lista fica livre. */}
      <div
        className={`${classeCabecalho} folha-cabecalho`}
        onPointerDown={folha.aoPressionar}
      >
        {titulo}
        <button
          type="button"
          className="mapa-botao-icone"
          title="Fechar"
          aria-label={rotuloFechar}
          onClick={onFechar}
        >
          <X size={16} />
        </button>
      </div>

      {children}

      {rodape && <div className="folha-rodape">{rodape}</div>}
    </aside>
  );
}
