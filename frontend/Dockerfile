FROM node:20-alpine
WORKDIR /app

COPY package.json package.json
COPY package-lock.json package-lock.json

RUN npm ci

COPY . .
RUN npm run build
RUN npm install --global serve

CMD ["npx", "-y", "serve", "-s", "build", "-p", "8000"]
