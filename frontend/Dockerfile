# Production Multi-Stage Dockerfile for FixIt React/Vite Frontend
# Stage 1: Build static assets
FROM node:20-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
ARG VITE_PUBLIC_REGISTRATION_ENABLED=false
ARG VITE_DEMO_MODE_ENABLED=false
ENV VITE_PUBLIC_REGISTRATION_ENABLED=${VITE_PUBLIC_REGISTRATION_ENABLED} \
    VITE_DEMO_MODE_ENABLED=${VITE_DEMO_MODE_ENABLED}
RUN npm run build

# Stage 2: Serve via Nginx
FROM nginx:alpine as runner

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
