# Frontend Team Tech Stack Recommendations

## Overview
This document outlines the recommended technology stack for the Frontend Team responsible for the touch display interface, web dashboard, map visualization, and user experience for the Raspberry Pi GPS Tracking Carputer project.

---

## Core Frontend Framework

### Why Svelte/SvelteKit?

**Svelte** is the ideal choice for this project due to:

**Performance:**
- Smallest bundle size (compiles to vanilla JS)
- No virtual DOM overhead
- Faster runtime performance (critical on Raspberry Pi)
- Compile-time optimizations

**Developer Experience:**
- Simplest, most intuitive syntax
- Built-in reactivity (no useState, no hooks)
- Less boilerplate code
- Excellent TypeScript support

**Perfect for Embedded Systems:**
- Minimal JavaScript shipped to browser
- Low memory footprint
- Fast initial load times
- Excellent for touch interfaces

**Ecosystem:**
- SvelteKit for full-stack applications
- Growing component libraries
- Good mapping library support
- Active community

### Recommended Stack
- **Svelte 4+** (or Svelte 5 with runes)
- **SvelteKit 2+** for routing and SSR
- **TypeScript** for type safety
- **Vite** (built into SvelteKit)

---

## Map Visualization Stack

### Map Library Options

#### Option 1: MapLibre GL JS (Recommended)
**Best for vector tiles and modern web maps**
```typescript
// +page.svelte
<script lang="ts">
  import maplibregl from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import { onMount } from 'svelte';
  
  let mapContainer: HTMLDivElement;
  let map: maplibregl.Map;
  
  onMount(() => {
    map = new maplibregl.Map({
      container: mapContainer,
      style: '/map-style.json',
      center: [-122.6, 45.5],
      zoom: 12
    });
    
    return () => map.remove();
  });
</script>

<div bind:this={mapContainer} class="map-container" />
```

**Pros:**
- Open source fork of Mapbox GL JS
- Excellent vector tile support
- Smooth animations and interactions
- 3D terrain support
- Active development
- No API keys or usage limits

**Cons:**
- Steeper learning curve
- Requires vector tiles or raster source
- Manual integration with Svelte (no official wrapper yet)

**Svelte Integration:**
- Direct MapLibre GL JS usage with Svelte actions
- Custom wrapper components
- Use Svelte stores for map state

#### Option 2: Leaflet
**Best for simplicity and raster tiles**
```typescript
<script lang="ts">
  import L from 'leaflet';
  import 'leaflet/dist/leaflet.css';
  import { onMount } from 'svelte';
  
  let mapContainer: HTMLDivElement;
  
  onMount(() => {
    const map = L.map(mapContainer).setView([45.5, -122.6], 13);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    
    return () => map.remove();
  });
</script>
```

**Pros:**
- Mature, stable library
- Simple API
- Excellent plugin ecosystem
- Works great with raster tiles
- Lower learning curve
- svelte-leaflet package available

**Cons:**
- Limited vector tile support
- Less smooth animations than MapLibre
- Older codebase

**Svelte Integration:**
- **svelte-leaflet** - Community Svelte wrapper
- Direct Leaflet usage with Svelte actions

#### Option 3: OpenLayers
**Most feature-rich but complex**

**Pros:**
- Supports every geospatial format
- Very powerful
- Good for complex GIS applications

**Cons:**
- Steep learning curve
- Larger bundle size
- Overkill for this project

### Recommendation: MapLibre GL JS
Use **MapLibre GL JS** directly in Svelte for:
- Modern vector tile rendering
- Smooth performance on touch devices
- Offline map support
- Rich styling capabilities
- Direct control with Svelte lifecycle

---

## UI Component Library

### Component Library Options

#### Option 1: shadcn-svelte (Recommended)
**Svelte port of shadcn/ui**

**Pros:**
- Built on Bits UI (accessible Svelte components)
- Tailwind CSS styling
- Copy components into your project (full control)
- Beautiful default designs
- Dark mode support built-in
- TypeScript support

**Installation:**
```bash
npx shadcn-svelte@latest init
npx shadcn-svelte@latest add button
npx shadcn-svelte@latest add card dialog dropdown-menu
```

**Components Needed:**
- Button, Card, Dialog, Dropdown Menu
- Slider (for map settings)
- Switch (for toggles)
- Tabs, Table
- Toast notifications
- Command palette (for search)

**Example Usage:**
```svelte
<script lang="ts">
  import { Button } from '$lib/components/ui/button';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
</script>

<Card>
  <CardHeader>
    <CardTitle>GPS Tracker</CardTitle>
  </CardHeader>
  <CardContent>
    <Button>Start Tracking</Button>
  </CardContent>
</Card>
```

#### Option 2: Skeleton UI
**Full-featured Svelte component library**

**Pros:**
- Comprehensive component set
- Built-in theming
- Tailwind-based
- Good documentation
- Touch-friendly

**Cons:**
- More opinionated
- Larger bundle if using many components

#### Option 3: Melt UI
**Headless component library**

**Pros:**
- Unstyled, maximum flexibility
- Excellent accessibility
- TypeScript-first
- Smaller bundle size

**Cons:**
- Requires styling all components yourself
- More initial work

#### Option 4: daisyUI
**Tailwind component classes**

**Pros:**
- Simple to use
- Beautiful defaults
- Theme support
- No JavaScript required for most components

**Cons:**
- Class-based (not Svelte components)
- Less type safety

### Recommendation: shadcn-svelte + Tailwind CSS
Use **shadcn-svelte** with **Tailwind CSS** for:
- Modern, clean aesthetic
- Full customization control
- Excellent dark mode support (critical for night driving)
- Small bundle size (only include what you use)
- Accessibility built-in

---

## Styling Solution

### CSS Framework: Tailwind CSS

```javascript
// tailwind.config.js
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Custom carputer theme
        'carputer-primary': '#3b82f6',
        'carputer-secondary': '#8b5cf6',
      }
    }
  }
}
```

**Advantages:**
- Utility-first approach
- Excellent dark mode support
- Small production bundle (with PurgeCSS)
- Rapid development
- Consistent spacing and sizing
- Works perfectly with Svelte

**Alternatives:**
- **Svelte scoped styles** (built-in, no config needed)
- **UnoCSS** (faster alternative to Tailwind)
- **Vanilla CSS** with CSS variables

---

## State Management

### Svelte Stores (Built-in, Recommended)

**Svelte's built-in stores are perfect for this project:**

```typescript
// lib/stores/gps.ts
import { writable, derived } from 'svelte/store';

export interface GPSPosition {
  lat: number;
  lon: number;
  speed: number | null;
  heading: number | null;
  timestamp: Date;
}

export const gpsPosition = writable<GPSPosition | null>(null);
export const gpsSpeed = derived(gpsPosition, $pos => $pos?.speed ?? 0);
export const isMoving = derived(gpsSpeed, $speed => $speed > 0.5);

// Update position
export function updatePosition(pos: GPSPosition) {
  gpsPosition.set(pos);
}
```

**Usage in components:**
```svelte
<script lang="ts">
  import { gpsPosition, isMoving } from '$lib/stores/gps';
</script>

<div>
  {#if $gpsPosition}
    <p>Lat: {$gpsPosition.lat}</p>
    <p>Lon: {$gpsPosition.lon}</p>
    <p>Speed: {$gpsPosition.speed} km/h</p>
  {:else}
    <p>Waiting for GPS...</p>
  {/if}
  
  {#if $isMoving}
    <p>Currently moving</p>
  {/if}
</div>
```

**Store Types:**

#### Writable Stores
```typescript
// For mutable state
export const trackLayers = writable<TrackLayer[]>([]);
export const selectedTrack = writable<Track | null>(null);
```

#### Readable Stores
```typescript
// For read-only state
export const systemTime = readable(new Date(), (set) => {
  const interval = setInterval(() => {
    set(new Date());
  }, 1000);
  
  return () => clearInterval(interval);
});
```

#### Derived Stores
```typescript
// For computed values
export const visibleTracks = derived(
  [trackLayers, mapBounds],
  ([$layers, $bounds]) => $layers.filter(layer => 
    layer.visible && isInBounds(layer, $bounds)
  )
);
```

#### Custom Stores
```typescript
// For complex logic
function createTrackStore() {
  const { subscribe, set, update } = writable<Track[]>([]);
  
  return {
    subscribe,
    add: (track: Track) => update(tracks => [...tracks, track]),
    remove: (id: number) => update(tracks => tracks.filter(t => t.id !== id)),
    clear: () => set([]),
  };
}

export const tracks = createTrackStore();
```

**Why Svelte Stores are Perfect:**
- Built-in, no external library needed
- Extremely simple API
- Reactive by default ($ syntax)
- Minimal boilerplate
- Excellent performance
- TypeScript support
- Perfect for real-time GPS updates

**No Need for:**
- Redux/Redux Toolkit (too complex)
- Zustand (Svelte stores are simpler)
- MobX (Svelte reactivity is built-in)
- Context API (not needed in Svelte)

---

## Real-Time Data Handling

### WebSocket Integration

```typescript
// lib/websocket.ts
import { gpsPosition } from '$lib/stores/gps';
import type { GPSPosition } from '$lib/types';

export function connectGPSStream() {
  const ws = new WebSocket('ws://localhost:8000/api/gps/stream');
  
  ws.onopen = () => {
    console.log('GPS WebSocket connected');
  };
  
  ws.onmessage = (event) => {
    const data: GPSPosition = JSON.parse(event.data);
    gpsPosition.set(data);
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  ws.onclose = () => {
    console.log('GPS WebSocket closed, reconnecting...');
    setTimeout(connectGPSStream, 3000); // Reconnect after 3s
  };
  
  return ws;
}
```

**Usage in component:**
```svelte
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { connectGPSStream } from '$lib/websocket';
  import { gpsPosition } from '$lib/stores/gps';
  
  let ws: WebSocket;
  
  onMount(() => {
    ws = connectGPSStream();
  });
  
  onDestroy(() => {
    ws?.close();
  });
</script>

<div>
  {#if $gpsPosition}
    <p>Current position: {$gpsPosition.lat}, {$gpsPosition.lon}</p>
  {/if}
</div>
```

### Svelte Action for WebSocket

```typescript
// lib/actions/websocket.ts
export function websocket(node: HTMLElement, url: string) {
  const ws = new WebSocket(url);
  
  ws.onmessage = (event) => {
    node.dispatchEvent(new CustomEvent('message', { 
      detail: JSON.parse(event.data) 
    }));
  };
  
  return {
    destroy() {
      ws.close();
    }
  };
}

// Usage
<div use:websocket="ws://localhost:8000/api/gps/stream" 
     on:message={handleGPSUpdate}>
</div>
```

### Server-Sent Events Alternative

```typescript
// lib/sse.ts
import { gpsPosition } from '$lib/stores/gps';

export function connectGPSSSE() {
  const eventSource = new EventSource('/api/gps/stream');
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    gpsPosition.set(data);
  };
  
  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    eventSource.close();
  };
  
  return eventSource;
}
```

---

## Data Fetching & API Integration

### SvelteKit Load Functions

**SvelteKit's built-in data loading is perfect for this:**

```typescript
// routes/tracks/+page.ts
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
  const response = await fetch('/api/tracks');
  const tracks = await response.json();
  
  return {
    tracks
  };
};

// +page.svelte
<script lang="ts">
  import type { PageData } from './$types';
  
  export let data: PageData;
</script>

<ul>
  {#each data.tracks as track}
    <li>{track.name}</li>
  {/each}
</ul>
```

### Custom API Client

```typescript
// lib/api.ts
import { error } from '@sveltejs/kit';

export const api = {
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`/api${endpoint}`);
    if (!response.ok) throw error(response.status, 'API request failed');
    return response.json();
  },
  
  async post<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await fetch(`/api${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw error(response.status, 'API request failed');
    return response.json();
  },
  
  async delete(endpoint: string): Promise<void> {
    const response = await fetch(`/api${endpoint}`, { method: 'DELETE' });
    if (!response.ok) throw error(response.status, 'Delete failed');
  }
};

// Usage
import { api } from '$lib/api';

const tracks = await api.get<Track[]>('/tracks');
await api.post('/tracks', { name: 'New Track' });
await api.delete(`/tracks/${id}`);
```

### Using Stores for API Data

```typescript
// lib/stores/tracks.ts
import { writable } from 'svelte/store';
import { api } from '$lib/api';

function createTrackStore() {
  const { subscribe, set, update } = writable<Track[]>([]);
  let loading = writable(false);
  
  return {
    subscribe,
    loading: { subscribe: loading.subscribe },
    
    async load() {
      loading.set(true);
      try {
        const tracks = await api.get<Track[]>('/tracks');
        set(tracks);
      } finally {
        loading.set(false);
      }
    },
    
    async create(track: Partial<Track>) {
      const newTrack = await api.post<Track>('/tracks', track);
      update(tracks => [...tracks, newTrack]);
      return newTrack;
    },
    
    async delete(id: number) {
      await api.delete(`/tracks/${id}`);
      update(tracks => tracks.filter(t => t.id !== id));
    }
  };
}

export const trackStore = createTrackStore();
```

**Usage:**
```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { trackStore } from '$lib/stores/tracks';
  
  onMount(() => {
    trackStore.load();
  });
</script>

{#if $trackStore.loading}
  <p>Loading tracks...</p>
{:else}
  <ul>
    {#each $trackStore as track}
      <li>
        {track.name}
        <button on:click={() => trackStore.delete(track.id)}>Delete</button>
      </li>
    {/each}
  </ul>
{/if}
```

### Alternative: TanStack Query for Svelte

If you need advanced caching:

```bash
npm install @tanstack/svelte-query
```

```svelte
<script lang="ts">
  import { createQuery } from '@tanstack/svelte-query';
  
  const tracksQuery = createQuery({
    queryKey: ['tracks'],
    queryFn: async () => {
      const res = await fetch('/api/tracks');
      return res.json();
    }
  });
</script>

{#if $tracksQuery.isLoading}
  <p>Loading...</p>
{:else if $tracksQuery.error}
  <p>Error: {$tracksQuery.error.message}</p>
{:else if $tracksQuery.data}
  <ul>
    {#each $tracksQuery.data as track}
      <li>{track.name}</li>
    {/each}
  </ul>
{/if}
```

---

## Form Handling

### Svelte Native Forms (Recommended)

**Svelte's built-in form handling is simple and powerful:**

```svelte
<script lang="ts">
  import { z } from 'zod';
  
  const trackSchema = z.object({
    name: z.string().min(1, 'Name is required'),
    description: z.string().optional(),
  });
  
  let form = {
    name: '',
    description: ''
  };
  
  let errors: Record<string, string> = {};
  
  async function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    errors = {};
    
    const result = trackSchema.safeParse(form);
    
    if (!result.success) {
      result.error.errors.forEach(err => {
        errors[err.path[0]] = err.message;
      });
      return;
    }
    
    // Submit valid data
    await api.post('/tracks', result.data);
  }
</script>

<form on:submit={handleSubmit}>
  <label>
    Name
    <input bind:value={form.name} type="text" />
    {#if errors.name}<span class="error">{errors.name}</span>{/if}
  </label>
  
  <label>
    Description
    <textarea bind:value={form.description}></textarea>
  </label>
  
  <button type="submit">Save</button>
</form>
```

### SvelteKit Form Actions (Server-Side Forms)

```typescript
// routes/tracks/+page.server.ts
import { fail } from '@sveltejs/kit';
import type { Actions } from './$types';
import { z } from 'zod';

const trackSchema = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
});

export const actions: Actions = {
  create: async ({ request }) => {
    const formData = await request.formData();
    const data = {
      name: formData.get('name'),
      description: formData.get('description'),
    };
    
    const result = trackSchema.safeParse(data);
    
    if (!result.success) {
      return fail(400, {
        errors: result.error.flatten().fieldErrors,
        data
      });
    }
    
    // Save to database
    await db.tracks.create(result.data);
    
    return { success: true };
  }
};
```

```svelte
<!-- +page.svelte -->
<script lang="ts">
  import type { ActionData } from './$types';
  
  export let form: ActionData;
</script>

<form method="POST" action="?/create">
  <input name="name" type="text" value={form?.data?.name ?? ''} />
  {#if form?.errors?.name}
    <span class="error">{form.errors.name}</span>
  {/if}
  
  <textarea name="description">{form?.data?.description ?? ''}</textarea>
  
  <button type="submit">Create Track</button>
</form>

{#if form?.success}
  <p>Track created successfully!</p>
{/if}
```

### Felte (Advanced Form Library)

For complex forms with many fields:

```bash
npm install felte @felte/validator-zod
```

```svelte
<script lang="ts">
  import { createForm } from 'felte';
  import { validator } from '@felte/validator-zod';
  import { z } from 'zod';
  
  const schema = z.object({
    name: z.string().min(1, 'Required'),
    description: z.string().optional(),
  });
  
  const { form, errors, isValid } = createForm({
    extend: validator({ schema }),
    onSubmit: async (values) => {
      await api.post('/tracks', values);
    },
  });
</script>

<form use:form>
  <input name="name" type="text" />
  {#if $errors.name}<span>{$errors.name}</span>{/if}
  
  <textarea name="description"></textarea>
  
  <button type="submit" disabled={!$isValid}>Save</button>
</form>
```

**Why Svelte Native Forms:**
- No external library needed for simple forms
- Two-way binding with `bind:value`
- Minimal code
- Works great with Zod validation
- SvelteKit form actions for progressive enhancement

---

## File Upload & Import/Export

### File Handling with Svelte

```svelte
<script lang="ts">
  import { api } from '$lib/api';
  
  let dragActive = false;
  let uploading = false;
  
  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    
    uploading = true;
    
    for (const file of Array.from(files)) {
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        await fetch('/api/import/gpx', {
          method: 'POST',
          body: formData
        });
      } catch (error) {
        console.error('Upload failed:', error);
      }
    }
    
    uploading = false;
  }
  
  function handleDrop(event: DragEvent) {
    event.preventDefault();
    dragActive = false;
    handleFiles(event.dataTransfer?.files ?? null);
  }
  
  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dragActive = true;
  }
  
  function handleDragLeave() {
    dragActive = false;
  }
</script>

<div
  class="dropzone"
  class:active={dragActive}
  on:drop={handleDrop}
  on:dragover={handleDragOver}
  on:dragleave={handleDragLeave}
>
  <input
    type="file"
    accept=".gpx,.kml"
    multiple
    on:change={(e) => handleFiles(e.currentTarget.files)}
    id="file-input"
  />
  
  <label for="file-input">
    {#if uploading}
      <p>Uploading...</p>
    {:else if dragActive}
      <p>Drop files here</p>
    {:else}
      <p>Drag GPX/KML files here or click to browse</p>
    {/if}
  </label>
</div>

<style>
  .dropzone {
    border: 2px dashed #ccc;
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
    cursor: pointer;
  }
  
  .dropzone.active {
    border-color: #3b82f6;
    background: #eff6ff;
  }
  
  input[type="file"] {
    display: none;
  }
</style>
```

### File Download/Export

```svelte
<script lang="ts">
  async function exportTrack(trackId: number, format: 'gpx' | 'geojson') {
    const response = await fetch(`/api/export/${trackId}/${format}`);
    const blob = await response.blob();
    
    // Create download link
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `track-${trackId}.${format}`;
    a.click();
    
    URL.revokeObjectURL(url);
  }
</script>

<button on:click={() => exportTrack(track.id, 'gpx')}>
  Export as GPX
</button>

<button on:click={() => exportTrack(track.id, 'geojson')}>
  Export as GeoJSON
</button>
```

### Alternative: filepond-svelte

For advanced file upload with preview and validation:

```bash
npm install svelte-filepond filepond
```

```svelte
<script lang="ts">
  import FilePond from 'svelte-filepond';
  
  let pond;
  
  function handleProcessFile(error, file) {
    if (!error) {
      console.log('File uploaded:', file);
    }
  }
</script>

<FilePond
  bind:this={pond}
  name="file"
  server="/api/import/gpx"
  allowMultiple={true}
  accepted-file-types={['application/gpx+xml', 'application/vnd.google-earth.kml+xml']}
  onprocessfile={handleProcessFile}
/>
```

---

## Notifications & Alerts

### Toast Notifications with svelte-sonner

```bash
npm install svelte-sonner
```

```svelte
<!-- +layout.svelte -->
<script lang="ts">
  import { Toaster } from 'svelte-sonner';
</script>

<Toaster />

<slot />
```

```svelte
<!-- Usage in any component -->
<script lang="ts">
  import { toast } from 'svelte-sonner';
  
  function alertNewRoad() {
    toast.success('New Road Detected!', {
      description: 'You are on a road you have never driven before',
      duration: 5000,
    });
  }
  
  function alertGPSLost() {
    toast.error('GPS Signal Lost', {
      description: 'Searching for satellites...',
    });
  }
</script>

<button on:click={alertNewRoad}>Test Alert</button>
```

**Features:**
- Beautiful default styling
- Stacking notifications
- Promise-based toasts
- Dark mode support
- Tiny bundle size

**Alternative: svelte-french-toast**

```bash
npm install svelte-french-toast
```

```svelte
<script lang="ts">
  import toast, { Toaster } from 'svelte-french-toast';
  
  toast.success('Track saved!');
  toast.error('Failed to load GPS data');
  toast.loading('Importing track...');
</script>

<Toaster />
```

---

## Routing & Navigation

### SvelteKit File-based Routing

**SvelteKit uses file-based routing (like Next.js):**

```
src/routes/
├── +page.svelte                    # / (map view)
├── +layout.svelte                  # Root layout
├── +layout.ts                      # Root layout data
├── settings/
│   └── +page.svelte                # /settings
├── dashboard/
│   └── +page.svelte                # /dashboard
├── tracks/
│   ├── +page.svelte                # /tracks
│   ├── +page.ts                    # Load tracks data
│   └── [id]/
│       ├── +page.svelte            # /tracks/123
│       └── +page.ts                # Load single track
└── import/
    └── +page.svelte                # /import
```

### Layout Structure

```svelte
<!-- +layout.svelte -->
<script lang="ts">
  import { page } from '$app/stores';
  import Header from '$lib/components/Header.svelte';
  import Sidebar from '$lib/components/Sidebar.svelte';
  
  $: isTouchInterface = $page.route.id === '/';
</script>

{#if !isTouchInterface}
  <div class="app-layout">
    <Header />
    <Sidebar />
    <main>
      <slot />
    </main>
  </div>
{:else}
  <!-- Full-screen touch interface -->
  <slot />
{/if}
```

### Programmatic Navigation

```svelte
<script lang="ts">
  import { goto } from '$app/navigation';
  
  function navigateToTrack(id: number) {
    goto(`/tracks/${id}`);
  }
  
  function goBack() {
    history.back();
  }
</script>

<button on:click={() => navigateToTrack(123)}>
  View Track
</button>
```

### Navigation with Data Preloading

```svelte
<script lang="ts">
  import { preloadData } from '$app/navigation';
  
  async function handleHover() {
    // Preload data on hover for instant navigation
    await preloadData('/tracks/123');
  }
</script>

<a 
  href="/tracks/123" 
  on:mouseenter={handleHover}
>
  Track Details
</a>
```

### Route Protection

```typescript
// hooks.server.ts
import { redirect } from '@sveltejs/kit';
import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
  // Protect routes if needed
  if (event.url.pathname.startsWith('/admin')) {
    // Check authentication
    const session = event.cookies.get('session');
    if (!session) {
      throw redirect(303, '/login');
    }
  }
  
  return resolve(event);
};
```

---

## Geospatial Data Visualization

### Track Overlay Management

```svelte
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import maplibregl from 'maplibre-gl';
  import type { Map } from 'maplibre-gl';
  import { visibleTracks } from '$lib/stores/tracks';
  
  let mapContainer: HTMLDivElement;
  let map: Map;
  
  onMount(() => {
    map = new maplibregl.Map({
      container: mapContainer,
      style: '/map-style.json',
      center: [-122.6, 45.5],
      zoom: 12
    });
    
    map.on('load', () => {
      // Add source for tracks
      map.addSource('tracks', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: []
        }
      });
      
      // Add layer for tracks
      map.addLayer({
        id: 'tracks-layer',
        type: 'line',
        source: 'tracks',
        paint: {
          'line-color': ['get', 'color'],
          'line-width': 3
        }
      });
    });
  });
  
  // Update map when visible tracks change
  $: if (map && $visibleTracks) {
    const source = map.getSource('tracks');
    if (source && source.type === 'geojson') {
      source.setData({
        type: 'FeatureCollection',
        features: $visibleTracks.map(track => ({
          type: 'Feature',
          properties: { color: track.color },
          geometry: track.geojson
        }))
      });
    }
  }
  
  onDestroy(() => {
    map?.remove();
  });
</script>

<div bind:this={mapContainer} class="map-container" />
```

### APRS Station Markers

```svelte
<script lang="ts">
  import { aprsStations } from '$lib/stores/aprs';
  import maplibregl from 'maplibre-gl';
  
  let markers: maplibregl.Marker[] = [];
  
  // Update markers when stations change
  $: if (map && $aprsStations) {
    // Remove old markers
    markers.forEach(m => m.remove());
    markers = [];
    
    // Add new markers
    $aprsStations.forEach(station => {
      const el = document.createElement('div');
      el.className = 'aprs-marker';
      el.innerHTML = `
        <div class="aprs-symbol">${station.symbol}</div>
        <div class="aprs-callsign">${station.callsign}</div>
      `;
      
      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([station.lon, station.lat])
        .addTo(map);
      
      markers.push(marker);
    });
  }
</script>

<style>
  :global(.aprs-marker) {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  :global(.aprs-symbol) {
    font-size: 20px;
  }
  
  :global(.aprs-callsign) {
    font-size: 10px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 2px 4px;
    border-radius: 3px;
  }
</style>
```

### Custom Svelte Action for Map

```typescript
// lib/actions/map.ts
import maplibregl from 'maplibre-gl';
import type { Map, MapOptions } from 'maplibre-gl';

export function maplibre(node: HTMLElement, options: MapOptions) {
  const map = new maplibregl.Map({
    container: node,
    ...options
  });
  
  return {
    destroy() {
      map.remove();
    }
  };
}

// Usage
<div use:maplibre={{ style: '/style.json', center: [-122, 45], zoom: 12 }} />
```

---

## Progressive Web App (PWA)

### SvelteKit PWA with vite-plugin-pwa

```bash
npm install -D @vite-pwa/sveltekit
```

```typescript
// vite.config.ts
import { sveltekit } from '@sveltejs/kit/vite';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    sveltekit(),
    SvelteKitPWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'GPS Carputer',
        short_name: 'Carputer',
        description: 'GPS Tracking and Navigation',
        theme_color: '#3b82f6',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: '/icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/.*\.tile\.openstreetmap\.org\/.*/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'map-tiles',
              expiration: {
                maxEntries: 500,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
              }
            }
          }
        ]
      }
    })
  ]
});
```

**Features:**
- Offline functionality
- App-like experience
- Home screen installation
- Service worker for caching
- Automatic updates

---

## Dark Mode & Theming

### Theme Implementation with Svelte

```typescript
// lib/stores/theme.ts
import { writable } from 'svelte/store';
import { browser } from '$app/environment';

type Theme = 'light' | 'dark';

function createThemeStore() {
  // Get initial theme from localStorage or system preference
  const getInitialTheme = (): Theme => {
    if (!browser) return 'light';
    
    const stored = localStorage.getItem('theme') as Theme | null;
    if (stored) return stored;
    
    // Auto-detect time of day for driving
    const hour = new Date().getHours();
    return (hour < 6 || hour > 18) ? 'dark' : 'light';
  };
  
  const { subscribe, set, update } = writable<Theme>(getInitialTheme());
  
  return {
    subscribe,
    set: (theme: Theme) => {
      if (browser) {
        localStorage.setItem('theme', theme);
        document.documentElement.classList.toggle('dark', theme === 'dark');
      }
      set(theme);
    },
    toggle: () => {
      update(current => {
        const newTheme = current === 'light' ? 'dark' : 'light';
        if (browser) {
          localStorage.setItem('theme', newTheme);
          document.documentElement.classList.toggle('dark', newTheme === 'dark');
        }
        return newTheme;
      });
    },
    autoDetect: () => {
      const hour = new Date().getHours();
      const theme = (hour < 6 || hour > 18) ? 'dark' : 'light';
      if (browser) {
        localStorage.setItem('theme', theme);
        document.documentElement.classList.toggle('dark', theme === 'dark');
      }
      set(theme);
    }
  };
}

export const theme = createThemeStore();
```

**Usage:**
```svelte
<script lang="ts">
  import { theme } from '$lib/stores/theme';
  import { Sun, Moon } from 'lucide-svelte';
</script>

<button on:click={theme.toggle}>
  {#if $theme === 'light'}
    <Moon />
  {:else}
    <Sun />
  {/if}
</button>
```

**Auto-switching with interval:**
```svelte
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { theme } from '$lib/stores/theme';
  
  let interval: number;
  
  onMount(() => {
    // Check every hour and auto-switch
    interval = setInterval(() => {
      theme.autoDetect();
    }, 60 * 60 * 1000);
  });
  
  onDestroy(() => {
    clearInterval(interval);
  });
</script>
```

**Tailwind dark mode config:**
```javascript
// tailwind.config.js
export default {
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        // Light mode colors
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        // Add more theme colors
      }
    }
  }
}
```

```css
/* app.css */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
}
```

---

## Touch Interface Optimization

### Touch-Friendly Components

```css
/* Global touch styles in app.css */
.touch-target {
  @apply min-h-12 min-w-12 p-3;
}

.btn-touch {
  @apply h-14 px-6 text-lg font-semibold rounded-lg;
}

.driving-text {
  @apply text-lg md:text-xl;
}
```

### Gesture Support with Svelte Actions

```typescript
// lib/actions/gestures.ts
interface SwipeOptions {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  threshold?: number;
}

export function swipe(node: HTMLElement, options: SwipeOptions) {
  let startX: number;
  let startY: number;
  const threshold = options.threshold ?? 50;
  
  function handleTouchStart(e: TouchEvent) {
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
  }
  
  function handleTouchEnd(e: TouchEvent) {
    const endX = e.changedTouches[0].clientX;
    const endY = e.changedTouches[0].clientY;
    
    const deltaX = endX - startX;
    const deltaY = endY - startY;
    
    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > threshold) {
      if (deltaX > 0) options.onSwipeRight?.();
      else options.onSwipeLeft?.();
    } else if (Math.abs(deltaY) > threshold) {
      if (deltaY > 0) options.onSwipeDown?.();
      else options.onSwipeUp?.();
    }
  }
  
  node.addEventListener('touchstart', handleTouchStart);
  node.addEventListener('touchend', handleTouchEnd);
  
  return {
    destroy() {
      node.removeEventListener('touchstart', handleTouchStart);
      node.removeEventListener('touchend', handleTouchEnd);
    }
  };
}
```

**Usage:**
```svelte
<script lang="ts">
  import { swipe } from '$lib/actions/gestures';
  
  function nextTrack() {
    console.log('Next track');
  }
  
  function previousTrack() {
    console.log('Previous track');
  }
</script>

<div 
  use:swipe={{
    onSwipeLeft: nextTrack,
    onSwipeRight: previousTrack,
    threshold: 100
  }}
  class="map-container"
>
  Map content
</div>
```

### Long Press Action

```typescript
// lib/actions/longpress.ts
export function longpress(node: HTMLElement, duration: number = 500) {
  let timer: number;
  
  function handleMouseDown() {
    timer = setTimeout(() => {
      node.dispatchEvent(new CustomEvent('longpress'));
    }, duration);
  }
  
  function handleMouseUp() {
    clearTimeout(timer);
  }
  
  node.addEventListener('mousedown', handleMouseDown);
  node.addEventListener('touchstart', handleMouseDown);
  node.addEventListener('mouseup', handleMouseUp);
  node.addEventListener('touchend', handleMouseUp);
  
  return {
    destroy() {
      node.removeEventListener('mousedown', handleMouseDown);
      node.removeEventListener('touchstart', handleMouseDown);
      node.removeEventListener('mouseup', handleMouseUp);
      node.removeEventListener('touchend', handleMouseUp);
    }
  };
}

// Usage
<button 
  use:longpress={1000}
  on:longpress={() => console.log('Long pressed!')}
>
  Hold me
</button>
```

---

## Performance Optimization

### Code Splitting with SvelteKit

**Automatic route-based code splitting:**
```typescript
// SvelteKit automatically code-splits by route
// Each +page.svelte is a separate chunk

// For manual lazy loading:
<script lang="ts">
  let HeavyComponent;
  
  async function loadHeavyComponent() {
    const module = await import('$lib/components/HeavyComponent.svelte');
    HeavyComponent = module.default;
  }
</script>

{#if HeavyComponent}
  <svelte:component this={HeavyComponent} />
{:else}
  <button on:click={loadHeavyComponent}>Load Component</button>
{/if}
```

### Virtual Scrolling for Large Lists

```bash
npm install svelte-virtual
```

```svelte
<script lang="ts">
  import VirtualList from 'svelte-virtual';
  import type { Track } from '$lib/types';
  
  export let tracks: Track[];
</script>

<VirtualList items={tracks} let:item height="400px">
  <div class="track-item">
    <h3>{item.name}</h3>
    <p>{item.distance_km} km</p>
  </div>
</VirtualList>
```

**Alternative: svelte-tiny-virtual-list**

```bash
npm install svelte-tiny-virtual-list
```

```svelte
<script lang="ts">
  import VirtualList from 'svelte-tiny-virtual-list';
  
  export let tracks: Track[];
</script>

<VirtualList
  width="100%"
  height={400}
  itemCount={tracks.length}
  itemSize={80}
>
  <div slot="item" let:index let:style {style}>
    <div class="track-item">
      <h3>{tracks[index].name}</h3>
      <p>{tracks[index].distance_km} km</p>
    </div>
  </div>
</VirtualList>
```

### Map Performance Optimization

```svelte
<script lang="ts">
  import { debounce } from '$lib/utils';
  
  let map: maplibregl.Map;
  
  // Debounce expensive operations
  const updateMapBounds = debounce((bounds: any) => {
    fetchTracksInBounds(bounds);
  }, 300);
  
  function handleMapMove() {
    const bounds = map.getBounds();
    updateMapBounds(bounds);
  }
  
  onMount(() => {
    map = new maplibregl.Map({...});
    map.on('moveend', handleMapMove);
  });
</script>
```

```typescript
// lib/utils.ts
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: number;
  
  return function(...args: Parameters<T>) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}
```

### Simplify Track Geometries

```bash
npm install @turf/simplify
```

```typescript
import simplify from '@turf/simplify';

// Simplify before rendering
const simplifiedTrack = simplify(trackGeoJSON, {
  tolerance: 0.0001,
  highQuality: false
});
```

### Image Optimization

```svelte
<script lang="ts">
  // Use srcset for responsive images
</script>

<img
  src="/images/map-marker.png"
  srcset="/images/map-marker@2x.png 2x, /images/map-marker@3x.png 3x"
  alt="Map marker"
  loading="lazy"
/>
```

### Lazy Loading Images

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  
  let imageElement: HTMLImageElement;
  let loaded = false;
  
  onMount(() => {
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
          loaded = true;
          observer.disconnect();
        }
      });
      
      observer.observe(imageElement);
      
      return () => observer.disconnect();
    } else {
      loaded = true;
    }
  });
</script>

<img
  bind:this={imageElement}
  src={loaded ? actualSrc : placeholder}
  alt="Track preview"
/>
```

---

## Build & Development Tools

### SvelteKit Configuration

```typescript
// svelte.config.js
import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  
  kit: {
    adapter: adapter(),
    alias: {
      $lib: './src/lib',
      $components: './src/lib/components'
    }
  }
};

export default config;
```

### Vite Configuration

```typescript
// vite.config.ts
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'maplibre': ['maplibre-gl'],
          'turf': ['@turf/turf'],
        }
      }
    }
  }
});
```

### TypeScript Configuration

```json
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "paths": {
      "$lib": ["./src/lib"],
      "$lib/*": ["./src/lib/*"]
    }
  }
}
```

---

## Testing Strategy

### Testing Framework Setup

```bash
npm install -D vitest @testing-library/svelte @testing-library/jest-dom jsdom
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte({ hot: !process.env.VITEST })],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/tests/setup.ts']
  }
});
```

```typescript
// src/tests/setup.ts
import '@testing-library/jest-dom';
```

### Unit Testing Example

```typescript
// TrackItem.test.ts
import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import TrackItem from '$lib/components/TrackItem.svelte';

describe('TrackItem', () => {
  it('renders track name', () => {
    render(TrackItem, {
      props: {
        track: {
          id: 1,
          name: 'Morning Commute',
          distance_km: 15.5,
        }
      }
    });
    
    expect(screen.getByText('Morning Commute')).toBeInTheDocument();
    expect(screen.getByText('15.5 km')).toBeInTheDocument();
  });
});
```

### Component Testing with User Events

```typescript
import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import Button from '$lib/components/ui/Button.svelte';

describe('Button', () => {
  it('calls onClick when clicked', async () => {
    const onClick = vi.fn();
    
    render(Button, {
      props: { onClick }
    });
    
    const button = screen.getByRole('button');
    await fireEvent.click(button);
    
    expect(onClick).toHaveBeenCalledOnce();
  });
});
```

### Testing Stores

```typescript
// stores/gps.test.ts
import { describe, it, expect } from 'vitest';
import { get } from 'svelte/store';
import { gpsPosition, updatePosition } from '$lib/stores/gps';

describe('GPS Store', () => {
  it('updates position', () => {
    updatePosition({
      lat: 45.5,
      lon: -122.6,
      speed: 60,
      heading: 180,
      timestamp: new Date()
    });
    
    const position = get(gpsPosition);
    expect(position?.lat).toBe(45.5);
    expect(position?.lon).toBe(-122.6);
  });
});
```

### E2E Testing with Playwright

```bash
npm install -D @playwright/test
```

```typescript
// tests/import.test.ts
import { test, expect } from '@playwright/test';

test('imports GPX file', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await page.click('text=Import Track');
  
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles('tests/fixtures/test-track.gpx');
  
  await expect(page.locator('text=Import successful')).toBeVisible();
});
```

---

## Error Handling

### Error Boundary with SvelteKit

```svelte
<!-- +error.svelte -->
<script lang="ts">
  import { page } from '$app/stores';
  
  function reload() {
    window.location.reload();
  }
</script>

<div class="error-container">
  <h1>Oops! Something went wrong</h1>
  <p>{$page.error?.message || 'An unexpected error occurred'}</p>
  <button on:click={reload}>Reload App</button>
</div>

<style>
  .error-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 2rem;
    text-align: center;
  }
</style>
```

### Custom Error Handler

```typescript
// hooks.client.ts
import type { HandleClientError } from '@sveltejs/kit';
import { toast } from 'svelte-sonner';

export const handleError: HandleClientError = ({ error, event }) => {
  console.error('Error:', error, event);
  
  // Show user-friendly toast notification
  if (error instanceof Error) {
    if (error.message.includes('GPS')) {
      toast.error('GPS Error', {
        description: 'Unable to get GPS position'
      });
    } else if (error.message.includes('Network')) {
      toast.error('Connection Error', {
        description: 'Check your network connection'
      });
    } else {
      toast.error('Error', {
        description: error.message
      });
    }
  }
  
  return {
    message: 'An error occurred'
  };
};
```

### API Error Handling

```typescript
// lib/api.ts
import { error } from '@sveltejs/kit';
import { toast } from 'svelte-sonner';

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(`/api${endpoint}`, options);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw error(response.status, errorData.message || 'API request failed');
    }
    
    return response.json();
  } catch (err) {
    if (err instanceof Error) {
      toast.error('Request failed', {
        description: err.message
      });
    }
    throw err;
  }
}
```

---

## Project Structure

```
src/
├── routes/
│   ├── +layout.svelte            # Root layout
│   ├── +layout.ts                # Root layout data
│   ├── +page.svelte              # / (map view - touch interface)
│   ├── +page.ts                  # Map view data
│   ├── settings/
│   │   └── +page.svelte          # /settings
│   ├── dashboard/
│   │   ├── +page.svelte          # /dashboard
│   │   └── +page.ts              # Dashboard data
│   ├── tracks/
│   │   ├── +page.svelte          # /tracks list
│   │   ├── +page.ts              # Load tracks
│   │   └── [id]/
│   │       ├── +page.svelte      # /tracks/123
│   │       └── +page.ts          # Load single track
│   ├── import/
│   │   └── +page.svelte          # /import
│   └── api/                      # API routes (if using SvelteKit endpoints)
│       ├── tracks/
│       │   └── +server.ts
│       └── gps/
│           └── +server.ts
├── lib/
│   ├── components/
│   │   ├── ui/                   # shadcn-svelte components
│   │   │   ├── button.svelte
│   │   │   ├── card.svelte
│   │   │   ├── dialog.svelte
│   │   │   └── ...
│   │   ├── map/
│   │   │   ├── MapView.svelte
│   │   │   ├── TrackLayer.svelte
│   │   │   └── APRSMarkers.svelte
│   │   ├── tracks/
│   │   │   ├── TrackList.svelte
│   │   │   ├── TrackItem.svelte
│   │   │   └── TrackImport.svelte
│   │   ├── dashboard/
│   │   │   ├── SystemHealth.svelte
│   │   │   └── Statistics.svelte
│   │   └── layout/
│   │       ├── Header.svelte
│   │       └── Sidebar.svelte
│   ├── stores/
│   │   ├── gps.ts
│   │   ├── tracks.ts
│   │   ├── aprs.ts
│   │   ├── theme.ts
│   │   └── ui.ts
│   ├── actions/
│   │   ├── gestures.ts           # Swipe, longpress actions
│   │   ├── map.ts                # Map-related actions
│   │   └── websocket.ts          # WebSocket action
│   ├── utils/
│   │   ├── api.ts                # API client
│   │   ├── mapUtils.ts           # Map helper functions
│   │   ├── geoUtils.ts           # Geospatial calculations
│   │   └── formatters.ts         # Data formatting
│   └── types/
│       ├── gps.ts
│       ├── track.ts
│       ├── aprs.ts
│       └── api.ts
├── app.html                      # HTML template
├── app.css                       # Global styles
└── hooks.client.ts               # Client hooks

---

## Recommended Full Stack

```
Core Framework:
├── Svelte 4+ (or Svelte 5 with runes)
├── SvelteKit 2+ (routing, SSR, API routes)
├── TypeScript 5+
└── Vite (built into SvelteKit)

Map Visualization:
├── MapLibre GL JS (direct integration)
├── @turf/turf (geospatial operations)
└── Custom Svelte actions for map control

UI Components:
├── shadcn-svelte (component library)
├── Tailwind CSS (styling)
├── Bits UI (accessible primitives)
└── lucide-svelte (icons)

State Management:
├── Svelte Stores (built-in, writable/readable/derived)
├── SvelteKit load functions (page data)
└── Custom stores for complex state

Real-Time:
├── Native WebSocket API
└── Custom Svelte actions for WebSocket

Data Fetching:
├── SvelteKit load functions (SSR data loading)
├── Native fetch API
└── @tanstack/svelte-query (optional, for advanced caching)

Forms:
├── Svelte native forms (two-way binding)
├── SvelteKit form actions (progressive enhancement)
├── Felte (optional, for complex forms)
└── Zod (schema validation)

Utilities:
├── clsx (conditional classnames)
├── zod (schema validation)
├── svelte-sonner (notifications)
└── Native file input (file upload)

Testing:
├── Vitest (unit tests)
├── @testing-library/svelte (component tests)
├── Playwright (E2E tests)
└── MSW (API mocking, optional)

Developer Tools:
├── ESLint (linting)
├── Prettier (code formatting)
├── svelte-check (type checking)
└── Husky (git hooks)

PWA:
└── @vite-pwa/sveltekit (service worker)
```

---

## Performance Targets

### Loading Performance
- Initial page load: < 3 seconds
- Time to Interactive (TTI): < 5 seconds
- First Contentful Paint (FCP): < 1.5 seconds
- Map render time: < 2 seconds

### Runtime Performance
- 60 FPS for map animations
- < 100ms response to user input
- GPS update processing: < 50ms
- Track layer rendering: < 500ms for 10 tracks

### Bundle Size
- Main bundle: < 300KB (gzipped)
- Map vendor chunk: < 500KB (gzipped)
- Total initial load: < 1MB (gzipped)
- Lazy-loaded routes: < 100KB each

---

## Mobile Responsiveness

### Breakpoints

```typescript
// tailwind.config.js
module.exports = {
  theme: {
    screens: {
      'sm': '640px',    // Small phones
      'md': '768px',    // Tablets
      'lg': '1024px',   // Small laptops
      'xl': '1280px',   // Desktops
      'touch': { 'raw': '(hover: none)' },  // Touch devices
    }
  }
}
```

### Adaptive Layouts

```typescript
function MapView() {
  const isMobile = useMediaQuery('(max-width: 768px)');
  
  return (
    <div className={isMobile ? 'mobile-layout' : 'desktop-layout'}>
      {isMobile ? <MobileControls /> : <DesktopControls />}
      <Map />
    </div>
  );
}
```

---

## Security Considerations

### XSS Prevention
- React escapes content by default
- Sanitize any dangerouslySetInnerHTML usage
- Validate all user inputs

### API Security
```typescript
// Add CSRF token to requests
const api = axios.create({
  baseURL: '/api',
  headers: {
    'X-CSRF-Token': getCsrfToken(),
  },
});
```

### Content Security Policy
```html
<!-- index.html -->
<meta http-equiv="Content-Security-Policy" 
  content="default-src 'self'; 
           script-src 'self' 'unsafe-inline'; 
           style-src 'self' 'unsafe-inline';
           img-src 'self' data: https://*.openstreetmap.org;">
```

---

## Deployment

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### SvelteKit Adapters

**For Node.js server:**
```bash
npm install -D @sveltejs/adapter-node
```

```typescript
// svelte.config.js
import adapter from '@sveltejs/adapter-node';

export default {
  kit: {
    adapter: adapter()
  }
};
```

**For static site (if no SSR needed):**
```bash
npm install -D @sveltejs/adapter-static
```

```typescript
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: 'index.html'
    })
  }
};
```

### nginx Configuration

```nginx
server {
    listen 80;
    server_name carputer.local;
    root /var/www/carputer/build;
    index index.html;

    # For static adapter
    location / {
        try_files $uri $uri/ /index.html;
    }

    # For node adapter - proxy to SvelteKit server
    # location / {
    #     proxy_pass http://localhost:3000;
    #     proxy_http_version 1.1;
    #     proxy_set_header Upgrade $http_upgrade;
    #     proxy_set_header Connection 'upgrade';
    #     proxy_set_header Host $host;
    #     proxy_cache_bypass $http_upgrade;
    # }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## Development Workflow

### Package Scripts

```json
{
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:e2e": "playwright test",
    "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
    "check:watch": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json --watch",
    "lint": "eslint .",
    "format": "prettier --write ."
  }
}
```

### Pre-commit Hooks with Husky

```bash
npm install -D husky lint-staged
npx husky install
```

```bash
# .husky/pre-commit
npm run check
npm run lint
npm run format
npm run test
```

```json
// package.json
{
  "lint-staged": {
    "*.{js,ts,svelte}": [
      "eslint --fix",
      "prettier --write"
    ]
  }
}
```

---

## Security Considerations

### XSS Prevention
- Svelte escapes content by default
- Use `{@html}` only with sanitized content
- Validate all user inputs

### API Security
```typescript
// lib/api.ts
import { browser } from '$app/environment';

export async function apiRequest(endpoint: string, options?: RequestInit) {
  // Add CSRF token if in browser
  const headers = new Headers(options?.headers);
  if (browser) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (csrfToken) {
      headers.set('X-CSRF-Token', csrfToken);
    }
  }
  
  return fetch(endpoint, {
    ...options,
    headers
  });
}
```

### Content Security Policy

```typescript
// hooks.server.ts
export const handle = async ({ event, resolve }) => {
  const response = await resolve(event);
  
  response.headers.set(
    'Content-Security-Policy',
    "default-src 'self'; " +
    "script-src 'self' 'unsafe-inline'; " +
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data: https://*.openstreetmap.org;"
  );
  
  return response;
};
```

---

## Next Steps

1. **Initialize project**
   ```bash
   npm create svelte@latest carputer-frontend
   cd carputer-frontend
   npm install
   npx shadcn-svelte@latest init
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

2. **Install core dependencies**
   ```bash
   npm install maplibre-gl @turf/turf
   npm install zod
   npm install svelte-sonner
   npm install lucide-svelte
   ```

3. **Implement map view**
   - Create MapView component with MapLibre GL JS
   - Add current position marker
   - Implement track layers with Svelte stores

4. **Build UI components**
   - Set up shadcn-svelte components
   - Create reusable components
   - Implement dark mode with Svelte stores

5. **Real-time GPS integration**
   - WebSocket connection with Svelte action
   - Svelte stores for GPS state
   - Position updates and reactivity

6. **Track management**
   - Track list and detail views with SvelteKit routing
   - Import/export functionality
   - Track filtering and search

7. **Dashboard development**
   - System health widgets
   - Statistics displays
   - Settings management with SvelteKit form actions

8. **Testing & optimization**
   - Unit and component tests with Vitest
   - Performance profiling
   - Bundle size optimization

---

## Additional Resources

- **Svelte Documentation:** https://svelte.dev/docs
- **SvelteKit Documentation:** https://kit.svelte.dev/docs
- **TypeScript Handbook:** https://www.typescriptlang.org/docs/
- **MapLibre GL JS:** https://maplibre.org/
- **Tailwind CSS:** https://tailwindcss.com/
- **shadcn-svelte:** https://www.shadcn-svelte.com/
- **Svelte Society:** https://sveltesociety.dev/
- **Bits UI:** https://www.bits-ui.com/
- **Vite:** https://vitejs.dev/
- **Vitest:** https://vitest.dev/
