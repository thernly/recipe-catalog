import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import svelte from "eslint-plugin-svelte";
import globals from "globals";
import ts from "typescript-eslint";
import svelteConfig from "./svelte.config.js";

export default ts.config(
  {
    ignores: [".svelte-kit/", "build/", "dist/", ".wrangler/", "node_modules/"],
  },
  js.configs.recommended,
  ...ts.configs.recommended,
  ...svelte.configs.recommended,
  prettier,
  ...svelte.configs.prettier,
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      // TypeScript already reports undefined names, and no-undef misfires on TS-only globals.
      "no-undef": "off",
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
        },
      ],
      // The app is always served from the origin root (no `paths.base`), so plain hrefs are correct.
      "svelte/no-navigation-without-resolve": "off",
      // Existing debt, reported as warnings so `pnpm lint` passes while new cases stay visible.
      // Fixing them changes runtime behaviour (keyed DOM reuse, reactive collections), so it
      // needs its own change. Raise each to 'error' once its count reaches zero.
      "svelte/require-each-key": "warn",
      "svelte/prefer-svelte-reactivity": "warn",
      "@typescript-eslint/no-explicit-any": "warn",
    },
  },
  {
    files: ["**/*.svelte", "**/*.svelte.ts", "**/*.svelte.js"],
    languageOptions: {
      parserOptions: {
        parser: ts.parser,
        extraFileExtensions: [".svelte"],
        svelteConfig,
      },
    },
  },
  {
    // Mocks and fixtures cast freely; `any` is fine there.
    files: ["**/*.test.ts", "src/test/**"],
    rules: { "@typescript-eslint/no-explicit-any": "off" },
  },
);
