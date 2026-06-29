# MASDojo frontend. Builds the Vite SPA and serves it on :5173.
FROM node:20-alpine

WORKDIR /app

# Install dependencies first for layer caching. Use a reproducible, lockfile-
# pinned install.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Build-time ONLY: Vite inlines VITE_API_BASE_URL during `npm run build`, so a
# runtime env has no effect — set it as a build arg (see docker-compose.yml).
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

EXPOSE 5173

# `vite preview` serves the production build; host flag exposes it on the network.
CMD ["npm", "run", "preview", "--", "--port", "5173", "--host"]
