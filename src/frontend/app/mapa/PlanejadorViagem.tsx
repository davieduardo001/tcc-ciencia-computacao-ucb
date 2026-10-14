"use client";

import {
  KeyboardEvent,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpDown,
  Bus,
  Crosshair,
  Footprints,
  LoaderCircle,
  MapPin,
  Pencil,
  Repeat,
  RotateCw,
  Search,
  SearchX,
  Star,
  X,
} from "lucide-react";
import {
  buscarLugares,
  Lugar,
  OpcaoViagem,
  PernaViagem,
  RotaFavorita,
  SalvarFavoritoError,
  salvarFavorito,
} from "@/lib/api";
import BadgeLinha from "./BadgeLinha";
import SeloFonte from "./SeloFonte";
import {
  Destaque,
  destaquesDasOpcoes,
  duracaoDaOpcao,
  minutosAPe,
  Passo,
  passosDaOpcao,
  ROTULO_DESTAQUE,
} from "./resumoViagem";

const DEBOUNCE_MS = 350;
const MIN_CARACTERES = 3;

export type Extremo = "origem" | "destino";

/** Ponto escolhido pelo usuário, venha de onde vier (busca, GPS ou mapa). */
export interface PontoEscolhido {
  nome: string;
  lat: number;
  lng: number;
}

interface PlanejadorViagemProps {
  origem: PontoEscolhido | null;
  destino: PontoEscolhido | null;
  onDefinir: (extremo: Extremo, ponto: PontoEscolhido | null) => void;
  onInverter: () => void;
  onBuscar: () => void;
  /** Ativa o modo "clique no mapa pra escolher este ponto". */
  onEscolherNoMapa: (extremo: Extremo) => void;
  escolhendoNoMapa: Extremo | null;
  onUsarMinhaLocalizacao: (extremo: Extremo) => void;
  temLocalizacao: boolean;
  opcoes: OpcaoViagem[] | null;
  opcaoSelecionada: number | null;
  onSelecionarOpcao: (indice: number) => void;
  calculando: boolean;
  erro: string | null;
  onFechar: () => void;
  /** US #16 — quantos ônibus estão rodando cada linha do itinerário,
   * indexado por número da linha. */
  veiculosPorLinha: Record<string, number>;
  /** Falso enquanto a primeira consulta de posição não voltou — evita
   * dizer "nenhum ônibus" antes de ter perguntado. */
  rastreando: boolean;
  /** US #25 — IDs dos favoritos já salvos, para marcar a estrela. */
  favoritosIds?: Set<string>;
  /** US #25 — callback ao salvar favorito com sucesso. */
  onFavoritoSalvo?: (favorito: RotaFavorita) => void;
}

function CampoLugar({
  extremo,
  rotulo,
  placeholder,
  valor,
  onDefinir,
  onEscolherNoMapa,
  escolhendo,
  onUsarMinhaLocalizacao,
  temLocalizacao,
}: {
  extremo: Extremo;
  rotulo: string;
  placeholder: string;
  valor: PontoEscolhido | null;
  onDefinir: (extremo: Extremo, ponto: PontoEscolhido | null) => void;
  onEscolherNoMapa: (extremo: Extremo) => void;
  escolhendo: boolean;
  onUsarMinhaLocalizacao: (extremo: Extremo) => void;
  temLocalizacao: boolean;
}) {
  const [texto, setTexto] = useState("");
  const [sugestoes, setSugestoes] = useState<Lugar[]>([]);
  const [abertas, setAbertas] = useState(false);
  const [buscando, setBuscando] = useState(false);
  // Opção destacada pelas setas do teclado (-1 = nenhuma). O foco real
  // continua no input; a opção ativa é anunciada via aria-activedescendant.
  const [indiceAtivo, setIndiceAtivo] = useState(-1);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Mesmo problema do autocomplete de linhas: uma busca antiga que
  // demore mais pra responder sobrescreveria a atual.
  const sequenciaRef = useRef(0);
  const listaId = useId();

  // Quando o ponto é definido por fora (GPS, clique no mapa, inversão),
  // o campo precisa refletir isso.
  useEffect(() => {
    setTexto(valor?.nome ?? "");
  }, [valor]);

  const digitar = useCallback(
    (novo: string) => {
      setTexto(novo);
      if (debounceRef.current) clearTimeout(debounceRef.current);

      const sequencia = ++sequenciaRef.current;

      if (novo.trim().length < MIN_CARACTERES) {
        setSugestoes([]);
        setIndiceAtivo(-1);
        setBuscando(false);
        return;
      }

      setBuscando(true);
      debounceRef.current = setTimeout(async () => {
        const resultado = await buscarLugares(novo);
        if (sequencia !== sequenciaRef.current) return;
        setSugestoes(resultado);
        setIndiceAtivo(-1);
        setBuscando(false);
        setAbertas(true);
      }, DEBOUNCE_MS);
    },
    []
  );

  const listaAberta = abertas && sugestoes.length > 0;

  function escolher(lugar: Lugar) {
    onDefinir(extremo, { nome: lugar.nome, lat: lugar.lat, lng: lugar.lng });
    setSugestoes([]);
    setIndiceAtivo(-1);
    setAbertas(false);
  }

  // Padrão ARIA "combobox com lista": setas percorrem, Enter escolhe,
  // Esc fecha. Sem isso, quem navega por teclado digitava e não alcançava
  // nenhuma sugestão.
  function aoTeclar(evento: KeyboardEvent<HTMLInputElement>) {
    if (!listaAberta) {
      if (evento.key === "ArrowDown" && sugestoes.length > 0) {
        evento.preventDefault();
        setAbertas(true);
        setIndiceAtivo(0);
      }
      return;
    }

    if (evento.key === "ArrowDown") {
      evento.preventDefault();
      setIndiceAtivo((i) => (i + 1) % sugestoes.length);
    } else if (evento.key === "ArrowUp") {
      evento.preventDefault();
      setIndiceAtivo((i) => (i <= 0 ? sugestoes.length - 1 : i - 1));
    } else if (evento.key === "Enter" && indiceAtivo >= 0) {
      // Enter com opção ativa escolhe a opção — não envia o formulário.
      evento.preventDefault();
      escolher(sugestoes[indiceAtivo]);
    } else if (evento.key === "Escape") {
      setAbertas(false);
      setIndiceAtivo(-1);
    }
  }

  return (
    <div className={`plan-campo${escolhendo ? " escolhendo" : ""}`}>
      <label className="plan-campo-rotulo" htmlFor={`plan-${extremo}`}>
        <span className={`plan-bolinha ${extremo}`} aria-hidden="true" />
        {rotulo}
      </label>

      <div className="plan-campo-linha">
        <input
          id={`plan-${extremo}`}
          className="plan-input"
          role="combobox"
          aria-expanded={listaAberta}
          aria-controls={listaAberta ? listaId : undefined}
          aria-autocomplete="list"
          aria-activedescendant={
            listaAberta && indiceAtivo >= 0 ? `${listaId}-op-${indiceAtivo}` : undefined
          }
          value={texto}
          placeholder={escolhendo ? "Toque no mapa..." : placeholder}
          autoComplete="off"
          onChange={(e) => digitar(e.target.value)}
          onKeyDown={aoTeclar}
          onFocus={() => setAbertas(true)}
          onBlur={() => setTimeout(() => setAbertas(false), 150)}
        />

        {texto && (
          <button
            type="button"
            className="plan-botao-campo"
            title="Limpar"
            aria-label={`Limpar ${rotulo.toLowerCase()}`}
            onClick={() => {
              setTexto("");
              setSugestoes([]);
              onDefinir(extremo, null);
            }}
          >
            <X size={14} />
          </button>
        )}

        {buscando && <LoaderCircle size={14} className="plan-girando" aria-hidden="true" />}
      </div>

      <div className="plan-atalhos">
        <button
          type="button"
          className="plan-atalho"
          onClick={() => onUsarMinhaLocalizacao(extremo)}
          disabled={!temLocalizacao}
          title={
            temLocalizacao
              ? "Usar minha localização"
              : "Localização indisponível — permita o acesso no navegador"
          }
        >
          <Crosshair size={13} /> Minha localização
        </button>
        <button
          type="button"
          className={`plan-atalho${escolhendo ? " ativo" : ""}`}
          onClick={() => onEscolherNoMapa(extremo)}
        >
          <MapPin size={13} /> {escolhendo ? "Toque no mapa" : "Escolher no mapa"}
        </button>
      </div>

      {listaAberta && (
        <ul className="plan-sugestoes" role="listbox" id={listaId} aria-label={`Sugestões de ${rotulo.toLowerCase()}`}>
          {sugestoes.map((lugar, indice) => (
            <li
              key={`${lugar.lat}-${lugar.lng}-${indice}`}
              id={`${listaId}-op-${indice}`}
              role="option"
              aria-selected={indice === indiceAtivo}
              className={indice === indiceAtivo ? "ativa" : undefined}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => escolher(lugar)}
            >
              <strong>{lugar.nome}</strong>
              <span>{lugar.endereco}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/**
 * 582 dos 7.142 abrigos do SEMOB vêm sem nome utilizável na fonte (só o
 * CEP). Nesses casos o backend manda string vazia de propósito. Coordenada
 * crua ("Ponto em -15.8131, -48.0123") não diz nada a quem vai embarcar, e
 * o metro de caminhada já está ao lado — por isso o rótulo é um texto
 * humano; a coordenada fica só no `title`, pra quem precisar conferir.
 */
const ROTULO_PARADA_SEM_NOME = "Parada sem nome";

function rotuloDoPonto(nome: string): string {
  return nome || ROTULO_PARADA_SEM_NOME;
}

function dicaDoPonto(nome: string, lat: number, lng: number): string | undefined {
  return nome ? undefined : `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
}

function ResumoOpcao({ opcao, destaques }: { opcao: OpcaoViagem; destaques: Destaque[] }) {
  const { minutos, aoVivo } = duracaoDaOpcao(opcao);
  const aPe = minutosAPe(opcao.caminhada_metros);

  // Só <span> aqui dentro: o resumo vive dentro de um <button>, que só
  // aceita conteúdo de fraseado (um <div> ali é HTML inválido).
  return (
    <span className="plan-opcao-resumo">
      <span className="plan-opcao-topo">
        <span className="plan-opcao-linhas">
          {opcao.pernas.map((perna, indice) => (
            <span
              className="plan-opcao-linha-item"
              key={`${perna.numero}-${perna.sentido}-${indice}`}
            >
              {indice > 0 && <Repeat size={12} className="plan-opcao-troca" aria-hidden="true" />}
              <BadgeLinha numero={perna.numero} />
            </span>
          ))}
        </span>

        <span className="plan-opcao-duracao">
          <strong>{minutos} min</strong>
          <span
            className={aoVivo ? "plan-opcao-selo-ao-vivo" : "plan-opcao-selo-estimado"}
            title={
              aoVivo
                ? "Calculado a partir da posição ao vivo dos ônibus"
                : "Sem ônibus rastreado se aproximando; estimativa por velocidade média"
            }
          >
            {aoVivo && <span className="mapa-pulso" />}
            {aoVivo ? "ao vivo" : "estimado"}
          </span>
        </span>
      </span>

      <span className="plan-opcao-chips">
        <span className="plan-chip">
          <Footprints size={13} aria-hidden="true" />
          {aPe > 0 ? `${aPe} min a pé` : "sem caminhada"}
          {aPe > 0 && <span className="plan-chip-detalhe">{opcao.caminhada_metros} m</span>}
        </span>
        <span className="plan-chip">
          {opcao.baldeacoes === 0
            ? "direto"
            : `${opcao.baldeacoes} ${opcao.baldeacoes === 1 ? "baldeação" : "baldeações"}`}
        </span>
        {destaques.map((destaque) => (
          <span className="plan-chip destaque" key={destaque}>
            {ROTULO_DESTAQUE[destaque]}
          </span>
        ))}
      </span>
    </span>
  );
}

/**
 * Quando o ônibus chega — a informação acionável do passo de embarque, por
 * isso é um bloco próprio e destacado, e não mais uma linha de 12,5px acima
 * do texto. US #16 no contexto da US #20: quem planeja a viagem quer saber
 * onde está o ônibus que vai pegar, sem buscar a linha de novo. US #159 —
 * quando a rota já trouxe uma espera calculada para esta perna, ela é mais
 * específica que a contagem de US #16 (fala do ônibus que serve *esta*
 * viagem, não de todos os que rodam a linha agora) e aparece antes.
 */
function Chegada({
  perna,
  veiculosPorLinha,
  rastreando,
}: {
  perna: PernaViagem;
  veiculosPorLinha: Record<string, number>;
  rastreando: boolean;
}) {
  if (perna.fonte_espera === "tempo_real" && perna.espera_min != null) {
    return (
      <p className="plan-chegada ao-vivo">
        <span className="mapa-pulso" />
        <Bus size={14} aria-hidden="true" />
        <span>
          Chega em <strong>{perna.espera_min} min</strong>
          {perna.prefixo_veiculo ? ` (carro ${perna.prefixo_veiculo})` : ""}
        </span>
        <SeloFonte fonte="ao_vivo" />
      </p>
    );
  }

  if (perna.fonte_espera === "intervalo_medio" && perna.intervalo_medio_min != null) {
    return (
      <p className="plan-chegada">
        <span>
          Passa a cada ~<strong>{perna.intervalo_medio_min} min</strong>
          {perna.espera_min != null ? ` (espera estimada ~${perna.espera_min} min)` : ""}
        </span>
        <SeloFonte fonte="media" />
      </p>
    );
  }

  // Espera fixa da baldeação (sem intervalo medido para a linha): entra na
  // duração total da opção, mas a tela não dizia nada sobre ela — a pessoa
  // via "Nenhum ônibus reportando posição" e não sabia que havia uma espera
  // somada ao tempo.
  if (perna.fonte_espera === "teorica" && perna.espera_min != null) {
    return (
      <p className="plan-chegada">
        <span>
          Espera estimada ~<strong>{perna.espera_min} min</strong>
        </span>
        <SeloFonte fonte="estimado" />
      </p>
    );
  }

  const rodando = veiculosPorLinha[perna.numero] ?? 0;
  if (rodando > 0) {
    return (
      <p className="plan-chegada ao-vivo">
        <span className="mapa-pulso" />
        <Bus size={14} aria-hidden="true" />
        {/* "ônibus" é invariável: singular e plural têm o mesmo texto. */}
        <span>
          <strong>{rodando}</strong> ônibus rodando agora
        </span>
        <SeloFonte fonte="ao_vivo" />
      </p>
    );
  }

  return (
    <p className="plan-chegada sem-onibus">
      {rastreando
        ? "Nenhum ônibus desta linha reportando posição agora"
        : "Procurando ônibus..."}
    </p>
  );
}

function kmParaTexto(km: number): string {
  return String(km).replace(".", ",");
}

function Metros({ metros }: { metros: number }) {
  return (
    <>
      <strong>{minutosAPe(metros)} min</strong> <span className="plan-tempo-metros">({metros} m)</span>
    </>
  );
}

/**
 * Detalhe da opção como linha do tempo — era texto corrido de três linhas
 * iguais. Cada passo tem marcador próprio: o número do marcador do mapa no
 * embarque (a tela e o mapa dizem o mesmo), seta no desembarque, pegadas na
 * caminhada, setas de troca na baldeação.
 */
function LinhaDoTempo({
  passos,
  veiculosPorLinha,
  rastreando,
}: {
  passos: Passo[];
  veiculosPorLinha: Record<string, number>;
  rastreando: boolean;
}) {
  return (
    <ol className="plan-tempo">
      {passos.map((passo, posicao) => (
        <li key={passo.chave} className={`plan-tempo-passo ${passo.tipo}`}>
          <span className="plan-tempo-marcador" aria-hidden="true">
            {passo.tipo === "caminhar" && <Footprints size={14} />}
            {passo.tipo === "embarcar" && passo.numeroDoPasso}
            {passo.tipo === "viajar" && <Bus size={14} />}
            {passo.tipo === "descer" && <ArrowDown size={14} />}
            {passo.tipo === "baldear" && <Repeat size={14} />}
          </span>

          <div className="plan-tempo-corpo">
            {passo.tipo === "caminhar" && (
              <p className="plan-tempo-titulo">
                Caminhe <Metros metros={passo.metros} />{" "}
                {posicao === 0 ? "até o embarque" : "até o destino"}
              </p>
            )}

            {passo.tipo === "embarcar" && (
              <>
                <p className="plan-tempo-titulo">
                  Embarque em{" "}
                  <strong
                    title={dicaDoPonto(
                      passo.perna.embarque.parada_nome,
                      passo.perna.embarque.lat,
                      passo.perna.embarque.lng
                    )}
                  >
                    {rotuloDoPonto(passo.perna.embarque.parada_nome)}
                  </strong>
                </p>
                <p className="plan-tempo-linha">
                  <BadgeLinha numero={passo.perna.numero} />
                  <span className="plan-tempo-nome">{passo.perna.nome}</span>
                </p>
                <Chegada
                  perna={passo.perna}
                  veiculosPorLinha={veiculosPorLinha}
                  rastreando={rastreando}
                />
              </>
            )}

            {passo.tipo === "viajar" && (
              <p className="plan-tempo-detalhe">
                {passo.perna.paradas_no_trecho > 0
                  ? `${passo.perna.paradas_no_trecho} paradas · `
                  : ""}
                {kmParaTexto(passo.perna.distancia_km)} km
              </p>
            )}

            {passo.tipo === "descer" && (
              <p className="plan-tempo-titulo">
                Desça em{" "}
                <strong
                  title={dicaDoPonto(
                    passo.perna.desembarque.parada_nome,
                    passo.perna.desembarque.lat,
                    passo.perna.desembarque.lng
                  )}
                >
                  {rotuloDoPonto(passo.perna.desembarque.parada_nome)}
                </strong>
              </p>
            )}

            {passo.tipo === "baldear" && (
              <p className="plan-tempo-titulo">
                Baldeação
                {passo.metros > 0 && (
                  <>
                    : caminhe <Metros metros={passo.metros} />
                  </>
                )}{" "}
                e pegue a linha <BadgeLinha numero={passo.para} />
              </p>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}

/** Limites da folha, em pixels. O mínimo é a faixa que fica visível
 *  quando ela está recolhida: alça mais o cabeçalho. */
const ALTURA_MINIMA = 96;
const LIMIAR_ARRASTO = 46;

/**
 * Folha arrastável do mobile (issue #132).
 *
 * A folha é a camada do meio da tela: fica sobre o mapa e sob a barra de
 * navegação. Recolhida, deixa o trajeto visível e mantém a alça ao
 * alcance do polegar; arrastada para cima, volta a mostrar as opções.
 *
 * O estado só muda se houve movimento de verdade (mais de 3 px). Sem
 * isso, um toque na alça registraria como arrasto de zero pixel e a
 * folha oscilaria sozinha.
 */
function useFolhaArrastavel() {
  const ref = useRef<HTMLElement>(null);
  const [recolhida, setRecolhida] = useState(false);
  const [altura, setAltura] = useState<number | null>(null);
  const [arrastando, setArrastando] = useState(false);
  const arrasto = useRef<{ y0: number; altura0: number; moveu: boolean } | null>(
    null
  );
  const suprimirClique = useRef(false);

  const aoMover = useCallback((evento: PointerEvent) => {
    const atual = arrasto.current;
    if (!atual || !ref.current) return;

    const dy = evento.clientY - atual.y0;
    if (Math.abs(dy) > 3) atual.moveu = true;

    const teto = window.innerHeight * 0.82;
    setAltura(Math.max(ALTURA_MINIMA, Math.min(teto, atual.altura0 - dy)));
  }, []);

  const aoSoltar = useCallback(
    (evento: PointerEvent) => {
      const atual = arrasto.current;
      window.removeEventListener("pointermove", aoMover);
      window.removeEventListener("pointerup", aoSoltar);
      window.removeEventListener("pointercancel", aoSoltar);
      arrasto.current = null;
      setArrastando(false);
      setAltura(null);

      if (!atual || !atual.moveu) return;

      const dy = evento.clientY - atual.y0;
      if (dy < -LIMIAR_ARRASTO) setRecolhida(false);
      else if (dy > LIMIAR_ARRASTO) setRecolhida(true);

      // O pointerup dispara um clique logo em seguida; sem isso, arrastar
      // também alternaria o estado, desfazendo o que o arrasto acabou de
      // decidir.
      suprimirClique.current = true;
      window.setTimeout(() => {
        suprimirClique.current = false;
      }, 60);
    },
    [aoMover]
  );

  const aoPressionar = useCallback(
    (evento: React.PointerEvent) => {
      if (!ref.current) return;
      arrasto.current = {
        y0: evento.clientY,
        altura0: ref.current.offsetHeight,
        moveu: false,
      };
      setArrastando(true);
      window.addEventListener("pointermove", aoMover);
      window.addEventListener("pointerup", aoSoltar);
      window.addEventListener("pointercancel", aoSoltar);
    },
    [aoMover, aoSoltar]
  );

  const aoClicar = useCallback(() => {
    if (suprimirClique.current) return;
    setRecolhida((estava) => !estava);
  }, []);

  return { ref, recolhida, altura, arrastando, aoPressionar, aoClicar };
}

export default function PlanejadorViagem({
  origem,
  destino,
  onDefinir,
  onInverter,
  onBuscar,
  onEscolherNoMapa,
  escolhendoNoMapa,
  onUsarMinhaLocalizacao,
  temLocalizacao,
  opcoes,
  opcaoSelecionada,
  onSelecionarOpcao,
  calculando,
  erro,
  onFechar,
  veiculosPorLinha,
  rastreando,
  favoritosIds = new Set(),
  onFavoritoSalvo,
}: PlanejadorViagemProps) {
  const podeBuscar = Boolean(origem && destino) && !calculando;
  const folha = useFolhaArrastavel();
  const idBase = useId();

  // Mobile: depois de calcular, o formulário recolhe numa linha
  // "Origem → Destino [Editar]" pra rota continuar visível no mapa. Um novo
  // resultado sempre volta ao modo resumido.
  const [editando, setEditando] = useState(false);
  useEffect(() => {
    setEditando(false);
  }, [opcoes]);
  const comResultado = opcoes !== null && opcoes.length > 0;
  const destaques = opcoes ? destaquesDasOpcoes(opcoes) : [];

  // US #25 — estado do botão de favorito por índice de opção.
  const [salvando, setSalvando] = useState<number | null>(null);
  const [erroFavorito, setErroFavorito] = useState<string | null>(null);

  async function handleSalvarFavorito(indice: number) {
    if (!origem || !destino || !opcoes) return;
    const opcao = opcoes[indice];
    const primeiraPerna = opcao.pernas[0];
    if (!primeiraPerna) return;

    setSalvando(indice);
    setErroFavorito(null);

    try {
      const favorito = await salvarFavorito({
        numero_linha: primeiraPerna.numero,
        nome_linha: primeiraPerna.nome,
        label: `${origem.nome} → ${destino.nome}`,
        origem_lat: origem.lat,
        origem_lng: origem.lng,
        destino_lat: destino.lat,
        destino_lng: destino.lng,
      });
      onFavoritoSalvo?.(favorito);
    } catch (err) {
      if (err instanceof SalvarFavoritoError) {
        setErroFavorito(err.message);
      } else {
        setErroFavorito("Não foi possível salvar o favorito.");
      }
    } finally {
      setSalvando(null);
    }
  }

  // Chave de identificação de uma opção para verificar se já está salva.
  function chaveOpcao(opcao: OpcaoViagem, orig: PontoEscolhido, dest: PontoEscolhido): string {
    const linha = opcao.pernas[0]?.numero ?? "";
    return `${linha}:${orig.lat.toFixed(4)},${orig.lng.toFixed(4)}:${dest.lat.toFixed(4)},${dest.lng.toFixed(4)}`;
  }

  function jaFavoritado(opcao: OpcaoViagem): boolean {
    if (!origem || !destino) return false;
    // Verifica pelo cache local: itera os ids conhecidos checando a chave
    // lógica. O Set de IDs não permite verificação por conteúdo, então
    // guardamos a chave lógica no próprio Set quando salvamos.
    return favoritosIds.has(chaveOpcao(opcao, origem, destino));
  }

  // Anunciado a leitores de tela: o resultado chega sem mover o foco, e um
  // texto de botão que muda não avisa ninguém.
  const anuncio = calculando
    ? "Calculando rotas..."
    : opcoes === null
      ? ""
      : opcoes.length === 0
        ? "Nenhuma opção encontrada."
        : `${opcoes.length} ${opcoes.length === 1 ? "opção encontrada" : "opções encontradas"}.`;

  return (
    <aside
      ref={folha.ref}
      className={`plan-painel${folha.recolhida ? " recolhida" : ""}${
        folha.arrastando ? " arrastando" : ""
      }${comResultado ? " com-resultado" : ""}${editando ? " editando" : ""}`}
      style={folha.altura !== null ? { height: `${folha.altura}px` } : undefined}
    >
      {/* Alça da folha (mobile). O botão existe porque arrastar não é
          acessível por teclado — quem navega assim alterna por aqui. */}
      <button
        type="button"
        className="plan-alca"
        aria-expanded={!folha.recolhida}
        aria-label={folha.recolhida ? "Abrir opções de viagem" : "Recolher opções de viagem"}
        onPointerDown={folha.aoPressionar}
        onClick={folha.aoClicar}
      >
        <span className="plan-alca-traco" aria-hidden="true" />
      </button>

      <div className="plan-cabecalho">
        <strong>Para onde você vai?</strong>
        <button
          type="button"
          className="mapa-botao-icone"
          title="Fechar"
          aria-label="Fechar planejador de viagem"
          onClick={onFechar}
        >
          <X size={16} />
        </button>
      </div>

      {/* Só no mobile (o CSS esconde no desktop): o formulário some depois
          de calcular e este resumo o substitui. */}
      {comResultado && (
        <div className="plan-resumo-rota">
          <span className="plan-resumo-rota-trecho">
            <strong>{origem?.nome}</strong>
            <ArrowRight size={14} aria-hidden="true" />
            <strong>{destino?.nome}</strong>
          </span>
          <button
            type="button"
            className="plan-editar"
            aria-expanded={editando}
            onClick={() => setEditando((v) => !v)}
          >
            <Pencil size={14} aria-hidden="true" />
            {editando ? "Fechar edição" : "Editar"}
          </button>
        </div>
      )}

      <form
        className="plan-formulario"
        onSubmit={(e) => {
          e.preventDefault();
          if (podeBuscar) onBuscar();
        }}
      >
        <CampoLugar
          extremo="origem"
          rotulo="De onde"
          placeholder="Ex: Terminal Ceilândia"
          valor={origem}
          onDefinir={onDefinir}
          onEscolherNoMapa={onEscolherNoMapa}
          escolhendo={escolhendoNoMapa === "origem"}
          onUsarMinhaLocalizacao={onUsarMinhaLocalizacao}
          temLocalizacao={temLocalizacao}
        />

        <button
          type="button"
          className="plan-inverter"
          title="Inverter origem e destino"
          aria-label="Inverter origem e destino"
          onClick={onInverter}
          disabled={!origem && !destino}
        >
          <ArrowUpDown size={14} />
        </button>

        <CampoLugar
          extremo="destino"
          rotulo="Para onde"
          placeholder="Ex: Rodoviária do Plano Piloto"
          valor={destino}
          onDefinir={onDefinir}
          onEscolherNoMapa={onEscolherNoMapa}
          escolhendo={escolhendoNoMapa === "destino"}
          onUsarMinhaLocalizacao={onUsarMinhaLocalizacao}
          temLocalizacao={temLocalizacao}
        />

        <button type="submit" className="plan-buscar" disabled={!podeBuscar}>
          {calculando ? (
            <>
              <LoaderCircle size={15} className="plan-girando" /> Calculando...
            </>
          ) : (
            <>
              <Search size={15} /> Ver opções de ônibus
            </>
          )}
        </button>
      </form>

      <p className="sr-only" role="status">
        {anuncio}
      </p>

      {calculando && (
        <div className="plan-esqueletos" aria-hidden="true">
          <div className="plan-esqueleto" />
          <div className="plan-esqueleto" />
          <div className="plan-esqueleto" />
        </div>
      )}

      {erro && (
        <div className="plan-erro" role="alert">
          <p>{erro}</p>
          {podeBuscar && (
            <button type="button" className="plan-acao-erro" onClick={onBuscar}>
              <RotateCw size={14} aria-hidden="true" /> Tentar de novo
            </button>
          )}
        </div>
      )}

      {opcoes !== null && opcoes.length === 0 && !calculando && !erro && (
        <div className="plan-vazio">
          <SearchX size={22} aria-hidden="true" />
          <p>Nenhuma linha liga esses dois pontos — nem com troca de ônibus.</p>
          <p className="plan-vazio-dica">
            Tente um ponto de referência mais próximo de uma via principal.
          </p>
          <button
            type="button"
            className="plan-acao-secundaria"
            onClick={() => onDefinir("destino", null)}
          >
            Escolher outro destino
          </button>
        </div>
      )}

      {opcoes !== null && opcoes.length > 0 && (
        <div className="plan-resultados">
          <div className="plan-resultados-titulo">
            {opcoes.length} {opcoes.length === 1 ? "opção" : "opções"}
            {(() => {
              // A lista mistura diretas e baldeações, ordenadas por
              // tempo — às vezes a baldeação é a mais rápida. Um rótulo
              // baseado só na primeira opção mentiria sobre o resto.
              const diretas = opcoes.filter((o) => o.baldeacoes === 0).length;
              const comTroca = opcoes.length - diretas;
              if (diretas && comTroca) {
                return ` · ${diretas} direta${diretas > 1 ? "s" : ""}, ${comTroca} com baldeação`;
              }
              if (comTroca) return " · todas com baldeação";
              return ` · direta${diretas > 1 ? "s" : ""}`;
            })()}
          </div>

          <ul className="plan-opcoes">
            {opcoes.map((opcao, indice) => {
              const selecionada = indice === opcaoSelecionada;
              const idDetalhe = `${idBase}-detalhe-${indice}`;

              return (
                <li
                  key={indice}
                  className={`plan-opcao-card${selecionada ? " selecionada" : ""}`}
                >
                  {/* O botão contém só o resumo. Os passos ficam num
                      irmão: lista e <div> dentro de <button> é HTML
                      inválido e derruba a semântica pra quem usa leitor
                      de tela. */}
                  <button
                    type="button"
                    className="plan-opcao"
                    onClick={() => onSelecionarOpcao(indice)}
                    aria-expanded={selecionada}
                    aria-controls={selecionada ? idDetalhe : undefined}
                  >
                    <ResumoOpcao opcao={opcao} destaques={destaques[indice] ?? []} />
                  </button>

                  {selecionada && (
                    <div
                      id={idDetalhe}
                      className="plan-opcao-detalhe"
                      role="group"
                      aria-label={`Passos da opção ${indice + 1}`}
                    >
                      <LinhaDoTempo
                        passos={passosDaOpcao(opcao)}
                        veiculosPorLinha={veiculosPorLinha}
                        rastreando={rastreando}
                      />
                    </div>
                  )}

                  {/* US #25 — botão de favorito fora do <button> da opção
                      para evitar button dentro de button (HTML inválido). */}
                  {selecionada && (
                    <div className="plan-favorito-area">
                      <button
                        type="button"
                        className={`plan-favorito-btn${jaFavoritado(opcao) ? " salvo" : ""}`}
                        onClick={() => {
                          if (!jaFavoritado(opcao)) handleSalvarFavorito(indice);
                        }}
                        disabled={salvando === indice || jaFavoritado(opcao)}
                        aria-label={
                          jaFavoritado(opcao)
                            ? "Rota já salva nos favoritos"
                            : "Salvar como favorita"
                        }
                        title={
                          jaFavoritado(opcao)
                            ? "Já está nos seus favoritos"
                            : "Salvar rota como favorita"
                        }
                      >
                        {salvando === indice ? (
                          <LoaderCircle size={14} className="plan-girando" />
                        ) : (
                          <Star
                            size={14}
                            fill={jaFavoritado(opcao) ? "currentColor" : "none"}
                          />
                        )}
                        <span>
                          {jaFavoritado(opcao)
                            ? "Salva nos favoritos"
                            : salvando === indice
                            ? "Salvando..."
                            : "Salvar como favorita"}
                        </span>
                      </button>
                      {erroFavorito && salvando === null && (
                        <p
                          className="plan-erro plan-favorito-erro"
                          role="alert"
                        >
                          {erroFavorito}
                        </p>
                      )}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>

          {/* Legenda do selo "ao vivo": ele cobre só a espera pelo 1º
              ônibus. Antes a ressalva dizia "tempo estimado por velocidade
              média" logo abaixo de opções marcadas "ao vivo". */}
          <p className="plan-ressalva">
            <strong>Ao vivo</strong> vale só para a espera pelo primeiro ônibus
            (posição real). O tempo dentro do ônibus e as baldeações são
            estimados por velocidade e intervalo médios, sem horário de tabela.
            Planejamento por horário de partida está em desenvolvimento.
          </p>
        </div>
      )}
    </aside>
  );
}
