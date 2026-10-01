import { act, render } from "@testing-library/react";
import SplashScreen from "../SplashScreen";

function mockMatchMedia(reduzMovimento: boolean) {
  window.matchMedia = jest.fn().mockImplementation((query: string) => ({
    matches: reduzMovimento,
    media: query,
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  }));
}

describe("SplashScreen", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("mostra a splash (grade, traçado e marca) quando o usuário não pediu menos movimento", () => {
    mockMatchMedia(false);
    const { container } = render(<SplashScreen />);

    expect(container.querySelector(".splash")).toBeInTheDocument();
    expect(container.querySelector(".splash-tracado")).toBeInTheDocument();
    expect(container.querySelector(".splash-marca")).toBeInTheDocument();
  });

  it("some sozinha depois da duração total da animação", () => {
    mockMatchMedia(false);
    const { container } = render(<SplashScreen />);

    act(() => {
      jest.advanceTimersByTime(2600);
    });

    expect(container.querySelector(".splash")).not.toBeInTheDocument();
  });

  it("não renderiza nada quando prefers-reduced-motion está ativo", () => {
    mockMatchMedia(true);
    const { container } = render(<SplashScreen />);

    expect(container.querySelector(".splash")).not.toBeInTheDocument();
  });
});
