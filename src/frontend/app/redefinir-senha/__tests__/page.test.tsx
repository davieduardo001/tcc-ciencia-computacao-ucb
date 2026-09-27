import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { redefinirSenha } from "../../../lib/api";
import RedefinirSenhaPage from "../page";

jest.mock("../../../lib/api", () => ({
  redefinirSenha: jest.fn(),
  RecuperacaoSenhaError: class RecuperacaoSenhaError extends Error {},
}));

jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) {
    return <a href={href}>{children}</a>;
  };
});

jest.mock("next/navigation", () => ({
  useSearchParams: jest.fn(),
}));

import { useSearchParams } from "next/navigation";

describe("Página de redefinição de senha — US #133", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("exibe estado de link inválido quando não existe token", () => {
    (useSearchParams as jest.Mock).mockReturnValue({
      get: () => null,
    });

    render(<RedefinirSenhaPage />);

    expect(
      screen.getByText(/Este link de redefinição não é mais válido/i)
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", { name: /solicitar novo link/i })
    ).toHaveAttribute("href", "/recuperar-senha");
  });

  it("exibe o formulário quando existe token", () => {
    (useSearchParams as jest.Mock).mockReturnValue({
      get: (nome: string) => (nome === "token" ? "token-teste" : null),
    });

    render(<RedefinirSenhaPage />);

    expect(
      screen.getByText(/crie uma nova senha/i)
    ).toBeInTheDocument();

    expect(
      screen.getByLabelText(/nova senha/i)
    ).toBeInTheDocument();

    expect(
      screen.getByLabelText(/confirmar senha/i)
    ).toBeInTheDocument();
  });

  it("não envia quando as senhas são diferentes", async () => {
    (useSearchParams as jest.Mock).mockReturnValue({
      get: () => "token-teste",
    });

    render(<RedefinirSenhaPage />);

    fireEvent.change(screen.getByLabelText(/nova senha/i), {
      target: { value: "NovaSenha123!" },
    });

    fireEvent.change(screen.getByLabelText(/confirmar senha/i), {
      target: { value: "SenhaDiferente123!" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: /redefinir senha/i })
    );

    expect(redefinirSenha).not.toHaveBeenCalled();

    expect(
      screen.getByText(/senhas não coincidem/i)
    ).toBeInTheDocument();
  });

  it("envia o token e as senhas para a API", async () => {
    (useSearchParams as jest.Mock).mockReturnValue({
      get: () => "token-teste",
    });

    (redefinirSenha as jest.Mock).mockResolvedValue({
      mensagem: "Senha redefinida com sucesso.",
    });

    render(<RedefinirSenhaPage />);

    fireEvent.change(screen.getByLabelText(/nova senha/i), {
      target: { value: "NovaSenha123!" },
    });

    fireEvent.change(screen.getByLabelText(/confirmar senha/i), {
      target: { value: "NovaSenha123!" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: /redefinir senha/i })
    );

    await waitFor(() => {
      expect(redefinirSenha).toHaveBeenCalledWith({
        token: "token-teste",
        novaSenha: "NovaSenha123!",
        confirmacaoSenha: "NovaSenha123!",
      });
    });
  });

  it("exibe caminho para o login após redefinir a senha", async () => {
    (useSearchParams as jest.Mock).mockReturnValue({
      get: () => "token-teste",
    });

    (redefinirSenha as jest.Mock).mockResolvedValue({
      mensagem: "Senha redefinida com sucesso.",
    });

    render(<RedefinirSenhaPage />);

    fireEvent.change(screen.getByLabelText(/nova senha/i), {
      target: { value: "NovaSenha123!" },
    });

    fireEvent.change(screen.getByLabelText(/confirmar senha/i), {
      target: { value: "NovaSenha123!" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: /redefinir senha/i })
    );

    const link = await screen.findByRole("link", {
      name: /ir para o login/i,
    });

    expect(link).toHaveAttribute("href", "/login");
  });
});
