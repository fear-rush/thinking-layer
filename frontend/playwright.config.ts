import { defineConfig, devices } from "@playwright/test";

const frontendUrl = "http://127.0.0.1:3010";
const apiUrl = "http://127.0.0.1:8010";

export default defineConfig({
  testDir: "./e2e",
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
      name: "test-api",
      command: "uv run uvicorn --app-dir tests browser_api_app:app --host 127.0.0.1 --port 8010",
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
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
