import adapter from "@sveltejs/adapter-static";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import { sveltekit } from "@sveltejs/kit/vite";
import { svelteTesting } from "@testing-library/svelte/vite";
import tailwindcss from "@tailwindcss/vite";
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { defineConfig } from "vitest/config";

// App version: root VERSION file + "+<commit count>.<short sha>" (same rule as
// backend/app/core/version.py). APP_VERSION overrides it, e.g. in Docker builds.
function appVersion(): string {
  if (process.env.APP_VERSION) return process.env.APP_VERSION;
  let base: string;
  try {
    base = readFileSync(new URL("../VERSION", import.meta.url), "utf8").trim();
  } catch {
    return "dev";
  }
  try {
    const git = (args: string) =>
      execSync(`git ${args}`, { stdio: ["ignore", "pipe", "ignore"] })
        .toString()
        .trim();
    return `${base}+${git("rev-list --count HEAD")}.${git("rev-parse --short HEAD")}`;
  } catch {
    return base;
  }
}

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(appVersion()),
  },
  plugins: [
    tailwindcss(),
    sveltekit({
      preprocess: vitePreprocess(),
      // Static adapter for Docker deployment with nginx
      adapter: adapter({
        pages: "build",
        assets: "build",
        fallback: "index.html",
        precompress: false,
        strict: true,
      }),
    }),
    svelteTesting(),
  ],
  server: {
    port: 5173,
    proxy: {
      // Proxy all /api requests to backend
      "^/api/.*": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path /* Keep path as-is */,
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: [],
  },
});
