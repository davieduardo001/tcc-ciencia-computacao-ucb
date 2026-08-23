import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import Cadastro from "../page";

describe("Cadastro", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  function preencherFormulario({
    nome = "Ana Passageira",
    email = "ana@example.com",
    senha = "senha123",
    aceitarTermos = true,
  } = {}) {
    fireEvent.change(screen.getByLabelText("Nome"), { target: { value: nome } });
    fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: email } });
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: senha } });
    if (aceitarTermos) {
      fireEvent.click(screen.getByLabelText(/Aceito os termos/));
    }
  }

  it("cadastra com sucesso quando todos os campos são válidos", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({
        id: "1",
        nome: "Ana Passageira",
        email: "ana@example.com",
        mensagem: "Verifique seu e-mail para confirmar a conta.",
      }),
    });

    render(<Cadastro />);
    preencherFormulario();
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    await waitFor(() => {
      expect(
        screen.getByText("Verifique seu e-mail para confirmar a conta.")
      ).toBeInTheDocument();
    });
  });

  it("exibe 'Campo obrigatório' quando Nome ou E-mail estão vazios", async () => {
    render(<Cadastro />);
    preencherFormulario({ nome: "", email: "" });
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    await waitFor(() => {
      expect(screen.getAllByText("Campo obrigatório").length).toBeGreaterThanOrEqual(2);
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("informa e-mail já em uso quando o backend retorna 409", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ detail: "Este e-mail já está em uso." }),
    });

    render(<Cadastro />);
    preencherFormulario();
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    await waitFor(() => {
      expect(screen.getByText("Este e-mail já está em uso.")).toBeInTheDocument();
    });
  });

  it("exibe alerta quando a senha não atende aos critérios de complexidade", async () => {
    render(<Cadastro />);
    preencherFormulario({ senha: "abcdefgh" });
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    await waitFor(() => {
      expect(
        screen.getByText(
          "A senha deve ter ao menos 8 caracteres, incluindo letras e números"
        )
      ).toBeInTheDocument();
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("bloqueia envio quando os termos de uso não são aceitos", async () => {
    render(<Cadastro />);
    preencherFormulario({ aceitarTermos: false });
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    await waitFor(() => {
      expect(screen.getByText("Você deve aceitar os termos de uso")).toBeInTheDocument();
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });
});
