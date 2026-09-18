"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import LayoutAuth from "../LayoutAuth";
import CampoTexto from "../CampoTexto";
import CampoSenha from "../CampoSenha";
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
  const [lembrar, setLembrar] = useState(true);
  const [avisoRecuperacao, setAvisoRecuperacao] = useState(false);
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
    <LayoutAuth ativa="login" titulo={"A cidade\nno seu tempo."}>
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <CampoTexto
          id="email"
          label="E-mail"
          icone="email"
          tipo="email"
          value={email}
          onChange={setEmail}
          erro={erros.email}
          autoComplete="email"
        />

        <CampoSenha
          id="senha"
          label="Senha"
          value={senha}
          onChange={setSenha}
          erro={erros.senha}
          autoComplete="current-password"
        />

        <div className="auth-opcoes">
          <label className="caixa-marcavel">
            <input
              type="checkbox"
              checked={lembrar}
              onChange={(e) => setLembrar(e.target.checked)}
            />
            <span className="caixa-marca" aria-hidden="true">
              <svg
                width="11"
                height="11"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="3.5"
              >
                <path d="M5 13l4.5 4.5L19 7" />
              </svg>
            </span>
            Lembrar de mim
          </label>

          <button
            type="button"
            className="auth-link-discreto"
            onClick={() => setAvisoRecuperacao(true)}
          >
            Esqueci a senha
          </button>
        </div>

        {avisoRecuperacao && (
          <p className="auth-aviso" role="status">
            A recuperação de senha ainda não está disponível no aplicativo — o
            serviço existe no backend, mas falta a rota no Gateway (US #13).
          </p>
        )}

        {erros.geral && <p className="status-error">{erros.geral}</p>}
        {mensagemSucesso && (
          <p className="status-ok mensagem-sucesso">{mensagemSucesso}</p>
        )}

        <button type="submit" className="botao-primario" disabled={enviando}>
          {enviando ? "Entrando..." : "Entrar"}
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            aria-hidden="true"
          >
            <path d="M5 12h13M13 6l6 6-6 6" />
          </svg>
        </button>
      </form>

      {vinculoPendente ? (
        <div className="vinculo-confirmacao">
          <p>
            Já existe uma conta com senha para{" "}
            <strong>{vinculoPendente.email}</strong>. Confirma vincular essa
            conta ao seu login do Google? Você poderá entrar com o Google a
            partir de agora.
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
        GOOGLE_CLIENT_ID && (
          <>
            <div className="divisor">
              <span>ou continue com</span>
            </div>
            <GoogleLoginButton
              clientId={GOOGLE_CLIENT_ID}
              onCredential={handleGoogleCredential}
              disabled={enviandoGoogle}
            />
          </>
        )
      )}
    </LayoutAuth>
  );
}
