import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api/": {
        target: "http://127.0.0.1:8000",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      "/grafana/": { target: "http://127.0.0.1:18000" },
    },
  },
  test: { environment: "jsdom", setupFiles: ["./tests/setup.ts"] },
});
