# Multi-stage build for React Vite Frontend
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency definitions
COPY frontend/package.json frontend/pnpm-lock.yaml* frontend/package-lock.json* ./

# Install dependencies
RUN if [ -f pnpm-lock.yaml ]; then npm install -g pnpm && pnpm install --frozen-lockfile; \
    elif [ -f package-lock.json ]; then npm ci; \
    else npm install; fi

# Copy frontend source code
COPY frontend/ .

# Build Vite static bundle
ARG VITE_API_BASE=""
ENV VITE_API_BASE=$VITE_API_BASE

RUN npm run build

# Serve with Nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
