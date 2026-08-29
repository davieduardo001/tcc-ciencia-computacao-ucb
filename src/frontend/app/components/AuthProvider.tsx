"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { Usuario, buscarUsuarioLogado, logout as logoutApi } from "@/lib/auth";
import { useRouter } from "next/navigation";

interface AuthContextType {
  usuario: Usuario | null;
  carregando: boolean;
  login: (email: string, senha: string) => Promise<{ sucesso: boolean; erro?: string }>;
  logout: () => Promise<void>;
  recarregarUsuario: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregando, setCarregando] = useState(true);
  const router = useRouter();

  const recarregarUsuario = async () => {
    const user = await buscarUsuarioLogado();
    setUsuario(user);
  };

  useEffect(() => {
    recarregarUsuario().finally(() => setCarregando(false));
  }, []);

  const login = async (
    email: string,
    senha: string
  ): Promise<{ sucesso: boolean; erro?: string }> => {
    const { login: loginApi } = await import("@/lib/auth");
    const resultado = await loginApi(email, senha);

    if (resultado.sucesso) {
      await recarregarUsuario();
      router.push("/");
    }

    return resultado;
  };

  const logout = async () => {
    await logoutApi();
    setUsuario(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{ usuario, carregando, login, logout, recarregarUsuario }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider");
  }
  return context;
}
