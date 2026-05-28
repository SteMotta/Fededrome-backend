# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Dipendenze di sistema (rimosso curl per ottimizzare l'immagine)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Dipendenze Python (separato dal COPY . . per sfruttare la cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn uvicorn

# Codice applicativo
COPY . .

EXPOSE 8000

# Produzione: 2 worker Gunicorn + Uvicorn worker class
# Corretto: rimosse le backslash non valide per la sintassi JSON di CMD e rimosso il flag --proxy-headers non supportato da Gunicorn
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "2", "--bind", "0.0.0.0:8000", "--forwarded-allow-ips", "*", "--access-logfile", "-", "--error-logfile", "-"]