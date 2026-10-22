import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      "/v2": {
        target: "http://localhost:8888",
        changeOrigin: true,
      },
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      "/ws/sys-health": {
        target: "http://localhost:8090",
        changeOrigin: true,
        ws: true,
      },
      "/ws": {
        target: "http://localhost:8000",
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
