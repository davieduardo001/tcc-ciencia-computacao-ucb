"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { loginUsuario, LoginError } from "@/lib/api";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface Erros {
  email?: string;
  senha?: string;
  geral?: string;
}

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erros, setErros] = useState<Erros>({});
  const [enviando, setEnviando] = useState(false);
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);

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
      </main>

      <footer>
        <p>Movecity — TCC Grupo Segurança UCB</p>
      </footer>
    </div>
  );
}