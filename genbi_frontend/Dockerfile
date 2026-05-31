FROM node:20-alpine

# Chromium natif Alpine requis pour Playwright (musl libc, ARM64 compatible)
RUN apk add --no-cache chromium

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
