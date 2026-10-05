import { render, screen, waitFor } from "@testing-library/react";
import StatusServicos from "../page";

describe("StatusServicos", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        service: "gateway",
        status: "ok",
        servicos: [
          { service: "gateway", status: "ok" },
          { service: "auth", status: "ok" },
          { service: "mobilidade", status: "ok" },
          { service: "colaboracao", status: "ok" },
        ],
      }),
    }) as jest.Mock;
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("deve renderizar o título Movecity", async () => {
    render(<StatusServicos />);
    expect(screen.getByText("Movecity")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText("Carregando...")).not.toBeInTheDocument();
    });
  });

  it("deve marcar serviço como Offline quando a resposta falha", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({ ok: false });

    render(<StatusServicos />);

    await waitFor(() => {
      expect(screen.getAllByText("Offline").length).toBeGreaterThan(0);
    });
  });
});
