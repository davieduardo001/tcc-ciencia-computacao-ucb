"use client";

import { FormEvent, Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import LayoutAuth from "../LayoutAuth";
import CampoSenha from "../CampoSenha";
import { redefinirSenha, RecuperacaoSenhaError } from "@/lib/api";

interface Erros {
  novaSenha?: string;
  confirmacaoSenha?: string;
  geral?: string;
}

function RedefinirSenhaConteudo() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [novaSenha, setNovaSenha] = useState("");
  const [confirmacaoSenha, setConfirmacaoSenha] = useState("");
  const [erros, setErros] = useState<Erros>({});
  const [enviando, setEnviando] = useState(false);
  const [sucesso, setSucesso] = useState(false);

  function validar(): Erros {
    const novosErros: Erros = {};

    if (!novaSenha) {
      novosErros.novaSenha = "Campo obrigatório";
    } else if (novaSenha.length < 8) {
      novosErros.novaSenha = "A senha deve ter no mínimo 8 caracteres";
    }

    if (!confirmacaoSenha) {
      novosErros.confirmacaoSenha = "Campo obrigatório";
    } else if (novaSenha !== confirmacaoSenha) {
      novosErros.confirmacaoSenha = "As senhas não coincidem";
    }

    return novosErros;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setErros({});
    setSucesso(false);

    const novosErros = validar();

    if (Object.keys(novosErros).length > 0) {
      setErros(novosErros);
      return;
    }

    if (!token) {
      setErros({
        geral: "Este link de redefinição não é mais válido ou está incompleto.",
      });
      return;
    }

    setEnviando(true);

    try {
      await redefinirSenha({
        token,
        novaSenha,
        confirmacaoSenha,
      });

      setSucesso(true);
      setNovaSenha("");
      setConfirmacaoSenha("");
    } catch (err) {
      if (err instanceof RecuperacaoSenhaError) {
        setErros({ geral: err.message });
      } else {
        setErros({
          geral: "Não foi possível redefinir a senha. Tente novamente.",
        });
      }
    } finally {
      setEnviando(false);
    }
  }

  if (!token) {
    return (
      <LayoutAuth
        ativa="login"
        titulo={"Link de\nredefinição."}
        mostrarAbas={false}
      >
        <div className="auth-form">
          <p className="status-error">
            Este link de redefinição não é mais válido ou está incompleto.
          </p>

          <p className="auth-texto-intro">
            Solicite uma nova recuperação de senha para receber outro link.
          </p>

          <Link
            href="/recuperar-senha"
            className="botao-primario acento"
          >
            Solicitar novo link
          </Link>
        </div>
      </LayoutAuth>
    );
  }

  if (sucesso) {
    return (
      <LayoutAuth
        ativa="login"
        titulo={"Senha\nredefinida."}
        mostrarAbas={false}
      >
        <div className="auth-form">
          <p className="status-ok mensagem-sucesso">
            Sua senha foi redefinida com sucesso.
          </p>

          <p className="auth-texto-intro">
            Agora você pode entrar no aplicativo usando sua nova senha.
          </p>

          <Link href="/login" className="botao-primario acento">
            Ir para o login
          </Link>
        </div>
      </LayoutAuth>
    );
  }

  return (
    <LayoutAuth
      ativa="login"
      titulo={"Crie uma\nnova senha."}
      mostrarAbas={false}
    >
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <p className="auth-texto-intro">
          Escolha uma nova senha para acessar sua conta.
        </p>

        <CampoSenha
          id="nova-senha"
          label="Nova senha"
          placeholder="Nova senha"
          value={novaSenha}
          onChange={setNovaSenha}
          erro={erros.novaSenha}
          autoComplete="new-password"
          medidorForca
        />

        <CampoSenha
          id="confirmacao-senha"
          label="Confirmar senha"
          placeholder="Confirmar senha"
          value={confirmacaoSenha}
          onChange={setConfirmacaoSenha}
          erro={erros.confirmacaoSenha}
          autoComplete="new-password"
        />

        {erros.geral && <p className="status-error">{erros.geral}</p>}

        <button
          type="submit"
          className="botao-primario acento"
          disabled={enviando}
        >
          {enviando ? "Redefinindo..." : "Redefinir senha"}
        </button>
      </form>
    </LayoutAuth>
  );
}

export default function RedefinirSenha() {
  return (
    <Suspense>
      <RedefinirSenhaConteudo />
    </Suspense>
  );
}
