import { defineConfig } from "@playwright/test";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";

const testDirectory = mkdtempSync(resolve(tmpdir(), "lilt-e2e-"));
const python = resolve(
  __dirname,
  "..",
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  timeout: 60000,
  use: {
    baseURL: "http://127.0.0.1:3001",
    trace: process.env.PW_TRACE ? "retain-on-failure" : "off",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `"${python}" -m uvicorn app.main:app --host 127.0.0.1 --port 8001`,
      cwd: "../backend",
      url: "http://127.0.0.1:8001/api/health",
      reuseExistingServer: false,
      timeout: 30000,
      env: {
        OPENAI_API_KEY: "",
        DATABASE_URL: `sqlite:///${resolve(testDirectory, "learning.db").replaceAll("\\", "/")}`,
        FRONTEND_ORIGIN: "http://127.0.0.1:3001",
      },
    },
    {
      command: "npm run dev -- --port 3001",
      url: "http://127.0.0.1:3001",
      reuseExistingServer: false,
      timeout: 60000,
      env: { BACKEND_URL: "http://127.0.0.1:8001", NEXT_DIST_DIR: ".next-e2e" },
    },
  ],
});
