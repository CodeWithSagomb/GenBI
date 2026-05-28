from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="GenBI Backend API",
    description="API de génération et d'exécution SQL gouvernée et sécurisée pour la Business Intelligence Générative.",
    version="1.0.0"
)

# Configuration de CORS pour permettre au frontend React de se connecter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Bienvenue sur l'API GenBI ! Accédez à la documentation sur /docs"
    }

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
