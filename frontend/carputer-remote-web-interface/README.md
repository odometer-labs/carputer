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
- `/Logs` - Logs page
- `/Tracks` - Tracks page
- `/ManageData` - Manage data page

## Live Backend Data

The Home dashboard now uses live backend data (no hardcoded placeholder metrics):

- `GET /api/v1/tracks` - total GPS track count
- `GET /v2/versioning/latest` - current patch level
- `WS /ws/sys-health` - CPU, memory, disk, uptime, and network throughput
- `WS /ws/get-position` - current GPS fix (lat/lon, speed, heading)

If a backend source is temporarily unavailable, the UI displays `Unavailable` for that field instead of fake values.

## Local Development Proxy

`vite.config.ts` includes dev proxies so local frontend development can hit backend services without CORS setup:

- `/api` -> `http://localhost:8000` (legacy API)
- `/v2` -> `http://localhost:8888` (core API)
- `/ws` -> `http://localhost:8000` (legacy WebSocket streams)
- `/ws/sys-health` -> `http://localhost:8090` (sys-health WebSocket stream)

## Project Structure

- `src/pages` - top-level page components
- `src/assets/components` - shared UI components
- `src/utils` - helper utilities (navigation, etc.)

## Notes

- Routing is handled in `src/App.svelte`.
- Navigation helpers are in `src/utils/navigation.ts`.
- The Logs page currently displays hardcoded sample log data.
- It does not currently fetch a device log file such as `/device-logs/carputer-system.log`, so no Raspberry Pi web-server log-file exposure is required for the current implementation.
- Home dashboard formatting/status logic tests are in `src/test/homeHealth.test.ts` and API client tests are in `src/test/restApi.test.ts`.
