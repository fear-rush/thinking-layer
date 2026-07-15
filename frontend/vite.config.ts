import { defineConfig } from "vitest/config";

import { tanstackRouter } from "@tanstack/router-plugin/vite";

import viteReact from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const apiTarget = process.env.THINKING_LAYER_API_URL ?? "http://127.0.0.1:8000";

const config = defineConfig({
  resolve: { tsconfigPaths: true },
  plugins: [tailwindcss(), tanstackRouter({ target: "react" }), viteReact()],
  server: {
    proxy: {
      "/queries": apiTarget,
      "/feedback": apiTarget,
      "/documents": apiTarget,
      "/healthz": apiTarget,
    },
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});

export default config;
