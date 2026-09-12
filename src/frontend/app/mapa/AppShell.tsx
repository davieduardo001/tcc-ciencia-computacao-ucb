import Link from "next/link";
import {
  Bell,
  Bus,
  Map as MapIcon,
  Navigation,
  Plus,
  Search,
  Settings,
  Star,
  TriangleAlert,
  User,
} from "lucide-react";
import "./mapa.css";

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

export default function AppShell({ active, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="ms-sidebar">
        <div className="ms-brand">
          <div className="ms-brand-mark">M</div>
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
          <div className="ms-avatar">AM</div>
          <div>
            <strong>Admin Movecity</strong>
            <small>Conta demo</small>
          </div>
        </div>
      </aside>

      <header className="ms-topbar">
        <div className="ms-search">
          <Search size={17} className="ms-search-icon" />
          <input placeholder="Para onde vamos? Busque linha, parada ou destino" />
        </div>
        <div className="ms-actions">
          <button type="button" className="ms-icon-btn" title="Alertas">
            <Bell size={17} />
            <span className="ms-badge-count">3</span>
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
