---
name: project-stack
description: Full tech stack for recipe-catalog — SvelteKit/Tailwind v4 frontend, FastAPI/uv backend, pnpm workspace
metadata:
  type: project
---

## Frontend (`frontend/`)

- **Framework**: SvelteKit with Svelte 5, TypeScript, Vite v8
- **CSS**: Tailwind CSS v4.3.0 via `@tailwindcss/postcss`. Entry point is `src/app.css` using `@import "tailwindcss"`, `@config "../tailwind.config.js"`, and `@plugin` directives (v4 syntax — NOT `@tailwind` directives).
- **Theme system**: CSS custom properties in `app.css`. Four themes: `garden-fresh` (default), `bistro`, `dark`, `high-contrast`. Applied via `data-theme` attribute on `<html>`. Variables named `--primary-*`, `--accent-*`, `--neutral-*`, `--text-*`, `--space-*`, `--radius-*`.
- **Fonts**: Outfit (sans/UI) and Lora (display) via Google Fonts. Loaded in `app.html`. Referenced via CSS vars `--font-sans`, `--font-display`.
- **Icons**: `@lucide/svelte`
- **Package manager**: pnpm (workspace config at `frontend/pnpm-workspace.yaml`)
- **Testing**: Vitest v4 + jsdom + `@testing-library/svelte` v5. Config in `vite.config.ts`. Requires `svelteTesting()` plugin from `@testing-library/svelte/vite` for Svelte 5 browser bundle resolution.

### Key Tailwind v4 gotchas (learned the hard way)

- `theme.extend.spacing` names pollute `max-w-*`, `p-*`, etc. — do NOT add spacing names that match Tailwind's built-in size scale (`sm`, `md`, `lg`, `xl`, `2xl`, `3xl`).
- `theme.extend.borderRadius` with names like `md`, `lg` overrides Tailwind's default `rounded-*` values.
- Custom spacing/sizing is best kept entirely in CSS variables in `app.css`, not in `tailwind.config.js`.
- `tailwind.config.js` is NOT auto-read in v4 — requires `@config "../tailwind.config.js"` in the CSS file.
- Plugins load via `@plugin "@tailwindcss/forms"` in CSS, not `plugins: [require(...)]` in JS config.

## Backend (`backend/`)

- **Framework**: FastAPI (Python)
- **Package manager**: `uv` — use `uv run`, `uv add`, `uv sync`. Never `pip install`.
- **Database**: SQLite locally, Cloudflare D1 in production

## Deployment

- **Primary target**: Cloudflare Pages (frontend) + Cloudflare Workers (backend) + Cloudflare D1
- **Alternative**: Self-hosted on Proxmox with Docker + nginx (static adapter for SvelteKit)

## Auth

Custom auth with email/password + OAuth (Google, Microsoft, GitHub). Multi-user household support with invitation system.
