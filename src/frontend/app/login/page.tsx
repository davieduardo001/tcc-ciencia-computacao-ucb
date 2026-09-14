"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  loginUsuario,
  LoginError,
  loginComGoogle,
  confirmarVinculoGoogle,
  decodificarIdTokenGoogle,
  GoogleLoginError,
} from "@/lib/api";
import GoogleLoginButton from "./GoogleLoginButton";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

interface Erros {
  email?: string;
  senha?: string;
  geral?: string;
}

interface VinculoPendente {
  idToken: string;
  email: string;
  googleId: string;
}

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erros, setErros] = useState<Erros>({});
  const [enviando, setEnviando] = useState(false);
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);
  const [enviandoGoogle, setEnviandoGoogle] = useState(false);
  const [vinculoPendente, setVinculoPendente] =
    useState<VinculoPendente | null>(null);

  function validar(): Erros {
    const novosErros: Erros = {};

    if (!email.trim()) {
      novosErros.email = "Campo obrigatório";
    } else if (!EMAIL_REGEX.test(email)) {
      novosErros.email = "E-mail inválido";
    }
    if (!senha.trim()) {
      novosErros.senha = "Campo obrigatório";
    }

    return novosErros;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setMensagemSucesso(null);

    const novosErros = validar();
    if (Object.keys(novosErros).length > 0) {
      setErros(novosErros);
      return;
    }

    setErros({});
    setEnviando(true);

    try {
      await loginUsuario({ email, senha });
      setMensagemSucesso("Login realizado com sucesso!");
      router.push("/mapa");
    } catch (err) {
      if (err instanceof LoginError) {
        setErros({ geral: err.message });
      } else {
        setErros({ geral: "Não foi possível realizar o login. Tente novamente." });
      }
    } finally {
      setEnviando(false);
    }
  }

  async function handleGoogleCredential(idToken: string) {
    setErros({});
    setMensagemSucesso(null);
    setEnviandoGoogle(true);

    try {
      const resposta = await loginComGoogle(idToken);

      if (resposta.account_linking_required) {
        const payload = decodificarIdTokenGoogle(idToken);
        setVinculoPendente({
          idToken,
          email: payload.email ?? "",
          googleId: payload.sub ?? "",
        });
        return;
      }

      setMensagemSucesso("Login realizado com sucesso!");
      router.push("/mapa");
    } catch (err) {
      if (err instanceof GoogleLoginError) {
        setErros({ geral: err.message });
      } else {
        setErros({ geral: "Não foi possível entrar com o Google. Tente novamente." });
      }
    } finally {
      setEnviandoGoogle(false);
    }
  }

  async function handleConfirmarVinculo() {
    if (!vinculoPendente) return;

    setErros({});
    setEnviandoGoogle(true);

    try {
      await confirmarVinculoGoogle(vinculoPendente);
      setVinculoPendente(null);
      setMensagemSucesso("Conta vinculada ao Google com sucesso!");
      router.push("/mapa");
    } catch (err) {
      if (err instanceof GoogleLoginError) {
        setErros({ geral: err.message });
      } else {
        setErros({ geral: "Não foi possível confirmar o vínculo com o Google." });
      }
    } finally {
      setEnviandoGoogle(false);
    }
  }

  return (
    <div className="container">
      <header>
        <h1>Entrar</h1>
        <p className="subtitle">Movecity — Mobilidade Urbana Colaborativa</p>
      </header>

      <main>
        <form className="form-cadastro" onSubmit={handleSubmit} noValidate>
          <div className="campo">
            <label htmlFor="email">E-mail</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            {erros.email && <span className="erro-campo">{erros.email}</span>}
          </div>

          <div className="campo">
            <label htmlFor="senha">Senha</label>
            <input
              id="senha"
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
            />
            {erros.senha && <span className="erro-campo">{erros.senha}</span>}
          </div>

          {erros.geral && <p className="status-error">{erros.geral}</p>}
          {mensagemSucesso && (
            <p className="status-ok mensagem-sucesso">{mensagemSucesso}</p>
          )}

          <button type="submit" disabled={enviando}>
            {enviando ? "Entrando..." : "Entrar"}
          </button>

          <p className="link-alternativo">
            Ainda não tem conta? <Link href="/cadastro">Cadastre-se</Link>
          </p>
        </form>

        {vinculoPendente ? (
          <div className="vinculo-confirmacao">
            <p>
              Já existe uma conta com senha para <strong>{vinculoPendente.email}</strong>.
              Confirma vincular essa conta ao seu login do Google? Você poderá
              entrar com o Google a partir de agora.
            </p>
            <button
              type="button"
              onClick={handleConfirmarVinculo}
              disabled={enviandoGoogle}
            >
              {enviandoGoogle ? "Vinculando..." : "Confirmar vínculo com o Google"}
            </button>
            <button
              type="button"
              className="botao-secundario"
              onClick={() => setVinculoPendente(null)}
              disabled={enviandoGoogle}
            >
              Cancelar
            </button>
          </div>
        ) : (
          <>
            <div className="divisor">
              <span>ou</span>
            </div>
            <GoogleLoginButton
              clientId={GOOGLE_CLIENT_ID}
              onCredential={handleGoogleCredential}
              disabled={enviandoGoogle}
            />
          </>
        )}
      </main>

      <footer>
        <p>Movecity — TCC Grupo Segurança UCB</p>
      </footer>
    </div>
  );
}