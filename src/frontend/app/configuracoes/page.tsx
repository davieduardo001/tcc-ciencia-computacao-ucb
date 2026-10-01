"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "../mapa/AppShell";
import { buscarUsuarioAtual, atualizarFirstAccess, logoutUsuario } from "@/lib/api";

export default function Configuracoes() {
  const router = useRouter();
  const [usuario, setUsuario] = useState<{
    nome: string;
    email: string;
    avatarUrl: string | null;
    firstAccess: boolean;
  } | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [mensagem, setMensagem] = useState<{ tipo: "sucesso" | "erro"; texto: string } | null>(null);

  useEffect(() => {
    async function carregarUsuario() {
      try {
        const dados = await buscarUsuarioAtual();
        if (!dados) {
          router.push("/login");
          return;
        }
        setUsuario(dados);
      } catch {
        setMensagem({ tipo: "erro", texto: "Erro ao carregar configurações." });
      } finally {
        setCarregando(false);
      }
    }
    carregarUsuario();
  }, [router]);

  async function verTutorialNovamente() {
    try {
      await atualizarFirstAccess(true);
      setMensagem({ tipo: "sucesso", texto: "Tutorial será exibido novamente no próximo acesso." });
      setUsuario((prev) => prev ? { ...prev, firstAccess: true } : null);
      router.push("/tutorial");
    } catch {
      setMensagem({ tipo: "erro", texto: "Erro ao reativar tutorial." });
    }
  }

  async function fazerLogout() {
    try {
      await logoutUsuario();
      router.push("/login");
    } catch {
      setMensagem({ tipo: "erro", texto: "Erro ao sair. Tente novamente." });
    }
  }

  return (
    <AppShell active="configuracoes">
      <div className="config-page">
        {carregando ? (
          <div className="config-carregando">
            <div className="spinner"></div>
            <p>Carregando...</p>
          </div>
        ) : usuario ? (
          <>
            <h1>Configurações</h1>

            <section className="config-section">
              <h2>Perfil</h2>
              <div className="perfil-info">
                <div className="avatar">
                  {usuario.avatarUrl ? (
                    <img src={usuario.avatarUrl} alt={usuario.nome} />
                  ) : (
                    <span>{usuario.nome.charAt(0).toUpperCase()}</span>
                  )}
                </div>
                <div className="perfil-detalhes">
                  <p className="perfil-nome">{usuario.nome}</p>
                  <p className="perfil-email">{usuario.email}</p>
                </div>
              </div>
            </section>

            <section className="config-section">
              <h2>Tutorial de Onboarding</h2>
              <div className="config-item">
                <div className="config-item-info">
                  <h3>Ver tutorial novamente</h3>
                  <p>Reexibe o tutorial das principais funcionalidades</p>
                </div>
                <button
                  className="btn-rever"
                  onClick={verTutorialNovamente}
                  disabled={usuario.firstAccess}
                >
                  {usuario.firstAccess ? "Tutorial ativo" : "Ver tutorial"}
                </button>
              </div>
              <p className="config-dica">
                {usuario.firstAccess
                  ? "O tutorial será exibido automaticamente no seu próximo acesso."
                  : "O tutorial já foi concluído. Clique acima para rever."}
              </p>
            </section>

            <section className="config-section danger">
              <h2>Conta</h2>
              <button className="btn-logout" onClick={fazerLogout}>
                Sair da conta
              </button>
            </section>
          </>
        ) : null}

        {mensagem && (
          <div className={`toast ${mensagem.tipo}`}>
            {mensagem.texto}
          </div>
        )}

        <style jsx>{`
          .config-page {
            position: absolute;
            inset: 0;
            overflow-y: auto;
            padding: 24px 22px 48px;
          }
          .config-carregando {
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 1rem;
            color: var(--mc-texto-2);
          }
          .spinner {
            width: 36px;
            height: 36px;
            border: 3px solid var(--mc-borda-2);
            border-top-color: var(--mc-teal);
            border-radius: 50%;
            animation: spin 1s linear infinite;
          }
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
          .config-page h1 {
            font-family: var(--mc-fonte-display);
            font-size: 22px;
            font-weight: 700;
            color: var(--mc-petroleo);
            margin: 0 0 20px;
          }
          .config-section {
            background: #fff;
            border: 1.5px solid var(--mc-borda);
            border-radius: 20px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            max-width: 460px;
          }
          .config-section.danger {
            border-color: var(--mc-erro-fundo);
          }
          .config-section h2 {
            font-size: 0.8rem;
            font-weight: 700;
            color: var(--mc-texto-2);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin: 0 0 1rem;
          }
          .perfil-info {
            display: flex;
            align-items: center;
            gap: 1rem;
          }
          .avatar {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--mc-teal), var(--mc-mint));
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            font-weight: 700;
            overflow: hidden;
            flex-shrink: 0;
          }
          .avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 50%;
          }
          .perfil-nome {
            font-weight: 700;
            color: var(--mc-petroleo);
            margin: 0 0 0.25rem;
          }
          .perfil-email {
            font-size: 0.875rem;
            color: var(--mc-texto-2);
            margin: 0;
          }
          .config-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
          }
          .config-item-info {
            min-width: 0;
          }
          .config-item-info h3 {
            font-size: 1rem;
            font-weight: 700;
            color: var(--mc-petroleo);
            margin: 0 0 0.25rem;
          }
          .config-item-info p {
            font-size: 0.875rem;
            color: var(--mc-texto-2);
            margin: 0;
          }
          .btn-rever {
            flex-shrink: 0;
            min-height: 44px;
            padding: 0.5rem 1rem;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
            background: var(--mc-teal);
            color: #fff;
            white-space: nowrap;
          }
          .btn-rever:hover:not(:disabled) {
            background: var(--mc-teal-escuro);
          }
          .btn-rever:disabled {
            background: var(--mc-borda-3);
            color: var(--mc-texto-2);
            cursor: not-allowed;
          }
          .config-dica {
            font-size: 0.8rem;
            color: var(--mc-texto-2);
            margin: 0.75rem 0 0;
          }
          .btn-logout {
            width: 100%;
            min-height: 44px;
            padding: 0.75rem 1rem;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid var(--mc-erro);
            background: #fff;
            color: var(--mc-erro);
          }
          .btn-logout:hover {
            background: var(--mc-erro-fundo);
          }
          .toast {
            position: fixed;
            bottom: 1.5rem;
            left: 50%;
            transform: translateX(-50%);
            padding: 0.875rem 1.5rem;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.9rem;
            box-shadow: var(--shadow, 0 10px 25px rgba(0, 0, 0, 0.15));
            animation: slideUp 0.3s ease;
            /* Acima da navegação inferior (var(--z-nav) = 1200 dentro do
               AppShell) — sem isso o toast nascia atrás da barra no mobile. */
            z-index: calc(var(--z-nav, 1200) + 10);
          }
          .toast.sucesso {
            background: var(--mc-sucesso);
            color: #fff;
          }
          .toast.erro {
            background: var(--mc-erro);
            color: #fff;
          }
          @keyframes slideUp {
            from { opacity: 0; transform: translateX(-50%) translateY(20px); }
            to { opacity: 1; transform: translateX(-50%) translateY(0); }
          }
        `}</style>
      </div>
    </AppShell>
  );
}
