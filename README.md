# Inventory Scanner Pro

A modern inventory management system with real-time BOM verification using iOS native scanning.

## Architecture

### iOS Native App
- **Technology**: Swift, SwiftUI, VisionKit (DataScannerViewController)
- **Features**:
  - Real-time text scanning (Article # and PO #)
  - Inventory Mode & BOM Mode
  - Category selection (CCTV, CX, FIRE & BURG ALARM)
  - Manual article entry
  - Visual feedback (Green=Match, Orange=Difference)
  - Quantity management

### Backend API
- **Technology**: FastAPI, SQLAlchemy, SQLite
- **Features**:
  - RESTful API endpoints
  - Server-Sent Events (SSE) for real-time updates
  - Excel (XLSX) file upload and parsing
  - JWT authentication
  - Multi-user support

### Web Panel
- **Technology**: Next.js 14, TypeScript, TailwindCSS, shadcn/ui
- **Features**:
  - Real-time scanning feed
  - Article database management (Excel upload)
  - BOM management by category
  - Inventory vs BOM comparison
  - Match/Over/Under reporting
  - Session history

## Project Structure

```
inventory-scanner-pro/
├── ios-app/              # iOS Native App
├── backend/              # FastAPI Backend
├── web-panel/            # Next.js Web Panel
└── README.md
```

## Workflow

1. **Setup**: Upload article database (XLSX) to panel
2. **BOM Upload**: Upload BOM file for specific category
3. **Scanning**: Use iOS app to scan article labels
4. **Real-time Sync**: Scans appear instantly in web panel
5. **Comparison**: System compares scanned quantity vs BOM quantity
6. **Reporting**: View match status and discrepancies

## Data Models

### Article Database
- SAP Article
- Part Number
- Description
- Category

### BOM File
- SAP Article
- Part Number
- Description
- Quantity

### Inventory Record (Generated)
- SAP Article
- Part Number
- Description
- Quantity (from BOM)
- Quantity Inventory (scanned count)
- Status (Match/Over/Under)

## Getting Started

**Quick Start:** See [QUICKSTART.md](QUICKSTART.md) for 5-minute setup

**Detailed Setup:** See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete instructions

**Individual Components:**
- Backend: [backend/README.md](backend/README.md)
- Web Panel: [web-panel/README.md](web-panel/README.md)
- iOS App: [ios-app/README.md](ios-app/README.md)

## Key Features

### iOS App
- ✅ VisionKit DataScanner for real-time text recognition
- ✅ Automatic extraction of Article # and PO #
- ✅ Manual entry fallback
- ✅ BOM vs Inventory comparison mode
- ✅ Visual feedback (Green=Match, Orange=Difference)
- ✅ Category management (CCTV, CX, FIRE & BURG ALARM)

### Web Panel
- ✅ Real-time scanning feed via Server-Sent Events (SSE)
- ✅ Article database management with Excel upload
- ✅ BOM management by category
- ✅ Session analysis with match/difference reporting
- ✅ Modern UI with TailwindCSS and shadcn/ui

### Backend API
- ✅ FastAPI with automatic OpenAPI docs
- ✅ JWT authentication
- ✅ SQLAlchemy ORM with SQLite (PostgreSQL ready)
- ✅ Real-time SSE support
- ✅ Excel file parsing (XLSX)
- ✅ Multi-user session support

## API Endpoints

See interactive documentation at http://localhost:8000/docs

## Excel File Formats

### Article Database
Required columns: `SAP Article`, `Part Number`, `Description`, `Category`

### BOM Files
Required columns: `SAP Article`, `Part Number`, `Description`, `Quantity`

## Label Format

The iOS scanner recognizes these patterns:
```
PO # 12345678
Article # 87654321
```

## Technology Stack

- **iOS**: Swift, SwiftUI, VisionKit (iOS 16+)
- **Backend**: Python 3.9+, FastAPI, SQLAlchemy, SSE-Starlette
- **Web Panel**: Next.js 14, TypeScript, TailwindCSS, shadcn/ui
- **Real-time**: Server-Sent Events (SSE)
- **Database**: SQLite (development), PostgreSQL (production)
- **Deployment**: Google App Engine ready
