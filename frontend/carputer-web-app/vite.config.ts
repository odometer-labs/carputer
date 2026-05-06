import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      "/wifi": {
        target: "http://localhost:8888",
        changeOrigin: true,
      },
    },
  },
});
