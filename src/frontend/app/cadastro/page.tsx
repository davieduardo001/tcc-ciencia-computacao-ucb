"use client";

import { FormEvent, useState } from "react";
import LayoutAuth from "../LayoutAuth";
import CampoTexto from "../CampoTexto";
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
    <LayoutAuth ativa="cadastro" titulo={"Sua conta,\nem 1 minuto."}>
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <CampoTexto
          id="nome"
          label="Nome"
          placeholder="Nome completo"
          icone="pessoa"
          value={nome}
          onChange={setNome}
          erro={erros.nome}
          autoComplete="name"
        />

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
          placeholder="Criar senha"
          value={senha}
          onChange={setSenha}
          erro={erros.senha}
          autoComplete="new-password"
          medidorForca
        />

        <div className="campo-bloco">
          <label className="caixa-marcavel cartao-termos" htmlFor="termos">
            <input
              id="termos"
              type="checkbox"
              checked={termosAceitos}
              onChange={(e) => setTermosAceitos(e.target.checked)}
            />
            <span className="caixa-marca grande" aria-hidden="true">
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="3.4"
              >
                <path d="M5 13l4.5 4.5L19 7" />
              </svg>
            </span>
            Aceito os termos de uso
          </label>
          {erros.termos && <span className="erro-campo">{erros.termos}</span>}
        </div>

        {erros.geral && <p className="status-error">{erros.geral}</p>}
        {mensagemSucesso && (
          <p className="status-ok mensagem-sucesso">{mensagemSucesso}</p>
        )}

        <button
          type="submit"
          className="botao-primario acento"
          disabled={enviando}
        >
          {enviando ? "Cadastrando..." : "Cadastrar"}
        </button>
      </form>
    </LayoutAuth>
  );
}
