#!/bin/bash
set -e

echo "🚀 Fededrome Deploy — $(date)"

# Pull dell'ultimo codice dal repository
git pull origin main

# Rebuild dell'immagine FastAPI
docker compose build --no-cache fastapi

# Riavvio con downtime quasi-nullo (near-zero-downtime)
# --no-deps: non ricrea Redis e Nginx se non cambiati
docker compose up -d --no-deps fastapi

# Ricarica Nginx per ri-risolvere l'IP del nuovo container FastAPI ed evitare errori 502
docker compose exec nginx nginx -s reload 2>/dev/null || true

# Pulizia immagini non più usate
docker image prune -f

echo "✅ Deploy completato"
docker compose ps