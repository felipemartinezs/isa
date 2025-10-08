# Inventory Scanner Pro - Complete Setup Guide

This guide will walk you through setting up the complete inventory scanning system from scratch.

## System Overview

The system consists of three main components:
1. **Backend API** (FastAPI) - Handles data, authentication, and real-time events
2. **Web Panel** (Next.js) - Management interface for viewing scans and managing BOMs
3. **iOS App** (Swift/SwiftUI) - Mobile scanner using VisionKit

## Prerequisites

### Backend
- Python 3.9+
- pip

### Web Panel
- Node.js 18+
- npm or yarn

### iOS App
- macOS with Xcode 15+
- iOS device with iOS 16+ (for VisionKit)

## Step 1: Backend Setup

### 1.1 Navigate to Backend Directory
```bash
cd backend
```

### 1.2 Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 1.3 Install Dependencies
```bash
pip install -r requirements.txt
```

### 1.4 Configure Environment
```bash
cp .env.example .env
```

Edit `.env` and set a secure SECRET_KEY:
```
SECRET_KEY=your-very-secure-random-secret-key
```

### 1.5 Start Backend Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### 1.6 Create First User
Using the API docs at `/docs`, register a user:
```json
POST /auth/register
{
  "username": "admin",
  "email": "admin@example.com",
  "password": "your-password"
}
```

## Step 2: Web Panel Setup

### 2.1 Navigate to Web Panel Directory
```bash
cd ../web-panel
```

### 2.2 Install Dependencies
```bash
npm install
```

### 2.3 Configure Environment
```bash
cp .env.example .env.local
```

Edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2.4 Start Development Server
```bash
npm run dev
```

The web panel will be available at: `http://localhost:3000`

### 2.5 Login and Setup
1. Open `http://localhost:3000`
2. Login with the credentials you created
3. Navigate to "Article Database" tab
4. Upload your article database Excel file (columns: SAP Article, Part Number, Description, Category)
5. Navigate to "BOM Management" tab
6. Upload BOM files for each category (columns: SAP Article, Part Number, Description, Quantity)

## Step 3: iOS App Setup

### 3.1 Open in Xcode
```bash
cd ../ios-app
open InventoryScannerPro.xcodeproj
```

### 3.2 Configure Backend URL

Edit `InventoryScannerPro/Services/APIService.swift`:

For local development (Mac and iPhone on same Wi-Fi):
```swift
private let baseURL = "http://YOUR-MAC-IP:8000"
```

Find your Mac's IP:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

For production:
```swift
private let baseURL = "https://your-api.appspot.com"
```

### 3.3 Configure Signing
1. Select InventoryScannerPro target
2. Go to "Signing & Capabilities"
3. Select your development team
4. Choose automatic signing

### 3.4 Build and Run
1. Connect your iOS device (iOS 16+ required)
2. Select device as target
3. Press Cmd+R or click Play button

### 3.5 Login and Test
1. Login with same credentials
2. Configure session (Mode, Category, BOM if applicable)
3. Start scanning!

## Step 4: Testing the Complete Workflow

### 4.1 Upload Test Data

**Article Database Excel** (example):
| SAP Article | Part Number | Description | Category |
|-------------|-------------|-------------|----------|
| 87654321 | PN-12345 | Security Camera | CCTV |
| 87654322 | PN-12346 | DVR System | CCTV |
| 87654323 | PN-12347 | Network Cable | CX |

**BOM Excel** (example):
| SAP Article | Part Number | Description | Quantity |
|-------------|-------------|-------------|----------|
| 87654321 | PN-12345 | Security Camera | 10 |
| 87654322 | PN-12346 | DVR System | 2 |

### 4.2 Start a BOM Verification Session

On iOS App:
1. Select "BOM" mode
2. Choose "CCTV" category
3. Select the uploaded BOM
4. Tap "Start Session"

### 4.3 Scan Items

Option 1 - Camera Scan:
1. Tap "Scan Label"
2. Point camera at label with "Article # 87654321"
3. App automatically detects and submits

Option 2 - Manual Entry:
1. Tap "Manual Entry"
2. Enter article number
3. Set quantity
4. Tap "Submit"

### 4.4 View Real-time Updates

On Web Panel:
1. Go to "Real-time Feed" tab
2. Watch scans appear instantly
3. See MATCH/OVER/UNDER status in real-time

### 4.5 Review Session

On Web Panel:
1. Go to "Sessions" tab
2. Select your session
3. View summary with:
   - Match count
   - Over count
   - Under count
   - Item-by-item comparison

## Step 5: Production Deployment

### 5.1 Deploy Backend to Google App Engine

Create `backend/app.yaml`:
```yaml
runtime: python39
entrypoint: uvicorn app.main:app --host 0.0.0.0 --port $PORT

env_variables:
  SECRET_KEY: "production-secret-key-very-secure"
  DATABASE_URL: "postgresql://user:pass@host/db"  # Optional: upgrade to PostgreSQL

automatic_scaling:
  target_cpu_utilization: 0.65
  min_instances: 1
  max_instances: 10
```

Deploy:
```bash
cd backend
gcloud app deploy
```

### 5.2 Deploy Web Panel to Google App Engine

Create `web-panel/app.yaml`:
```yaml
runtime: nodejs20
env: standard

handlers:
  - url: /.*
    script: auto
    secure: always

env_variables:
  NEXT_PUBLIC_API_URL: "https://your-backend-url.appspot.com"
```

Build and deploy:
```bash
cd web-panel
npm run build
gcloud app deploy
```

### 5.3 Update iOS App for Production

Edit `APIService.swift`:
```swift
private let baseURL = "https://your-backend-url.appspot.com"
```

Build and archive:
1. Product → Archive
2. Distribute App
3. Upload to App Store Connect
4. Submit for TestFlight or App Store

## Excel File Formats

### Article Database Format
```
SAP Article | Part Number | Description      | Category
87654321    | PN-12345    | Security Camera  | CCTV
87654322    | PN-12346    | DVR System       | CCTV
87654323    | PN-12347    | Network Cable    | CX
87654324    | PN-12348    | Fire Alarm       | FIRE & BURG ALARM
```

### BOM Format
```
SAP Article | Part Number | Description      | Quantity
87654321    | PN-12345    | Security Camera  | 10
87654322    | PN-12346    | DVR System       | 2
87654323    | PN-12347    | Network Cable    | 50
```

## Label Format Example

The iOS app expects labels in this format:
```
PO # 12345678
Article # 87654321
```

## Troubleshooting

### Backend Issues
- **Port already in use**: Change port with `--port 8001`
- **Database errors**: Delete `inventory_scanner.db` and restart
- **Import errors**: Ensure virtual environment is activated

### Web Panel Issues
- **Can't connect to API**: Check NEXT_PUBLIC_API_URL in `.env.local`
- **CORS errors**: Backend allows all origins in development
- **SSE not working**: Check firewall settings

### iOS App Issues
- **Scanner not available**: Requires iOS 16+ and compatible device (A12 Bionic+)
- **Network errors**: Verify backend URL, check device and Mac are on same network
- **Authentication fails**: Ensure backend is running and credentials are correct

## Security Notes

### For Production:
1. **Change SECRET_KEY** in backend to a secure random string
2. **Configure CORS** to only allow your domain
3. **Use HTTPS** for all connections
4. **Enable authentication** on web panel routes
5. **Use PostgreSQL** instead of SQLite for production database
6. **Set up proper firewall** rules

## Support

For issues or questions:
1. Check the README in each component directory
2. Review API documentation at `/docs`
3. Check logs in backend terminal
4. Use browser developer tools for web panel debugging
5. Use Xcode console for iOS app debugging

## Next Steps

1. Customize the UI with your branding
2. Add more categories if needed
3. Configure email notifications
4. Set up automated backups
5. Create user roles and permissions
6. Add reporting features
7. Integrate with your ERP system

Enjoy your new Inventory Scanner Pro system! 🚀
