FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système nécessaires pour compiler psycopg2 si besoin
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

EXPOSE 8000

# Lancement du serveur uvicorn avec rechargement automatique en développement
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
