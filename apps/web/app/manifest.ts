import { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "WareFlow Wholesale WMS",
    short_name: "WareFlow",
    description: "Agentic B2B FMCG Wholesale Warehouse Management & Floor Operations",
    start_url: "/dashboard",
    display: "standalone",
    background_color: "#090d16",
    theme_color: "#8b5cf6",
    orientation: "portrait-primary",
    icons: [
      {
        src: "/icon.svg",
        sizes: "512x512",
        type: "image/svg+xml",
        purpose: "maskable",
      },
      {
        src: "/wareflow-logo.svg",
        sizes: "512x512",
        type: "image/svg+xml",
        purpose: "any",
      },
    ],
  };
}
