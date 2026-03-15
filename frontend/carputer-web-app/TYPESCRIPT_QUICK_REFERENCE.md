# TypeScript Setup Quick Reference

## Commands

```bash
# Start development server
npm run dev

# Type checking (no build output)
npm run type-check

# Production build
npm run build

# Preview production build locally
npm run preview
```

## Key Files to Know

| File               | Purpose                                     |
| ------------------ | ------------------------------------------- |
| `tsconfig.json`    | TypeScript compiler configuration           |
| `vite-env.d.ts`    | Type definitions for Vite + Svelte          |
| `vite.config.ts`   | Vite build configuration (TypeScript)       |
| `svelte.config.ts` | Svelte framework configuration (TypeScript) |
| `package.json`     | Project metadata and scripts                |

## Type Annotations Cheat Sheet

```typescript
// Basic types
let name: string = "John";
let age: number = 25;
let active: boolean = true;

// Functions
function greet(name: string): string {
  return `Hello, ${name}`;
}

// Optional parameters
function process(value?: string): void {
  if (value) console.log(value);
}

// Union types
type Status = "loading" | "success" | "error";
let status: Status = "loading";

// Interfaces
interface User {
  id: number;
  name: string;
  email?: string; // Optional property
}

// Null/undefined checks
if (value !== null && value !== undefined) {
  // Safe to use value
}

// Type assertions (use carefully!)
let element = document.getElementById("app")!; // ! = non-null assertion
```

## When You Add New Dependencies

If you install a package and need type definitions:

```bash
# Most packages include types, but if not:
npm install --save-dev @types/package-name
```

## Debugging in VS Code

1. Press `Ctrl+Shift+B` - Run build task
2. Press `Ctrl+Shift+P` → "TypeScript: Show Docs" - View symbol documentation
3. Hover over any identifier to see its type
4. Press `F12` - Go to type definition

## Common Error Solutions

| Error                     | Solution                                      |
| ------------------------- | --------------------------------------------- |
| "Cannot find module"      | Check import path and verify file exists      |
| "Property does not exist" | Verify the type has that property, check docs |
| "Object is possibly null" | Add `if (obj !== null)` check                 |
| "No declaration for 'x'"  | Add type annotations or install `@types/x`    |
