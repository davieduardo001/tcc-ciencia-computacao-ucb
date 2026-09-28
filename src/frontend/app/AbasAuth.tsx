import Link from "next/link";

/**
 * Alternador "Entrar / Criar conta" do topo da folha de autenticação.
 *
 * No protótipo as duas telas são uma só, com um controle segmentado. Aqui
 * são duas rotas, então a aba inativa é um link de verdade: o comportamento
 * é o mesmo para quem usa, e continua funcionando sem JavaScript.
 */
interface AbasAuthProps {
  ativa: "login" | "cadastro";
}

export default function AbasAuth({ ativa }: AbasAuthProps) {
  return (
    <nav className="abas-auth" aria-label="Entrar ou criar conta">
      {ativa === "login" ? (
        <span className="aba ativa" aria-current="page">
          Entrar
        </span>
      ) : (
        <Link className="aba" href="/login">
          Entrar
        </Link>
      )}

      {ativa === "cadastro" ? (
        <span className="aba ativa" aria-current="page">
          Criar conta
        </span>
      ) : (
        <Link className="aba" href="/cadastro">
          Criar conta
        </Link>
      )}
    </nav>
  );
}
