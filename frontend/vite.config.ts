import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 5173,
    proxy: {
      // Proxy all /api requests to backend
      "^/api/.*": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path, // Keep path as-is
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: [],
  },
});
