# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Create a startup script to handle PORT env variable
RUN echo $'#!/bin/sh\n\
  sed -i "s|__GEMINI_API_KEY__|$GEMINI_API_KEY|g" /usr/share/nginx/html/index.html\n\
  sed -i "s/listen 8080;/listen $PORT;/" /etc/nginx/nginx.conf\n\
  nginx -g "daemon off;"' > /start.sh && chmod +x /start.sh

# Expose port (Cloud Run will override this with PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:${PORT:-8080}/health || exit 1

# Start nginx
CMD ["/start.sh"]
