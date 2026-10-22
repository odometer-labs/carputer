# =============================================================================
# Carputer Frontend (Svelte + Vite)
# =============================================================================
# Multi-stage build: build static assets, then serve with nginx
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - install deps and build static assets
# -----------------------------------------------------------------------------
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files first for better layer caching
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build production assets
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Runtime - serve with nginx
# -----------------------------------------------------------------------------
FROM nginx:alpine AS runtime

# Copy custom nginx config for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# nginx runs on port 80 by default
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
