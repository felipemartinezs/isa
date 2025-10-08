# Quick Start Guide

Get the Inventory Scanner Pro system running in 5 minutes!

## 1. Start Backend (Terminal 1)

```bash
# Navigate to project first!
cd inventory-scanner-pro/backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend running at http://localhost:8000

## 2. Start Web Panel (Terminal 2)

```bash
# Navigate to project first!
cd inventory-scanner-pro/web-panel
npm install
cp .env.example .env.local
npm run dev
```

✅ Web Panel running at http://localhost:3000

## 3. Create Account

1. Open http://localhost:3000
2. Click "Sign up"
3. Create account: username, email, password
4. Login

## 4. Upload Data

**Article Database Tab:**
- Click "Choose File"
- Upload Excel with: SAP Article, Part Number, Description, Category
- Click "Upload"

**BOM Management Tab:**
- Select category (CCTV, CX, or FIRE & BURG ALARM)
- Enter BOM name
- Upload Excel with: SAP Article, Part Number, Description, Quantity
- Click "Upload"

## 5. Setup iOS App

```bash
cd ios-app
open InventoryScannerPro.xcodeproj
```

In Xcode:
1. Edit `Services/APIService.swift`
2. Change baseURL to your Mac's IP:
   ```swift
   private let baseURL = "http://192.168.1.XXX:8000"
   ```
3. Connect iPhone (iOS 16+)
4. Select device as target
5. Press Cmd+R to build and run

## 6. Start Scanning!

On iPhone:
1. Login with same credentials
2. Select Mode: **BOM** or **INVENTORY**
3. Select Category: **CCTV**, **CX**, or **FIRE & BURG ALARM**
4. If BOM mode: Select which BOM to verify
5. Tap **Start Session**
6. Tap **Scan Label** or **Manual Entry**
7. Watch real-time updates on web panel!

## Test Label Format

```
PO # 12345678
Article # 87654321
```

## Default Ports

- Backend API: 8000
- Web Panel: 3000

## Need Help?

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.

## Production Deployment

```bash
# Deploy Backend
cd backend
gcloud app deploy

# Deploy Web Panel
cd web-panel
npm run build
gcloud app deploy
```

Update iOS app with production URL and deploy via App Store Connect.

---

**That's it! You're ready to scan! 📱📦**
