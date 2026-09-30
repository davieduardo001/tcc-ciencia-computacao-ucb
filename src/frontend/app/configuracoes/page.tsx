"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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

  if (carregando) {
    return (
      <div className="config-container loading">
        <div className="spinner"></div>
        <p>Carregando...</p>
      </div>
    );
  }

  if (!usuario) {
    return null;
  }

  return (
    <div className="config-container">
      <header className="config-header">
        <h1>Configurações</h1>
      </header>

      <main className="config-main">
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
      </main>

      {mensagem && (
        <div className={`toast ${mensagem.tipo}`}>
          {mensagem.texto}
        </div>
      )}

      <style jsx>{`
        .config-container {
          min-height: 100vh;
          background: #f9fafb;
        }
        .config-container.loading {
          display: flex;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          gap: 1rem;
        }
        .spinner {
          width: 40px;
          height: 40px;
          border: 3px solid #e0e0e0;
          border-top-color: #2563eb;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .config-header {
          padding: 1.5rem 1rem;
          border-bottom: 1px solid #e5e7eb;
          background: white;
        }
        .config-header h1 {
          font-size: 1.25rem;
          font-weight: 700;
          color: #111827;
        }
        .config-main {
          padding: 1.5rem 1rem;
          max-width: 500px;
          margin: 0 auto;
        }
        .config-section {
          background: white;
          border-radius: 12px;
          padding: 1.25rem;
          margin-bottom: 1rem;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        .config-section.danger {
          border: 1px solid #fee2e2;
        }
        .config-section h2 {
          font-size: 0.875rem;
          font-weight: 600;
          color: #6b7280;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 1rem;
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
          background: linear-gradient(135deg, #2563eb, #3b82f6);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5rem;
          font-weight: 700;
          overflow: hidden;
        }
        .avatar img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          border-radius: 50%;
        }
        .perfil-nome {
          font-weight: 600;
          color: #111827;
          margin: 0 0 0.25rem;
        }
        .perfil-email {
          font-size: 0.875rem;
          color: #6b7280;
          margin: 0;
        }
        .config-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
        }
        .config-item-info h3 {
          font-size: 1rem;
          font-weight: 600;
          color: #111827;
          margin: 0 0 0.25rem;
        }
        .config-item-info p {
          font-size: 0.875rem;
          color: #6b7280;
          margin: 0;
        }
        .btn-rever {
          padding: 0.5rem 1rem;
          border-radius: 8px;
          font-weight: 600;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s;
          border: none;
          background: #2563eb;
          color: white;
          white-space: nowrap;
        }
        .btn-rever:hover:not(:disabled) {
          background: #1d4ed8;
        }
        .btn-rever:disabled {
          background: #9ca3af;
          cursor: not-allowed;
        }
        .config-dica {
          font-size: 0.8rem;
          color: #9ca3af;
          margin: 0.75rem 0 0;
        }
        .btn-logout {
          width: 100%;
          padding: 0.75rem 1rem;
          border-radius: 8px;
          font-weight: 600;
          font-size: 0.95rem;
          cursor: pointer;
          transition: all 0.2s;
          border: 1px solid #ef4444;
          background: white;
          color: #ef4444;
        }
        .btn-logout:hover {
          background: #fef2f2;
        }
        .toast {
          position: fixed;
          bottom: 1.5rem;
          left: 50%;
          transform: translateX(-50%);
          padding: 0.875rem 1.5rem;
          border-radius: 8px;
          font-weight: 500;
          font-size: 0.9rem;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
          animation: slideUp 0.3s ease;
          z-index: 100;
        }
        .toast.sucesso {
          background: #059669;
          color: white;
        }
        .toast.erro {
          background: #dc2626;
          color: white;
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateX(-50%) translateY(20px); }
          to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
      `}</style>
    </div>
  );
}