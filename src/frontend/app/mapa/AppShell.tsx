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
  { id: "mapa", href: "/mapa", label: "Mapa Interativo", Icone: MapIcon },
  { id: "linhas", href: "/linhas", label: "Linhas de Ônibus", Icone: Bus },
  { id: "rotas", href: "/rotas", label: "Rotas", Icone: Navigation },
  { id: "favoritos", href: "/favoritos", label: "Rotas Salvas", Icone: Star },
  {
    id: "ocorrencias",
    href: "/ocorrencias",
    label: "Ocorrências",
    Icone: TriangleAlert,
  },
  { id: "alertas", href: "/alertas", label: "Alertas", Icone: Bell },
  { id: "perfil", href: "/perfil", label: "Perfil", Icone: User },
] as const;

interface AppShellProps {
  active: (typeof NAV_ITEMS)[number]["id"];
  children: React.ReactNode;
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
          {NAV_ITEMS.map(({ id, href, label, Icone }) => (
            <Link
              key={id}
              href={href}
              className={id === active ? "active" : undefined}
            >
              <Icone size={17} />
              <span>{label}</span>
            </Link>
          ))}
        </nav>

        <div className="ms-spacer" />

        <Link href="/rotas" className="ms-nova-viagem">
          <Plus size={17} /> Nova Viagem
        </Link>

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
    </div>
  );
}
