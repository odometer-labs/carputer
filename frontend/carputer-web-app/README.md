# carputer-web-app

A Svelte web application for displaying a map and the user's location. This is the frontend component of the carputer project.

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```
3. Open your browser and navigate to the URL displayed in the terminal to see the app in action.

You can also run a fake GPS data source for testing. And you can run this app on a mobile device by using the `--host` option with the dev server and accessing the local IP address from your device. See src/fake-api/README.md for full details.

## Features

- Single‑page Svelte application with client‑side routing via `svelte-spa-router`.
- OpenLayers map that tracks and recenters on the user's current GPS location.
- Support for live GPS data (via `gpsfake` bridge) or simulated/mock positions (NMEA playback or random walk).
- A floating "back" button and navigation between pages: Home, Dashboard, Map Download, Settings, Wifi.
- Global runtime error handling: fatal errors render a full-screen recovery page, while non-fatal errors appear as dismissible warning popups.
- Utilities for toggling GPS mode, downloading recorded routes, and adjusting preferences.

## Project Assets

- **src/assets/components/** – reusable Svelte components such as `BackButton`, `ErrorPopup`, and other common UI widgets.
- **src/assets/styles/** – global CSS, utility classes and theme variables.
- **src/fake-api/** – development mock services (GPS, config) including types and example NMEA files.
- **src/pages/** – page components corresponding to router paths (DashboardPage, ErrorPage, HomeMapPage, MapDownloadPage, SettingPreferencePage, WifiPage).
- **src/stores/** – shared client state stores such as `errorStore`, which tracks fatal and non-fatal app errors.
- **scripts/** – helper scripts such as the `gpsd-ws-bridge` that proxies real GPSD data to WebSockets for the frontend.
- **tests/** – Vitest tests alongside source code under `src/test` verify functionality and CI health.

## Testing

Automated unit tests live alongside the source in `src/test`. They exercise the manual checklist from `UI_tests.md` (type-check, lint, dev server sanity, build) and cover a handful of frontend-specific modules and components.

To run the suite:

```bash
cd frontend/carputer-web-app
npm install          # get dependencies (including vitest and testing-library)
npm test             # run Vitest; add `--watch` for a watch mode
```

The same tests are used by CI to verify the frontend remains healthy as development continues.
