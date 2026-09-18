"use client";

import { CSSProperties, Fragment, useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Bell,
  Bus,
  LogOut,
  Map as MapIcon,
  Navigation,
  Plus,
  Search,
  Settings,
  Star,
  TriangleAlert,
  User,
} from "lucide-react";
import { buscarUsuarioAtual, logoutUsuario, LinhaResumo, UsuarioAtual } from "@/lib/api";
import AvisoEmBreve from "../AvisoEmBreve";
import "./mapa.css";

function iniciais(nome: string): string {
  const partes = nome.trim().split(/\s+/);
  const primeira = partes[0]?.[0] ?? "";
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : "";
  return (primeira + ultima).toUpperCase();
}

// "Linhas de Ônibus" e "Rotas" não são páginas separadas: as duas
// funcionalidades vivem dentro do mapa (busca de linha na barra de
// cima, planejador no painel lateral). Marcá-las como "em breve" dizia
// ao usuário que não existiam, sendo que estão entregues — as US #15,
// #17 e #20 estão em produção. Os links abrem o mapa já com o painel
// certo, via ?painel=.
//
// "Perfil" saiu daqui: já existe o botão de perfil na barra de cima, e
// ter os dois duplicava a mesma entrada.
const NAV_ITEMS = [
  { id: "mapa", href: "/mapa", label: "Mapa Interativo", Icone: MapIcon, disponivel: true },
  {
    id: "linhas",
    href: "/mapa?painel=linhas",
    label: "Linhas de Ônibus",
    Icone: Bus,
    disponivel: true,
  },
  {
    id: "rotas",
    href: "/mapa?painel=rotas",
    label: "Rotas",
    Icone: Navigation,
    disponivel: true,
  },
  { id: "favoritos", href: "/favoritos", label: "Rotas Salvas", Icone: Star, disponivel: false },
  {
    id: "ocorrencias",
    href: "/ocorrencias",
    label: "Ocorrências",
    Icone: TriangleAlert,
    disponivel: false,
  },
  { id: "alertas", href: "/alertas", label: "Alertas", Icone: Bell, disponivel: false },
] as const;

// Navegação inferior (mobile), conforme o protótipo v3: quatro destinos e
// o botão de ação no centro. É uma lista própria, e não um recorte de
// NAV_ITEMS, porque a barra lateral do desktop e a barra inferior do
// celular respondem a perguntas diferentes — a lateral lista tudo que
// existe, a inferior lista para onde se vai o tempo todo.
const NAV_INFERIOR = [
  { id: "mapa", href: "/mapa", label: "Mapa", Icone: MapIcon, disponivel: true },
  {
    id: "linhas",
    href: "/mapa?painel=linhas",
    label: "Linhas",
    Icone: Bus,
    disponivel: true,
  },
  {
    id: "rotas",
    href: "/mapa?painel=rotas",
    label: "Rotas",
    Icone: Navigation,
    disponivel: true,
  },
  { id: "perfil", href: "/perfil", label: "Perfil", Icone: User, disponivel: false },
] as const;

// O arco que abre no botão central. São as três seções que o protótipo
// tira da barra para caberem os quatro destinos principais. Nenhuma tem
// tela ainda — todas abrem o aviso de "em breve".
const ACOES_RAPIDAS = [
  { id: "salvas", label: "Rotas salvas", Icone: Star, dx: -74, dy: -54 },
  { id: "ocorrencias", label: "Ocorrências", Icone: TriangleAlert, dx: 0, dy: -84 },
  { id: "alertas", label: "Alertas", Icone: Bell, dx: 74, dy: -54 },
] as const;

interface AppShellProps {
  active: (typeof NAV_ITEMS)[number]["id"];
  children: React.ReactNode;
  /** US #17 — busca de linha pelo topbar. Sem essas props, a busca fica
   * só visual (páginas que ainda não a implementam). */
  onBuscarLinha?: (termo: string) => void;
  buscandoLinha?: boolean;
  /** Autocomplete: chamado a cada tecla digitada (com debounce de quem
   * usa), pra popular sugestoesLinha. */
  onDigitarBuscaLinha?: (termo: string) => void;
  sugestoesLinha?: LinhaResumo[];
  onSelecionarSugestaoLinha?: (numero: string) => void;
  /** Nonce: quando muda, o campo de busca recebe foco. Usado pelo item
   * "Linhas de Ônibus" da navegação, que aponta pra esta mesma página. */
  focarBusca?: number;
}

function ItemNav({
  item,
  active,
}: {
  item: (typeof NAV_ITEMS)[number];
  active: AppShellProps["active"];
}) {
  const { id, href, label, Icone, disponivel } = item;

  if (!disponivel) {
    return (
      <span className="ms-nav-item indisponivel" aria-disabled="true">
        <Icone size={17} />
        <span className="ms-nav-label">{label}</span>
        <em className="ms-badge-em-breve">Em breve</em>
      </span>
    );
  }

  return (
    <Link
      href={href}
      className={`ms-nav-item${id === active ? " active" : ""}`}
    >
      <Icone size={17} />
      <span className="ms-nav-label">{label}</span>
    </Link>
  );
}

export default function AppShell({
  active,
  children,
  onBuscarLinha,
  buscandoLinha,
  onDigitarBuscaLinha,
  sugestoesLinha,
  onSelecionarSugestaoLinha,
  focarBusca,
}: AppShellProps) {
  const router = useRouter();
  const [usuario, setUsuario] = useState<UsuarioAtual | null>(null);
  const [carregandoUsuario, setCarregandoUsuario] = useState(true);
  const [saindo, setSaindo] = useState(false);
  const [fabAberto, setFabAberto] = useState(false);
  const [emBreve, setEmBreve] = useState<string | null>(null);

  function avisar(label: string) {
    setFabAberto(false);
    setEmBreve(label);
  }

  // Escape fecha o arco: o fundo que o fecha por clique é decorativo, e
  // quem navega por teclado precisa de uma saída.
  useEffect(() => {
    if (!fabAberto) return;
    function aoTeclar(e: KeyboardEvent) {
      if (e.key === "Escape") setFabAberto(false);
    }
    document.addEventListener("keydown", aoTeclar);
    return () => document.removeEventListener("keydown", aoTeclar);
  }, [fabAberto]);
  const [sugestoesAbertas, setSugestoesAbertas] = useState(false);
  const fecharSugestoesTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const buscaRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (focarBusca) {
      buscaRef.current?.focus();
    }
  }, [focarBusca]);

  function fecharSugestoesComAtraso() {
    // Atraso pequeno pra permitir o onClick da sugestão disparar antes
    // do onBlur do input fechar a lista (senão o clique nunca chega).
    fecharSugestoesTimeout.current = setTimeout(() => setSugestoesAbertas(false), 150);
  }

  function cancelarFechamentoDeSugestoes() {
    if (fecharSugestoesTimeout.current) {
      clearTimeout(fecharSugestoesTimeout.current);
    }
  }

  async function handleSair() {
    setSaindo(true);
    await logoutUsuario();
    router.push("/login");
  }

  useEffect(() => {
    let ativo = true;

    buscarUsuarioAtual().then((dados) => {
      if (ativo) {
        setUsuario(dados);
        setCarregandoUsuario(false);
      }
    });

    return () => {
      ativo = false;
    };
  }, []);

  return (
    <div className="app-shell">
      <aside className="ms-sidebar">
        <div className="ms-brand">
          <div className="ms-brand-mark">
            <Image
              src="/movecity-icon.png"
              alt=""
              width={38}
              height={38}
              priority
            />
          </div>
          <div>
            <strong>Movecity</strong>
            <small>Mobilidade DF</small>
          </div>
        </div>

        <nav className="ms-nav">
          {NAV_ITEMS.map((item) => (
            <ItemNav key={item.id} item={item} active={active} />
          ))}
        </nav>

        <div className="ms-spacer" />

        <span className="ms-nova-viagem indisponivel" aria-disabled="true" title="Ainda não disponível">
          <Plus size={17} /> Nova Viagem
          <em className="ms-badge-em-breve">Em breve</em>
        </span>

        <div className="ms-user">
          <div className="ms-avatar">
            {usuario ? iniciais(usuario.nome) : <User size={16} />}
          </div>
          <div>
            <strong>
              {carregandoUsuario
                ? "Carregando..."
                : usuario?.nome ?? "Visitante"}
            </strong>
            <small>
              {carregandoUsuario ? "" : usuario?.email ?? "Não autenticado"}
            </small>
          </div>
          {usuario && (
            <button
              type="button"
              className="ms-sair-btn"
              title="Sair"
              onClick={handleSair}
              disabled={saindo}
            >
              <LogOut size={16} />
            </button>
          )}
        </div>
      </aside>

      <header className="ms-topbar">
        <form
          className="ms-search"
          onSubmit={(evento) => {
            evento.preventDefault();
            const termo = new FormData(evento.currentTarget).get("busca-linha");
            if (typeof termo !== "string") return;

            // Enter com sugestão única na lista seleciona ela direto —
            // importante pra busca por destino ("Ceilândia"), que nunca
            // bate como número exato de linha.
            if (sugestoesLinha?.length === 1 && onSelecionarSugestaoLinha) {
              onSelecionarSugestaoLinha(sugestoesLinha[0].numero);
            } else {
              onBuscarLinha?.(termo);
            }
            setSugestoesAbertas(false);
          }}
        >
          <Search size={17} className="ms-search-icon" />
          <input
            ref={buscaRef}
            name="busca-linha"
            placeholder="Buscar linha ou destino (ex: 0.110 ou Ceilândia)"
            disabled={buscandoLinha}
            autoComplete="off"
            onChange={(evento) => {
              setSugestoesAbertas(true);
              onDigitarBuscaLinha?.(evento.target.value);
            }}
            onFocus={() => {
              cancelarFechamentoDeSugestoes();
              setSugestoesAbertas(true);
            }}
            onBlur={fecharSugestoesComAtraso}
          />

          {sugestoesAbertas && sugestoesLinha && sugestoesLinha.length > 0 && (
            <ul className="ms-search-sugestoes" role="listbox">
              {sugestoesLinha.map((linha) => (
                <li key={linha.numero}>
                  <button
                    type="button"
                    onMouseDown={(evento) => {
                      // preventDefault evita o blur do input antes do
                      // clique registrar (senão a lista some antes).
                      evento.preventDefault();
                    }}
                    onClick={() => {
                      onSelecionarSugestaoLinha?.(linha.numero);
                      setSugestoesAbertas(false);
                    }}
                  >
                    <strong>{linha.numero}</strong>
                    <span className="ms-search-sugestao-nome">{linha.nome}</span>
                    <span className="ms-search-sugestao-sentido">{linha.sentido}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </form>
        <div className="ms-actions">
          <button type="button" className="ms-icon-btn" title="Alertas">
            <Bell size={17} />
          </button>
          <button type="button" className="ms-icon-btn" title="Preferências">
            <Settings size={17} />
          </button>
          <button type="button" className="ms-icon-btn" title="Perfil">
            <User size={17} />
          </button>
        </div>
      </header>

      <main className="ms-content">{children}</main>

      <nav className="ms-bottomnav" aria-label="Navegação principal">
        {NAV_INFERIOR.map(({ id, href, label, Icone, disponivel }, indice) => (
          <Fragment key={id}>
            {indice === 2 && <span className="ms-bottomnav-vao" aria-hidden="true" />}
            {disponivel ? (
              <Link
                href={href}
                className={`ms-bottomnav-item${id === active ? " active" : ""}`}
                aria-current={id === active ? "page" : undefined}
              >
                <Icone size={20} />
                <span className="ms-bottomnav-rotulo">{label}</span>
                <span className="ms-bottomnav-ponto" aria-hidden="true" />
              </Link>
            ) : (
              <button
                type="button"
                className="ms-bottomnav-item indisponivel"
                onClick={() => avisar(label)}
              >
                <Icone size={20} />
                <span className="ms-bottomnav-rotulo">{label}</span>
              </button>
            )}
          </Fragment>
        ))}

        <div className={`ms-fab-area${fabAberto ? " aberto" : ""}`}>
          {ACOES_RAPIDAS.map(({ id, label, Icone, dx, dy }, indice) => (
            <button
              key={id}
              type="button"
              className="ms-fab-acao"
              style={
                {
                  "--dx": `${dx}px`,
                  "--dy": `${dy}px`,
                  "--atraso": `${indice * 45}ms`,
                } as CSSProperties
              }
              tabIndex={fabAberto ? 0 : -1}
              aria-hidden={!fabAberto}
              onClick={() => avisar(label)}
            >
              <span className="ms-fab-acao-icone">
                <Icone size={17} />
              </span>
              <span className="ms-fab-acao-rotulo">{label}</span>
            </button>
          ))}

          <button
            type="button"
            className="ms-fab"
            aria-expanded={fabAberto}
            aria-label={fabAberto ? "Fechar ações rápidas" : "Ações rápidas"}
            onClick={() => setFabAberto((aberto) => !aberto)}
          >
            <Plus size={24} />
          </button>
        </div>
      </nav>

      {fabAberto && (
        <div
          className="ms-fab-fundo"
          aria-hidden="true"
          onClick={() => setFabAberto(false)}
        />
      )}

      <AvisoEmBreve
        aberto={emBreve !== null}
        onFechar={() => setEmBreve(null)}
        titulo={emBreve ?? ""}
      >
        Essa seção ainda está sendo construída. Em breve ela aparece por aqui.
      </AvisoEmBreve>
    </div>
  );
}
