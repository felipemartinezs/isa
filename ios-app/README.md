# Inventory Scanner Pro - iOS App

Native iOS app using SwiftUI and VisionKit for real-time text scanning and inventory management.

## Features

- **VisionKit Scanner**: Uses DataScannerViewController (iOS 16+) for real-time text recognition
- **Dual Modes**: Inventory mode and BOM verification mode
- **Category Management**: CCTV, CX, FIRE & BURG ALARM
- **Smart Text Extraction**: Automatically extracts Article # and PO # from scanned labels
- **Manual Entry**: Fallback option to manually enter article numbers
- **Real-time Sync**: Scans are immediately sent to backend and appear in web panel
- **Visual Feedback**: Color-coded status indicators (Green=Match, Orange=Difference)
- **Session Management**: Track and review scan sessions
- **History**: View past scanning sessions and records

## Requirements

- **iOS 16.0+**
- **Xcode 15.0+**
- **iPhone or iPad with VisionKit support**
- Camera permissions

## Setup

1. **Open in Xcode**:
```bash
cd ios-app
open InventoryScannerPro.xcodeproj
```

2. **Configure Backend URL**:
Edit `Services/APIService.swift` and update the `baseURL`:
```swift
private let baseURL = "http://your-backend-url.com"
```

For local testing:
```swift
private let baseURL = "http://localhost:8000"
```

For production:
```swift
private let baseURL = "https://your-api.appspot.com"
```

3. **Build and Run**:
- Select your target device
- Press Cmd+R to build and run

## Project Structure

```
InventoryScannerPro/
├── InventoryScannerProApp.swift    # App entry point
├── Models/
│   └── Models.swift                # Data models matching API
├── Services/
│   └── APIService.swift            # Network layer
├── Managers/
│   ├── AuthManager.swift           # Authentication state
│   └── ScannerManager.swift        # Scanner logic & session management
└── Views/
    ├── ContentView.swift           # Main routing
    ├── LoginView.swift             # Authentication
    ├── ScannerView.swift           # Main scanner interface
    ├── DataScannerView.swift       # VisionKit integration
    ├── ManualEntryView.swift       # Manual article entry
    ├── HistoryView.swift           # Session history
    └── SettingsView.swift          # User settings
```

## How It Works

### 1. Authentication
- User logs in with credentials
- JWT token is stored and used for API requests

### 2. Session Setup
- Select mode (Inventory or BOM)
- Choose category (CCTV, CX, FIRE & BURG ALARM)
- If BOM mode, select which BOM to verify against
- Start session

### 3. Scanning
- **Camera Scan**: Point camera at label, app automatically detects "Article # 12345678"
- **Manual Entry**: Type article number and quantity manually
- App extracts article and PO numbers using regex patterns
- Scan is immediately sent to backend

### 4. Real-time Feedback
- App receives scan result from API
- Displays status (MATCH, OVER, UNDER)
- Shows expected vs actual quantities
- Updates web panel in real-time via SSE

### 5. Session Completion
- End session when done
- View session history
- Review all scanned items

## Text Recognition Patterns

The app recognizes these patterns:
- `Article # 87654321`
- `Articulo # 87654321`
- `PO # 12345678`
- `P.O. # 12345678`

## VisionKit Notes

- **Requires iOS 16+**: DataScannerViewController is only available on iOS 16 and later
- **Device Support**: Not all devices support live text scanning (requires A12 Bionic or later)
- **Lighting**: Works best in well-lit conditions
- **Distance**: Hold camera 6-12 inches from label for best results

## Deployment

### TestFlight
1. Archive the app in Xcode
2. Upload to App Store Connect
3. Distribute via TestFlight

### App Store
1. Configure app in App Store Connect
2. Submit for review
3. Publish to App Store

## Permissions

The app requires camera permission to scan labels. This is declared in `Info.plist`:
```xml
<key>NSCameraUsageDescription</key>
<string>Camera access is required to scan article labels</string>
```

## Troubleshooting

### Scanner Not Available
- Check device compatibility (iOS 16+, A12 Bionic+)
- Use manual entry as fallback

### Network Errors
- Verify backend URL is correct
- Check network connectivity
- Ensure backend is running

### Authentication Issues
- Clear app data and re-login
- Check token expiration settings in backend

## Future Enhancements

- Offline mode with local caching
- Batch scanning
- Export session reports
- Barcode scanning support
- Multi-language support
