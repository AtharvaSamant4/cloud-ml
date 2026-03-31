FROM node:20-slim AS builder
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* bun.lockb* ./
RUN \
  if [ -f package-lock.json ]; then npm ci; \
  elif [ -f pnpm-lock.yaml ]; then npm install -g pnpm && pnpm install --frozen-lockfile; \
  elif [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
  elif [ -f bun.lockb ]; then npm install -g bun && bun install --frozen-lockfile; \
  else npm install; fi

# Copy source
COPY . .

# Build Next.js app
RUN npm run build || yarn build || pnpm build || bun run build

# --- Runtime image ---
FROM node:20-slim AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy only the built output and minimal files
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.ts ./next.config.ts
COPY --from=builder /app/tsconfig.json ./tsconfig.json

# Install production deps only
RUN npm install --omit=dev || yarn install --production || pnpm install --prod || bun install --production

EXPOSE 3000

CMD ["npm", "run", "start"]
