# Inventory Scanner Pro - Backend API

FastAPI backend with real-time SSE updates, Excel file processing, and BOM comparison logic.

## Features

- **Authentication**: JWT-based authentication
- **Article Database**: Upload and manage article database from Excel
- **BOM Management**: Upload and manage BOMs by category
- **Scan Sessions**: Create and manage inventory/BOM scan sessions
- **Real-time Updates**: Server-Sent Events (SSE) for live scanning feed
- **BOM Comparison**: Automatic comparison of scanned vs expected quantities

## Setup

1. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and set SECRET_KEY
```

4. **Run the server**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Articles
- `POST /articles/upload` - Upload article database (Excel)
- `GET /articles/` - Get all articles (with filters)
- `GET /articles/{sap_article}` - Get specific article
- `GET /articles/stats/count` - Get article statistics

### BOMs
- `POST /boms/upload` - Upload BOM file (Excel)
- `GET /boms/` - Get all BOMs (with category filter)
- `GET /boms/{bom_id}` - Get specific BOM
- `GET /boms/{bom_id}/items` - Get BOM items
- `DELETE /boms/{bom_id}` - Delete BOM

### Scanning
- `POST /scan/sessions` - Create scan session
- `GET /scan/sessions` - Get user's scan sessions
- `GET /scan/sessions/{session_id}` - Get specific session
- `POST /scan/sessions/{session_id}/end` - End session
- `POST /scan/records` - Create scan record
- `GET /scan/sessions/{session_id}/records` - Get session records
- `GET /scan/sessions/{session_id}/summary` - Get session summary with comparison

### Events (SSE)
- `GET /events/stream?session_id={id}` - SSE stream for real-time updates

## Excel File Formats

### Article Database
Columns: `SAP Article`, `Part Number`, `Description`, `Category`

### BOM File
Columns: `SAP Article`, `Part Number`, `Description`, `Quantity`

## Database Schema

- **users**: User accounts
- **articles**: Article database
- **boms**: BOM files
- **bom_items**: Items in each BOM
- **scan_sessions**: Scanning sessions
- **scan_records**: Individual scan records

## Deployment to Google App Engine

1. Create `app.yaml`:
```yaml
runtime: python39
entrypoint: uvicorn app.main:app --host 0.0.0.0 --port $PORT

env_variables:
  SECRET_KEY: "your-production-secret-key"
```

2. Deploy:
```bash
gcloud app deploy
```
