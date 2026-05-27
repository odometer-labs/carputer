# Carputer Remote Web Interface

Simple Svelte app for controlling and viewing parts of the carputer UI from a browser.

## Tech Stack

- Svelte 5
- Vite
- TypeScript
- svelte-spa-router

## Getting Started

1. Install dependencies:

```bash
npm install
```

2. Start the dev server:

```bash
npm run dev
```

3. Open the URL shown in the terminal (usually `http://localhost:5173`).

## Available Scripts

- `npm run dev` - start local development server
- `npm run build` - build production assets
- `npm run preview` - preview production build locally
- `npm run type-check` - run TypeScript checks
- `npm run lint` - lint TypeScript files
- `npm run test` - run tests once
- `npm run test:watch` - run tests in watch mode

## App Routes

- `/` - Home page
- `/Tracks` - Tracks page
- `/ManageData` - Manage data page

## Project Structure

- `src/pages` - top-level page components
- `src/assets/components` - shared UI components
- `src/utils` - helper utilities (navigation, etc.)

## Notes

- Routing is handled in `src/App.svelte`.
- Navigation helpers are in `src/utils/navigation.ts`.
