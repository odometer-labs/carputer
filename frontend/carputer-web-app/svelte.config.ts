import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import type { Config } from "@sveltejs/vite-plugin-svelte";

const config: Config = {
  // Consult https://svelte.dev/docs#compile-time-svelte-preprocess
  // for more information about preprocessors
  preprocess: vitePreprocess(),
};

export default config;
