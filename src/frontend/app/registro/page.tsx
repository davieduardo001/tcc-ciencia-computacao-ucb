"use client";

import { useState } from "react";
import { registrar } from "@/lib/auth";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function RegistroPage() {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro("");
    setCarregando(true);

    const resultado = await registrar(nome, email, senha);

    if (resultado.sucesso) {
      setSucesso(true);
      setTimeout(() => router.push("/login"), 2000);
    } else {
      setErro(resultado.erro || "Erro ao criar conta");
    }

    setCarregando(false);
  };

  return (
    <div className="container">
      <header>
        <h1>Movecity</h1>
        <p className="subtitle">Criar nova conta</p>
      </header>

      <main>
        {sucesso ? (
          <p className="sucesso">Conta criada com sucesso! Redirecionando...</p>
        ) : (
          <form onSubmit={handleSubmit} className="form">
            {erro && <p className="erro">{erro}</p>}

            <div className="campo">
              <label htmlFor="nome">Nome</label>
              <input
                id="nome"
                type="text"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                required
              />
            </div>

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
                minLength={6}
              />
            </div>

            <button type="submit" disabled={carregando}>
              {carregando ? "Criando..." : "Criar conta"}
            </button>
          </form>
        )}

        <p className="link">
          Já tem conta?{" "}
          <Link href="/login">Fazer login</Link>
        </p>
      </main>
    </div>
  );
}
