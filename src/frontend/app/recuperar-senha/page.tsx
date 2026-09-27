"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import LayoutAuth from "../LayoutAuth";
import CampoTexto from "../CampoTexto";
import { solicitarResetSenha, RecuperacaoSenhaError } from "@/lib/api";

interface Erros {
  email?: string;
  geral?: string;
}

export default function RecuperarSenha() {
  const [email, setEmail] = useState("");
  const [erros, setErros] = useState<Erros>({});
  const [enviando, setEnviando] = useState(false);
  const [enviado, setEnviado] = useState(false);

  function validar(): Erros {
    const novosErros: Erros = {};

    if (!email.trim()) {
      novosErros.email = "Campo obrigatório";
    }

    return novosErros;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setEnviado(false);
    setErros({});

    const novosErros = validar();

    if (Object.keys(novosErros).length > 0) {
      setErros(novosErros);
      return;
    }

    setEnviando(true);

    try {
      await solicitarResetSenha(email.trim());
      setEnviado(true);
    } catch (err) {
      if (err instanceof RecuperacaoSenhaError) {
        setErros({ geral: err.message });
      } else {
        setErros({
          geral: "Não foi possível solicitar a recuperação. Tente novamente.",
        });
      }
    } finally {
      setEnviando(false);
    }
  }

  return (
    <LayoutAuth
      ativa="login"
      titulo={"Recupere\nsua senha."}
      mostrarAbas={false}
    >
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        {!enviado ? (
          <>
            <p className="auth-texto-intro">
              Informe seu e-mail e enviaremos um link para você criar uma nova
              senha.
            </p>

            <CampoTexto
              id="email"
              label="E-mail"
              placeholder="Seu e-mail"
              icone="email"
              tipo="email"
              value={email}
              onChange={setEmail}
              erro={erros.email}
              autoComplete="email"
            />

            {erros.geral && <p className="status-error">{erros.geral}</p>}

            <button
              type="submit"
              className="botao-primario acento"
              disabled={enviando}
            >
              {enviando ? "Enviando..." : "Enviar link de recuperação"}
            </button>
          </>
        ) : (
          <>
            <p className="status-ok mensagem-sucesso">
              Se o e-mail estiver cadastrado, você receberá um link de
              redefinição.
            </p>

            <p className="auth-texto-intro">
              Verifique sua caixa de entrada e siga as instruções para criar
              uma nova senha.
            </p>

            <Link href="/login" className="botao-primario acento">
              Voltar para o login
            </Link>
          </>
        )}
      </form>
    </LayoutAuth>
  );
}
