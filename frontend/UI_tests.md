# UI Tests

## Automated Tests
Run the automated suite:

```bash
cd frontend/carputer-web-app
npm install   # ensure dependencies including test libraries
npm test      # runs vitest, which includes the above script checks plus component/service tests
```
This suite includes:
- Type-checking the TypeScript code to catch type errors.
- Linting the code with ESLint to enforce code quality and style.
- Starting the development server to ensure it runs without errors.
- Building the production bundle to verify the build process works.
- Running unit tests for frontend-specific modules and components.

## Manual Tests
Start by running:
```bash
npm run dev
```
Then open the app in a browser verify that:
- [x] UI looks good in the browser and is responsive.

Then open the browser dev tools and change the device type to be responsive. Verify that:
- [x] UI adapts correctly to different screen sizes and orientations.

Now run the dev host dev server with:
```bash
npm run dev -- --host
```
Then access the app from a mobile device on the same network using the provided local IP address. Verify that:
- [x] UI works correctly on a real mobile device.
- [x] UI looks good in different landscape modes.
  


