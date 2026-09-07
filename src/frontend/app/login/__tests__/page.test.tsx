import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import Login from "../page";

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

describe("Login", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
    localStorage.clear();
  });

  afterEach(() => {
    jest.resetAllMocks();
    delete (window as unknown as { google?: unknown }).google;
  });

  function capturarCallbackGoogle(): (response: { credential: string }) => void {
    let callback: (response: { credential: string }) => void = () => {};
    window.google = {
      accounts: {
        id: {
          initialize: (config) => {
            callback = config.callback;
          },
          renderButton: jest.fn(),
        },
      },
    };
    return (...args) => callback(...args);
  }

  function preencherFormulario({
    email = "ana@example.com",
    senha = "senha123",
  } = {}) {
    fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: email } });
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: senha } });
  }

  it("realiza login com sucesso quando todos os campos são válidos", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: "token123",
        refresh_token: "refresh123",
        token_type: "bearer",
      }),
    });

    render(<Login />);
    preencherFormulario();
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      expect(
        screen.getByText("Login realizado com sucesso!")
      ).toBeInTheDocument();
    });
  });

  it("exibe 'Campo obrigatório' quando E-mail ou Senha estão vazios", async () => {
    render(<Login />);
    preencherFormulario({ email: "", senha: "" });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      expect(screen.getAllByText("Campo obrigatório").length).toBeGreaterThanOrEqual(2);
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("exibe 'E-mail inválido' quando o formato do e-mail é incorreto", async () => {
    render(<Login />);
    preencherFormulario({ email: "invalido", senha: "senha123" });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      expect(screen.getByText("E-mail inválido")).toBeInTheDocument();
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("exibe erro quando o backend retorna login inválido", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Usuário ou senha inválidos" }),
    });

    render(<Login />);
    preencherFormulario();
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      expect(screen.getByText("Usuário ou senha inválidos")).toBeInTheDocument();
    });
  });

  it("exibe link para a página de cadastro", () => {
    render(<Login />);
    const link = screen.getByRole("link", { name: "Cadastre-se" });
    expect(link).toHaveAttribute("href", "/cadastro");
  });

  it("bloqueia envio quando os campos não são preenchidos", async () => {
    render(<Login />);
    preencherFormulario({ email: "", senha: "" });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      expect(screen.getAllByText("Campo obrigatório").length).toBeGreaterThanOrEqual(2);
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("realiza login via Google com sucesso e redireciona pro mapa", async () => {
    const dispararCredencial = capturarCallbackGoogle();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: "token-google",
        refresh_token: "refresh-google",
        token_type: "bearer",
        account_linking_pending: false,
        account_linking_required: false,
      }),
    });

    render(<Login />);
    await act(async () => {
      dispararCredencial({ credential: "id-token-fake" });
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/auth/login/google"),
        expect.objectContaining({ method: "POST" })
      );
    });
    expect(localStorage.getItem("access_token")).toBe("token-google");
  });

  it("pede confirmação de vínculo quando o e-mail do Google já tem conta com senha", async () => {
    const dispararCredencial = capturarCallbackGoogle();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: "",
        refresh_token: "",
        token_type: "bearer",
        account_linking_pending: true,
        account_linking_required: true,
      }),
    });

    render(<Login />);
    // header.payload.signature — payload é {"email":"ana@example.com","sub":"google-123"} em base64url
    const payload = btoa(JSON.stringify({ email: "ana@example.com", sub: "google-123" }));
    await act(async () => {
      dispararCredencial({ credential: `header.${payload}.signature` });
    });

    await waitFor(() => {
      expect(
        screen.getByText(/Já existe uma conta com senha para/)
      ).toBeInTheDocument();
    });
    expect(screen.getByText("ana@example.com")).toBeInTheDocument();
  });

  it("confirma o vínculo com o Google e redireciona pro mapa", async () => {
    const dispararCredencial = capturarCallbackGoogle();
    const payload = btoa(JSON.stringify({ email: "ana@example.com", sub: "google-123" }));

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          access_token: "",
          refresh_token: "",
          token_type: "bearer",
          account_linking_pending: true,
          account_linking_required: true,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          access_token: "token-vinculado",
          refresh_token: "refresh-vinculado",
          token_type: "bearer",
          account_linking_pending: false,
          account_linking_required: false,
        }),
      });

    render(<Login />);
    await act(async () => {
      dispararCredencial({ credential: `header.${payload}.signature` });
    });

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Confirmar vínculo com o Google" })
      ).toBeInTheDocument();
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Confirmar vínculo com o Google" })
    );

    await waitFor(() => {
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining("/api/auth/link-google/confirmar"),
        expect.objectContaining({ method: "POST" })
      );
    });
    expect(localStorage.getItem("access_token")).toBe("token-vinculado");
  });

  it("exibe erro quando o login via Google falha", async () => {
    const dispararCredencial = capturarCallbackGoogle();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Token Google inválido" }),
    });

    render(<Login />);
    await act(async () => {
      dispararCredencial({ credential: "id-token-invalido" });
    });

    await waitFor(() => {
      expect(screen.getByText("Token Google inválido")).toBeInTheDocument();
    });
  });
});