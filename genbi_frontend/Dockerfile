FROM node:20-alpine

WORKDIR /app

# Copie et installation des packages Node
COPY package.json .
RUN npm install

# Copie de l'intégralité du code frontend
COPY . .

EXPOSE 5173

# Démarrage du serveur de développement Vite
CMD ["npm", "run", "dev"]
