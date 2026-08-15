import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Movecity — Mobilidade Urbana Colaborativa",
  description: "Aplicativo de mobilidade urbana colaborativa para o DF",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
