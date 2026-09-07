import { render, screen } from "@testing-library/react";
import GoogleLoginButton from "../GoogleLoginButton";

describe("GoogleLoginButton", () => {
  afterEach(() => {
    delete (window as unknown as { google?: unknown }).google;
    jest.resetAllMocks();
  });

  it("não renderiza nada quando não há clientId configurado", () => {
    render(<GoogleLoginButton onCredential={jest.fn()} />);
    expect(screen.queryByTestId("google-login-button")).not.toBeInTheDocument();
  });

  it("inicializa e renderiza o botão do Google quando o script já está carregado", () => {
    const initialize = jest.fn();
    const renderButton = jest.fn();
    window.google = { accounts: { id: { initialize, renderButton } } };

    render(
      <GoogleLoginButton clientId="client-id-teste" onCredential={jest.fn()} />
    );

    expect(screen.getByTestId("google-login-button")).toBeInTheDocument();
    expect(initialize).toHaveBeenCalledWith(
      expect.objectContaining({ client_id: "client-id-teste" })
    );
    expect(renderButton).toHaveBeenCalled();
  });

  it("chama onCredential com o id_token recebido do Google", () => {
    const onCredential = jest.fn();
    let callbackCapturada: ((response: { credential: string }) => void) | undefined;

    window.google = {
      accounts: {
        id: {
          initialize: ({ callback }) => {
            callbackCapturada = callback;
          },
          renderButton: jest.fn(),
        },
      },
    };

    render(<GoogleLoginButton clientId="client-id-teste" onCredential={onCredential} />);

    callbackCapturada?.({ credential: "id-token-fake" });

    expect(onCredential).toHaveBeenCalledWith("id-token-fake");
  });
});
