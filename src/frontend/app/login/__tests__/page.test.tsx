import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import Login from "../page";

describe("Login", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
    localStorage.clear();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

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

  it("bloqueia envio quando os campos não são preenchidos", async () => {
    render(<Login />);
    preencherFormulario({ email: "", senha: "" });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      expect(screen.getAllByText("Campo obrigatório").length).toBeGreaterThanOrEqual(2);
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });
});