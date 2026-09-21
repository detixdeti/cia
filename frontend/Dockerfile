FROM node:24-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173
# --host macht den Entwicklungsserver ausserhalb des Containers erreichbar.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
