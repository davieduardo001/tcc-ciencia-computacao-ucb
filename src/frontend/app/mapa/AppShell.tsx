"use client";

import { useEffect, useState } from "react";
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
import { buscarUsuarioAtual, logoutUsuario, UsuarioAtual } from "@/lib/api";
import "./mapa.css";

function iniciais(nome: string): string {
  const partes = nome.trim().split(/\s+/);
  const primeira = partes[0]?.[0] ?? "";
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : "";
  return (primeira + ultima).toUpperCase();
}

const NAV_ITEMS = [
  { id: "mapa", href: "/mapa", label: "Mapa Interativo", Icone: MapIcon, disponivel: true },
  { id: "linhas", href: "/linhas", label: "Linhas de Ônibus", Icone: Bus, disponivel: false },
  { id: "rotas", href: "/rotas", label: "Rotas", Icone: Navigation, disponivel: false },
  { id: "favoritos", href: "/favoritos", label: "Rotas Salvas", Icone: Star, disponivel: false },
  {
    id: "ocorrencias",
    href: "/ocorrencias",
    label: "Ocorrências",
    Icone: TriangleAlert,
    disponivel: false,
  },
  { id: "alertas", href: "/alertas", label: "Alertas", Icone: Bell, disponivel: false },
  { id: "perfil", href: "/perfil", label: "Perfil", Icone: User, disponivel: false },
] as const;

interface AppShellProps {
  active: (typeof NAV_ITEMS)[number]["id"];
  children: React.ReactNode;
  /** US #17 — busca de linha pelo topbar. Sem essa prop, a busca fica
   * só visual (páginas que ainda não a implementam). */
  onBuscarLinha?: (termo: string) => void;
  buscandoLinha?: boolean;
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
}: AppShellProps) {
  const router = useRouter();
  const [usuario, setUsuario] = useState<UsuarioAtual | null>(null);
  const [carregandoUsuario, setCarregandoUsuario] = useState(true);
  const [saindo, setSaindo] = useState(false);

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
            if (onBuscarLinha && typeof termo === "string") {
              onBuscarLinha(termo);
            }
          }}
        >
          <Search size={17} className="ms-search-icon" />
          <input
            name="busca-linha"
            placeholder="Buscar linha (ex: 116 ou 0.110)"
            disabled={buscandoLinha}
          />
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
        {NAV_ITEMS.map(({ id, href, label, Icone, disponivel }) =>
          disponivel ? (
            <Link
              key={id}
              href={href}
              className={`ms-bottomnav-item${id === active ? " active" : ""}`}
              aria-label={label}
              title={label}
            >
              <Icone size={20} />
              <span className="sr-only">{label}</span>
            </Link>
          ) : (
            <span
              key={id}
              className="ms-bottomnav-item indisponivel"
              aria-disabled="true"
              aria-label={`${label} — ainda não disponível`}
              title={`${label} — ainda não disponível`}
            >
              <Icone size={20} />
              <span className="sr-only">{label}</span>
            </span>
          )
        )}
      </nav>
    </div>
  );
}
