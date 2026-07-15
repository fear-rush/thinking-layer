import { defineConfig, devices } from "@playwright/test";

const frontendUrl = "http://127.0.0.1:3010";
const apiUrl = "http://127.0.0.1:8010";
const backendMode = process.env.THINKING_LAYER_E2E_BACKEND ?? "fixture";
const useLiveBackend = backendMode === "live";

if (!useLiveBackend && backendMode !== "fixture") {
  throw new Error("THINKING_LAYER_E2E_BACKEND must be `fixture` or `live`.");
}

export default defineConfig({
  testDir: useLiveBackend ? "./e2e-live" : "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: "list",
  use: {
    baseURL: frontendUrl,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      name: useLiveBackend ? "live-api" : "fixture-api",
      command: useLiveBackend
        ? "uv run uvicorn thinking_layer.api.app:app --host 127.0.0.1 --port 8010"
        : "uv run uvicorn --app-dir tests browser_api_app:app --host 127.0.0.1 --port 8010",
      cwd: "..",
      env: { PYTHONPATH: "." },
      url: `${apiUrl}/healthz`,
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      name: "frontend",
      command: "bun run dev:e2e",
      env: { THINKING_LAYER_API_URL: apiUrl },
      url: frontendUrl,
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
  projects: [
    {
      name: useLiveBackend ? "chromium-live" : "chromium-fixture",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
