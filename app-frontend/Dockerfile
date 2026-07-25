# ---- build ----
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite вшивает VITE_*-переменные в бандл на этапе сборки (не в рантайме) —
# поэтому это build ARG, а не обычная env-переменная контейнера.
ARG VITE_API_BASE_URL
ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_GOOGLE_CLIENT_ID=${VITE_GOOGLE_CLIENT_ID}

RUN npm run build

# ---- runtime ----
FROM nginx:1.27-alpine

RUN adduser -D -H -u 1000 appuser \
    && chown -R appuser:appuser /var/cache/nginx /var/run /var/log/nginx \
    && touch /var/run/nginx.pid \
    && chown appuser:appuser /var/run/nginx.pid

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

USER appuser
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:8080/health || exit 1
