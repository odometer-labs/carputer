import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: ["dist/**", "node_modules/**"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["src/**/*.{ts,mts,cts}", "vite-env.d.ts"],
    languageOptions: {
      globals: globals.browser,
    },
  },
  {
    files: ["*.config.{ts,mts,cts}"],
    languageOptions: {
      globals: globals.node,
    },
  },
);