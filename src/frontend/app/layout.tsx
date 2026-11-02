import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import RegistrarServiceWorker from "./RegistrarServiceWorker";
import SplashScreen from "./SplashScreen";
import "./globals.css";

// Identidade v3: Manrope para texto corrido, Sora para títulos e números.
// As fontes ficam no repositório (app/fonts) e não vêm do Google Fonts: o
// build da Vercel já falhou por o Google estar fora do ar (issue #234).
// `display: "swap"` evita tela em branco enquanto a fonte carrega — o app é
// usado na rua, em 4G, e texto com fonte de sistema é melhor que texto
// invisível.
const manrope = localFont({
  src: "./fonts/manrope-latin-wght-normal.woff2",
  weight: "200 800",
  variable: "--font-manrope",
  display: "swap",
});

const sora = localFont({
  src: "./fonts/sora-latin-wght-normal.woff2",
  weight: "100 800",
  variable: "--font-sora",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Movecity — Mobilidade Urbana Colaborativa",
  description: "Aplicativo de mobilidade urbana colaborativa para o DF",
  applicationName: "Movecity",
  // O link do manifesto é gerado pelo Next a partir de app/manifest.ts.
  appleWebApp: {
    capable: true,
    title: "Movecity",
    // A barra de status do iOS fica sobre o conteúdo. O layout já reserva
    // o espaço dela com env(safe-area-inset-top).
    statusBarStyle: "black-translucent",
  },
  // O ícone do iOS não é declarado aqui: no Next, o ícone por convenção de
  // arquivo (app/icon.png, app/apple-icon.png) sobrepõe o campo `icons` do
  // metadata, e a tag simplesmente não sai. Ele mora em app/apple-icon.png.
};

export const viewport: Viewport = {
  themeColor: "#0e2a3f",
  // Sem viewport-fit=cover o iOS devolve 0 em env(safe-area-inset-*), e o
  // respiro que a navegação e o herói reservam para o entalhe e para a
  // barra de gestos simplesmente não acontece.
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={`${manrope.variable} ${sora.variable}`}>
      <body>
        <SplashScreen />
        {children}
        <RegistrarServiceWorker />
      </body>
    </html>
  );
}
