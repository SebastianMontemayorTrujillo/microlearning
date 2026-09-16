FROM node:22-bookworm-slim AS build
WORKDIR /app/frontend
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ENV BACKEND_URL=http://backend:8000
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-bookworm-slim
WORKDIR /app/frontend
ENV NODE_ENV=production
ENV BACKEND_URL=http://backend:8000
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=build /app/frontend/.next ./.next
COPY --from=build /app/frontend/node_modules ./node_modules
COPY --from=build /app/frontend/package.json ./package.json
COPY --from=build /app/frontend/next.config.ts ./next.config.ts
EXPOSE 3000
CMD ["./node_modules/.bin/next", "start", "--hostname", "0.0.0.0", "--port", "3000"]
