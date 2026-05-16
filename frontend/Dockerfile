# Build Stage
FROM node:20-alpine AS builder
WORKDIR /app/frontend

ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_GATEWAY_WS_URL=ws://localhost:8000/ws/telemetry/
ARG VITE_ML_BASE_URL=http://localhost:8001

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_GATEWAY_WS_URL=$VITE_GATEWAY_WS_URL
ENV VITE_ML_BASE_URL=$VITE_ML_BASE_URL

COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
COPY shared/ ../shared/
RUN npm run build

# Production Stage
FROM nginx:alpine
COPY --from=builder /app/frontend/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
