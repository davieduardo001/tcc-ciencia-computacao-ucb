import { render, screen, waitFor } from "@testing-library/react";
import Home from "../page";

describe("Home", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ service: "gateway", status: "ok" }),
    }) as jest.Mock;
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("deve renderizar o título Movecity", async () => {
    render(<Home />);
    expect(screen.getByText("Movecity")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText("Carregando...")).not.toBeInTheDocument();
    });
  });

  it("deve marcar serviço como Offline quando a resposta falha", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({ ok: false });

    render(<Home />);

    await waitFor(() => {
      expect(screen.getAllByText("Offline").length).toBeGreaterThan(0);
    });
  });
});
