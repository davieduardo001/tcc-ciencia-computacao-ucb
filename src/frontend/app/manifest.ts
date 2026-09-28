import type { MetadataRoute } from "next";

/**
 * Manifesto do PWA.
 *
 * `start_url` é `/mapa`, não `/`: a home do aplicativo é o mapa — é para
 * lá que o login redireciona e é ali que fica a navegação. Quem instala o
 * app e toca no ícone quer ver onde está o ônibus, não a tela de status
 * dos serviços.
 */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Movecity — Mobilidade Urbana Colaborativa",
    short_name: "Movecity",
    description:
      "Rastreie ônibus do DF em tempo real, com dados oficiais da SEMOB e reportes de outros passageiros.",
    lang: "pt-BR",
    start_url: "/mapa",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    // Cor da tela de abertura e da barra do sistema: o petróleo da marca.
    background_color: "#07212c",
    theme_color: "#0e2a3f",
    categories: ["travel", "navigation", "utilities"],
    icons: [
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      // Maskable tem a marca dentro da zona segura (60% do quadro), porque
      // o Android recorta o ícone no formato do sistema — em aparelho que
      // usa máscara circular, um ícone sem essa folga perde as bordas.
      {
        src: "/icons/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
