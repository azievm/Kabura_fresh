import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Фронт отдаётся тем же FastAPI, что и API (один origin через туннель),
// поэтому запросы к /api/* идут относительно. В dev проксируем на бот.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8080",
    },
  },
});
