import * as fs from "fs";
import * as path from "path";

/**
 * Guarda de acessibilidade (WCAG 2.2 AA) dos pares de cor da tela de rotas.
 *
 * O jsdom não calcula contraste: um texto ilegível passa em qualquer teste de
 * componente. Foi assim que o número da linha (branco sobre --mc-mint, 1,78:1)
 * chegou à produção. Este teste lê os tokens de verdade de globals.css e
 * trava a razão mínima de cada par que o card #179 corrigiu.
 */

const GLOBALS = fs.readFileSync(path.join(__dirname, "..", "globals.css"), "utf8");
const MAPA_CSS = fs.readFileSync(path.join(__dirname, "..", "mapa", "mapa.css"), "utf8");
const FAVORITOS_CSS = fs.readFileSync(
  path.join(__dirname, "..", "favoritos", "favoritos.css"),
  "utf8"
);

function token(nome: string): string {
  const achado = GLOBALS.match(new RegExp(`${nome}:\\s*(#[0-9a-fA-F]{6})\\b`));
  if (!achado) throw new Error(`Token ${nome} não encontrado (ou não é #rrggbb) em globals.css`);
  return achado[1];
}

function cor(valor: string): string {
  return valor.startsWith("--") ? token(valor) : valor;
}

function luminancia(hex: string): number {
  const [r, g, b] = [1, 3, 5]
    .map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function razao(a: string, b: string): number {
  const [x, y] = [luminancia(cor(a)), luminancia(cor(b))];
  const [claro, escuro] = x > y ? [x, y] : [y, x];
  return (claro + 0.05) / (escuro + 0.05);
}

const BRANCO = "#ffffff";

// [primeiro plano, fundo, razão mínima, onde é usado]
const PARES: [string, string, number, string][] = [
  [BRANCO, "--mc-petroleo", 4.5, "número da linha (.plan-badge-linha) — era mint, 1,78:1"],
  [BRANCO, "--mc-teal-escuro", 4.5, "botão 'Ver opções de ônibus' — era teal, 2,99:1"],
  ["--mc-sucesso-texto", "--mc-sucesso-fundo", 4.5, "selo 'ao vivo' — era 2,96:1"],
  ["--mc-alerta-texto", "--mc-alerta-fundo", 4.5, "botão de favorito salvo / selo pendente"],
  ["--mc-erro-texto", "--mc-erro-fundo", 4.5, "mensagens de erro — eram âmbar, 2,6:1"],
  ["--mc-texto-2", "--mc-areia-clara", 4.5, "texto secundário no cartão selecionado"],
  ["--mc-texto-2", BRANCO, 4.5, "selo de origem do dado (.selo-fonte) — fundo branco sólido"],
  ["--mc-sucesso-texto", BRANCO, 4.5, "selo 'ao vivo' (.selo-fonte.ao-vivo)"],
  [BRANCO, "--mc-embarque", 4.5, "número do passo de embarque (marcador azul)"],
  ["--mc-embarque", BRANCO, 4.5, "ícone/borda do passo de baldeação"],
  // componentes de interface e contornos: 3:1 (WCAG 1.4.11)
  ["--mc-borda-campo", BRANCO, 3, "borda dos campos de texto — era 1,15:1"],
  ["--mc-borda-campo", "--mc-areia-clara", 3, "borda do campo sobre o fundo do app"],
  ["--mc-teal-escuro", BRANCO, 3, "contorno de foco (outline) sobre branco"],
  ["--mc-teal-escuro", "--mc-areia-clara", 3, "contorno de foco sobre o fundo do app"],
];

describe("contraste dos tokens da tela de rotas (WCAG 2.2 AA)", () => {
  it.each(PARES)("%s sobre %s ≥ %s:1 — %s", (frente, fundo, minimo) => {
    expect(razao(frente, fundo)).toBeGreaterThanOrEqual(minimo);
  });

  it("a razão calculada bate com valores conhecidos (sanidade da função)", () => {
    expect(razao("#000000", "#ffffff")).toBeCloseTo(21, 0);
    // o par que provou o problema original
    expect(razao(BRANCO, "--mc-mint")).toBeLessThan(2);
  });
});

describe("escopo do CSS do botão de favorito (card #179)", () => {
  // O Next divide o CSS por rota: o que está em favoritos.css só existe em
  // /favoritos. As classes do botão são usadas pelo PlanejadorViagem, que
  // vive em /mapa — por isso o botão aparecia sem estilo. Teste de
  // componente (jsdom) não enxerga isso; este guarda enxerga.
  it.each([".plan-favorito-area", ".plan-favorito-btn", ".plan-favorito-erro"])(
    "%s está definido em mapa.css, onde o componente é usado",
    (seletor) => {
      expect(MAPA_CSS).toContain(seletor);
    }
  );

  it("favoritos.css não carrega mais as regras do botão do planejador", () => {
    expect(FAVORITOS_CSS).not.toContain(".plan-favorito");
  });
});
