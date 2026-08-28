#!/bin/bash
# ngrok-start.sh — tunnel frontend uniquement via proxy Vite → backend interne
# Usage : ./ngrok-start.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$PROJECT_DIR/.env"

echo "🔌 Arrêt des tunnels ngrok existants..."
pkill -f "ngrok http" 2>/dev/null || true
sleep 1

echo "🚇 Démarrage du tunnel frontend (:5173)..."
ngrok http 5173 --log=stdout > /tmp/ngrok.log 2>&1 &

echo "⏳ Attente de l'API locale ngrok..."
for i in $(seq 1 20); do
    sleep 1
    TUNNELS=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null)
    COUNT=$(echo "$TUNNELS" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('tunnels',[])))" 2>/dev/null || echo "0")
    if [ "$COUNT" -ge 1 ]; then break; fi
    if [ "$i" -eq 20 ]; then
        echo "❌ Timeout — ngrok n'a pas démarré. Voir /tmp/ngrok.log"
        exit 1
    fi
done

echo "🔍 Récupération de l'URL..."
FRONTEND_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
tunnels = json.load(sys.stdin)['tunnels']
for t in tunnels:
    if t['proto'] == 'https':
        print(t['public_url'])
        break
" 2>/dev/null)

if [ -z "$FRONTEND_URL" ]; then
    echo "❌ URL ngrok introuvable. Voir /tmp/ngrok.log"
    tail -20 /tmp/ngrok.log
    exit 1
fi

echo "✅ Frontend : $FRONTEND_URL"

echo ""
echo "📝 Mise à jour de .env (proxy Vite → backend interne)..."
cat > "$ENV_FILE" << EOF
# GenBI — variables d'environnement (généré par ngrok-start.sh le $(date))
# Mode ngrok : PUBLIC_API_URL vide = appels relatifs /api → proxy Vite → genbi-backend:8000

PUBLIC_API_URL=
CORS_ORIGINS=http://localhost:5173,${FRONTEND_URL}
EOF

echo "🔄 Recréation des conteneurs (pour appliquer les nouvelles env vars)..."
cd "$PROJECT_DIR"
docker compose up -d --force-recreate genbi-backend genbi-frontend

sleep 8

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 GenBI est accessible depuis n'importe où :"
echo "   $FRONTEND_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📌 Partage ce lien avec l'autre ordinateur."
echo "   (Premier accès : cliquer 'Visit Site' sur la page ngrok)"
echo ""
echo "⚠️  Pour arrêter : pkill -f 'ngrok http'"
echo "   Puis restaurer le mode local : docker compose restart"
