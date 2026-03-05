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

## Features
- Displays an OpenLayers map centered on the user's current location.
- A button to snap the map to the user's location.

## Project Assets
- Components Folder: holds reusable Svelte components that are used across multiple pages.
- Styles Folder: holds global CSS used throughout the application.

## Notes
This thing is slow right now because it's using browser geolocation data, which is not very fast. Once we can start getting data from the hardware, this should improve significantly.

