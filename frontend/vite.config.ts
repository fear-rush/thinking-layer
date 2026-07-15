import { defineConfig } from "vitest/config";

import { tanstackStart } from "@tanstack/react-start/plugin/vite";

import viteReact from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const apiTarget = process.env.THINKING_LAYER_API_URL ?? "http://127.0.0.1:8000";

const config = defineConfig({
  resolve: { tsconfigPaths: true },
  plugins: [tailwindcss(), tanstackStart(), viteReact()],
  server: {
    proxy: {
      "/v1": apiTarget,
      "/healthz": apiTarget,
    },
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});

export default config;
