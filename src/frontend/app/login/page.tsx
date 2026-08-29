"use client";

import { useState } from "react";
import { useAuth } from "../components/AuthProvider";
import Link from "next/link";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro("");
    setCarregando(true);

    const resultado = await login(email, senha);

    if (!resultado.sucesso) {
      setErro(resultado.erro || "Erro ao fazer login");
    }

    setCarregando(false);
  };

  return (
    <div className="container">
      <header>
        <h1>Movecity</h1>
        <p className="subtitle">Entrar na sua conta</p>
      </header>

      <main>
        <form onSubmit={handleSubmit} className="form">
          {erro && <p className="erro">{erro}</p>}

          <div className="campo">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="campo">
            <label htmlFor="senha">Senha</label>
            <input
              id="senha"
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
            />
          </div>

          <button type="submit" disabled={carregando}>
            {carregando ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <p className="link">
          Não tem conta?{" "}
          <Link href="/registro">Criar conta</Link>
        </p>
      </main>
    </div>
  );
}
