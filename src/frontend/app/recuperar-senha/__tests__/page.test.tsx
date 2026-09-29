import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { solicitarResetSenha } from "../../../lib/api";
import RecuperarSenhaPage from "../page";

jest.mock("../../../lib/api", () => ({
  solicitarResetSenha: jest.fn(),
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

describe("Página de recuperação de senha — US #133", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("exibe o formulário de recuperação", () => {
    render(<RecuperarSenhaPage />);

    expect(
      screen.getByText(/Recupere sua senha/i)
    ).toBeInTheDocument();

    expect(
      screen.getByLabelText(/e-mail/i)
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: /enviar link/i })
    ).toBeInTheDocument();
  });

  it("não envia quando o e-mail está vazio", async () => {
    render(<RecuperarSenhaPage />);

    fireEvent.click(
      screen.getByRole("button", { name: /enviar link/i })
    );

    expect(solicitarResetSenha).not.toHaveBeenCalled();
  });

  it("solicita a recuperação e exibe a confirmação", async () => {
    (solicitarResetSenha as jest.Mock).mockResolvedValue({
      mensagem:
        "Se o e-mail estiver cadastrado, voce recebera um link de redefinicao.",
    });

    render(<RecuperarSenhaPage />);

    fireEvent.change(screen.getByLabelText(/e-mail/i), {
      target: { value: "teste@example.com" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: /enviar link/i })
    );

    await waitFor(() => {
      expect(solicitarResetSenha).toHaveBeenCalledWith(
        "teste@example.com"
      );
    });

    expect(
      screen.getByText(/Se o e-mail estiver cadastrado/i)
    ).toBeInTheDocument();

    expect(
      screen.getByText(/Verifique sua caixa de entrada/i)
    ).toBeInTheDocument();
  });

  it("exibe mensagem amigável quando a API retorna erro", async () => {
    (solicitarResetSenha as jest.Mock).mockRejectedValue(
  new (require("../../../lib/api").RecuperacaoSenhaError)(
    "Muitas solicitações. Tente novamente mais tarde."
  )
);

    render(<RecuperarSenhaPage />);

    fireEvent.change(screen.getByLabelText(/e-mail/i), {
      target: { value: "teste@example.com" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: /enviar link/i })
    );

    await waitFor(() => {
      expect(
        screen.getByText(/Muitas solicitações/i)
      ).toBeInTheDocument();
    });
  });

  it("possui caminho para voltar ao login após a solicitação", async () => {
    (solicitarResetSenha as jest.Mock).mockResolvedValue({
      mensagem:
        "Se o e-mail estiver cadastrado, voce recebera um link de redefinicao.",
    });

    render(<RecuperarSenhaPage />);

    fireEvent.change(screen.getByLabelText(/e-mail/i), {
      target: { value: "teste@example.com" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: /enviar link/i })
    );

    const link = await screen.findByRole("link", {
      name: /voltar para o login/i,
    });

    expect(link).toHaveAttribute("href", "/login");
  });
});

