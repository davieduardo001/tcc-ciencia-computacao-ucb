"use client";

import { FormEvent, useState } from "react";
import Image from "next/image";
import AbasAuth from "../AbasAuth";
import CampoSenha from "../CampoSenha";
import { registrarUsuario, RegistroError } from "@/lib/api";

const SENHA_REGEX = /^(?=.*[A-Za-z])(?=.*\d).{8,}$/;

interface Erros {
  nome?: string;
  email?: string;
  senha?: string;
  termos?: string;
  geral?: string;
}

export default function Cadastro() {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [termosAceitos, setTermosAceitos] = useState(false);
  const [erros, setErros] = useState<Erros>({});
  const [enviando, setEnviando] = useState(false);
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);

  function validar(): Erros {
    const novosErros: Erros = {};

    if (!nome.trim()) {
      novosErros.nome = "Campo obrigatório";
    }
    if (!email.trim()) {
      novosErros.email = "Campo obrigatório";
    }
    if (senha && !SENHA_REGEX.test(senha)) {
      novosErros.senha =
        "A senha deve ter ao menos 8 caracteres, incluindo letras e números";
    }
    if (!termosAceitos) {
      novosErros.termos = "Você deve aceitar os termos de uso";
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
      await registrarUsuario({ nome, email, senha, termosAceitos });
      setMensagemSucesso("Verifique seu e-mail para confirmar a conta.");
      setNome("");
      setEmail("");
      setSenha("");
      setTermosAceitos(false);
    } catch (err) {
      if (err instanceof RegistroError && err.message.includes("em uso")) {
        setErros({ email: err.message });
      } else {
        setErros({ geral: "Não foi possível concluir o cadastro. Tente novamente." });
      }
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="container tela-auth">
      <header>
        <div className="marca">
          <span className="marca-simbolo">
            <Image
              src="/movecity-icon.png"
              alt=""
              width={32}
              height={32}
              priority
            />
          </span>
          <span className="marca-texto">
            <strong>MoveCity</strong>
            <small>Mobilidade DF</small>
          </span>
        </div>
        <h1>Criar conta</h1>
        <p className="subtitle">Sua conta, em 1 minuto.</p>
      </header>

      <main>
        <AbasAuth ativa="cadastro" />

        <form className="form-cadastro" onSubmit={handleSubmit} noValidate>
          <div className="campo">
            <label htmlFor="nome">Nome</label>
            <input
              id="nome"
              type="text"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
            />
            {erros.nome && <span className="erro-campo">{erros.nome}</span>}
          </div>

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

          <CampoSenha
            id="senha"
            label="Senha"
            value={senha}
            onChange={setSenha}
            erro={erros.senha}
            autoComplete="new-password"
            medidorForca
          />

          <div className="campo campo-checkbox">
            <label htmlFor="termos">
              <input
                id="termos"
                type="checkbox"
                checked={termosAceitos}
                onChange={(e) => setTermosAceitos(e.target.checked)}
              />
              Aceito os termos de uso
            </label>
            {erros.termos && <span className="erro-campo">{erros.termos}</span>}
          </div>

          {erros.geral && <p className="status-error">{erros.geral}</p>}
          {mensagemSucesso && (
            <p className="status-ok mensagem-sucesso">{mensagemSucesso}</p>
          )}

          <button type="submit" disabled={enviando}>
            {enviando ? "Cadastrando..." : "Cadastrar"}
          </button>

        </form>
      </main>

      <footer>
        <p>Movecity — TCC Grupo Segurança UCB</p>
      </footer>
    </div>
  );
}
