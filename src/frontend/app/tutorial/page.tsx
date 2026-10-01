"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Map, Search, Star, TriangleAlert } from "lucide-react";
import { atualizarFirstAccess, buscarUsuarioAtual } from "@/lib/api";

// Ícones em lucide-react, não emoji — mesmo sistema usado no resto do
// app (AppShell, mapa, /ocorrencias). Mapa/Ocorrências/Rotas salvas
// usam exatamente os mesmos ícones de app/mapa/AppShell.tsx, de
// propósito: é o mesmo conceito, deveria parecer a mesma coisa.
const ETAPAS = [
  {
    titulo: "Buscar Linhas",
    descricao: "Digite o número, nome ou destino da linha para ver trajetos, paradas e horários.",
    Icone: Search,
  },
  {
    titulo: "Visualizar no Mapa",
    descricao: "Veja o trajeto da linha, posições dos ônibus em tempo real e pontos de embarque mais próximos.",
    Icone: Map,
  },
  {
    titulo: "Reportar Ocorrência",
    descricao: "Ajude a comunidade reportando ônibus fantasma, atrasos, lotação ou problemas de segurança.",
    Icone: TriangleAlert,
  },
  {
    titulo: "Salvar Rota Favorita",
    descricao: "Marque suas linhas e rotas preferidas para receber alertas personalizados de chegada e atraso.",
    Icone: Star,
  },
];

export default function Tutorial() {
  const router = useRouter();
  const [etapaAtual, setEtapaAtual] = useState(0);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    async function verificarPrimeiroAcesso() {
      try {
        const usuario = await buscarUsuarioAtual();
        if (!usuario) {
          router.push("/login");
          return;
        }
        if (!usuario.firstAccess) {
          router.push("/mapa");
          return;
        }
      } catch {
        setErro("Não foi possível verificar seu acesso.");
      } finally {
        setCarregando(false);
      }
    }
    verificarPrimeiroAcesso();
  }, [router]);

  async function pularTutorial() {
    try {
      await atualizarFirstAccess(false);
      router.push("/mapa");
    } catch {
      setErro("Erro ao pular tutorial. Tente novamente.");
    }
  }

  async function concluirTutorial() {
    try {
      await atualizarFirstAccess(false);
      router.push("/mapa");
    } catch {
      setErro("Erro ao concluir tutorial. Tente novamente.");
    }
  }

  if (carregando) {
    return (
      <div className="tutorial-container loading">
        <div className="spinner"></div>
        <p>Carregando tutorial...</p>
      </div>
    );
  }

  if (erro) {
    return (
      <div className="tutorial-container error">
        <p className="status-error">{erro}</p>
        <button onClick={() => router.push("/mapa")}>Ir para o mapa</button>
      </div>
    );
  }

  const etapa = ETAPAS[etapaAtual];
  const isUltima = etapaAtual === ETAPAS.length - 1;

  return (
    <div className="tutorial-container">
      <div className="tutorial-card">
        <div className="tutorial-progress">
          {ETAPAS.map((_, i) => (
            <div
              key={i}
              className={`progress-dot ${i <= etapaAtual ? "active" : ""} ${i === etapaAtual ? "current" : ""}`}
            />
          ))}
        </div>

        <div className="tutorial-content">
          <div className="tutorial-icone">
            <etapa.Icone size={40} strokeWidth={1.8} />
          </div>
          <h2>{etapa.titulo}</h2>
          <p>{etapa.descricao}</p>
        </div>

        <div className="tutorial-actions">
          <button
            className="btn-pular"
            onClick={pularTutorial}
            disabled={carregando}
          >
            Pular
          </button>

          {isUltima ? (
            <button
              className="btn-concluir"
              onClick={concluirTutorial}
              disabled={carregando}
            >
              Começar
            </button>
          ) : (
            <button
              className="btn-proximo"
              onClick={() => setEtapaAtual(etapaAtual + 1)}
              disabled={carregando}
            >
              Próximo
            </button>
          )}
        </div>
      </div>

      <style jsx>{`
        .tutorial-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 1rem;
          background: linear-gradient(135deg, #f5f7fa 0%, #e4ecf5 100%);
        }
        .tutorial-container.loading,
        .tutorial-container.error {
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
        .tutorial-card {
          background: white;
          border-radius: 16px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
          padding: 2.5rem;
          max-width: 420px;
          width: 100%;
          text-align: center;
        }
        .tutorial-progress {
          display: flex;
          justify-content: center;
          gap: 0.5rem;
          margin-bottom: 1.5rem;
        }
        .progress-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #d1d5db;
          transition: all 0.3s ease;
        }
        .progress-dot.active {
          background: #2563eb;
        }
        .progress-dot.current {
          transform: scale(1.3);
          box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.2);
        }
        .tutorial-icone {
          display: flex;
          justify-content: center;
          color: #2563eb;
          margin-bottom: 1rem;
        }
        .tutorial-content h2 {
          font-size: 1.5rem;
          font-weight: 700;
          color: #111827;
          margin-bottom: 0.5rem;
        }
        .tutorial-content p {
          font-size: 1rem;
          color: #6b7280;
          line-height: 1.6;
        }
        .tutorial-actions {
          display: flex;
          justify-content: space-between;
          margin-top: 2rem;
          gap: 1rem;
        }
        .btn-pular,
        .btn-proximo,
        .btn-concluir {
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          font-weight: 600;
          font-size: 0.95rem;
          cursor: pointer;
          transition: all 0.2s;
          border: none;
          flex: 1;
        }
        .btn-pular {
          background: transparent;
          color: #6b7280;
          border: 1px solid #d1d5db;
        }
        .btn-pular:hover:not(:disabled) {
          background: #f3f4f6;
          color: #374151;
        }
        .btn-proximo,
        .btn-concluir {
          background: #2563eb;
          color: white;
        }
        .btn-proximo:hover:not(:disabled),
        .btn-concluir:hover:not(:disabled) {
          background: #1d4ed8;
        }
        .btn-pular:disabled,
        .btn-proximo:disabled,
        .btn-concluir:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}