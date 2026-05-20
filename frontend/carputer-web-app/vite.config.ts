import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      "/wifi": {
        target: "http://localhost:9001",
        changeOrigin: true,
      },

      // Proxy v2 API calls to core-api (Go service)
      "/v2": {
        target: "http://localhost:8888",
        changeOrigin: true,
      },

      // Proxy v1 API calls to legacy Python backend (strips the /api prefix)
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      // Proxy HTTP and WebSocket calls under /ws directly to the backend
      "/ws": {
        target: "http://localhost:8000",
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
