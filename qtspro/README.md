# QTS Pro Platform

Este proyecto contiene la plataforma de backend y frontend para QTS Pro.

## Estructura

- `backend-api/`: API de FastAPI que gestiona los escaneos y los eventos en tiempo real (SSE).
- `frontend/`: Panel de control en Next.js que visualiza los datos.

## Cómo Ejecutar el Entorno Local

### 1. Iniciar el Backend

Abre una terminal y ejecuta los siguientes comandos:

```bash
cd backend-api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

El servidor de la API estará disponible en `http://localhost:8000`.

### 2. Iniciar el Frontend

Abre una **segunda** terminal y ejecuta:

```bash
cd frontend
npm run dev
```

El panel de control estará disponible en `http://localhost:3000/app`.

### 3. Probar el Flujo End-to-End

Para simular un escaneo desde un dispositivo, abre una **tercera** terminal y ejecuta el siguiente comando `curl`:

```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"po_number":"PO-DEMO","sap_article":"110-AX23","store_id":"WM3436","qty":1,"device_id":"dev-local","idempotency_key":"demo-1","source":"ios-live-text"}'
```

Deberías ver el evento aparecer instantáneamente en el panel en `http://localhost:3000/app`.
