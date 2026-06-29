# MASDojo frontend. Builds the Vite SPA and serves it on :5173.
FROM node:20-alpine

WORKDIR /app

# Install dependencies first for layer caching. Use a reproducible, lockfile-
# pinned install.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Build-time API base URL can be overridden at build or run time.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

EXPOSE 5173

# `vite preview` serves the production build; host flag exposes it on the network.
CMD ["npm", "run", "preview", "--", "--port", "5173", "--host"]
