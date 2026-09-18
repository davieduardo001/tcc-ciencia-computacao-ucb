import type { Metadata, Viewport } from "next";
import { Manrope, Sora } from "next/font/google";
import "./globals.css";

// Identidade v3: Manrope para texto corrido, Sora para títulos e números.
// `display: "swap"` evita tela em branco enquanto a fonte carrega — o app é
// usado na rua, em 4G, e texto com fonte de sistema é melhor que texto
// invisível.
const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-manrope",
  display: "swap",
});

const sora = Sora({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-sora",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Movecity — Mobilidade Urbana Colaborativa",
  description: "Aplicativo de mobilidade urbana colaborativa para o DF",
};

export const viewport: Viewport = {
  themeColor: "#0e2a3f",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={`${manrope.variable} ${sora.variable}`}>
      <body>{children}</body>
    </html>
  );
}
