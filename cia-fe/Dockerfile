# 1. Build the React app
FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# 2. Serve the built files with nginx, which also forwards /api to the backend
FROM nginx:alpine

# openssl creates the password hash in basic-auth.sh
RUN apk add --no-cache openssl

# Defaults for docker compose, Render overrides them
ENV PORT=80
ENV BACKEND_HOSTPORT=backend:8000

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY basic-auth.sh /docker-entrypoint.d/40-basic-auth.sh
RUN chmod +x /docker-entrypoint.d/40-basic-auth.sh
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
