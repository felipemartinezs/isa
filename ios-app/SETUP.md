# ISA Scanner - iOS App Setup

## Archivos Creados ✅

Todos los archivos Swift ya están listos:
- ✅ `ISAScannerApp.swift` - Entry point
- ✅ `Models.swift` - Data models
- ✅ `APIService.swift` - Backend communication
- ✅ `LoginView.swift` - Login screen
- ✅ `HomeView.swift` - Home screen (category/mode selection)
- ✅ `ScannerView.swift` - Live Text scanner (Apple VisionKit)

## Paso 1: Crear Proyecto en Xcode

1. **Abre Xcode**
2. **File → New → Project**
3. Selecciona **iOS → App**
4. Configuración:
   - **Product Name:** `ISAScanner`
   - **Team:** Tu cuenta de desarrollador
   - **Organization Identifier:** `com.tuempresa` (o tu dominio)
   - **Interface:** SwiftUI ✅
   - **Language:** Swift ✅
   - **Storage:** None
   - **Include Tests:** No (opcional)
5. **Guardar en:** `/Users/felipemartinez/Desktop/isa/inventory-scanner-pro/ios-app/`
6. **IMPORTANTE:** Nombra la carpeta del proyecto `ISAScanner` para que coincida con los archivos

## Paso 2: Configurar Permisos

En `Info.plist` o en **Target → Info → Custom iOS Target Properties**, agrega:

- **Privacy - Camera Usage Description:** "ISA necesita acceso a la cámara para escanear artículos"

## Paso 3: Reemplazar Archivos por Defecto

Xcode crea automáticamente algunos archivos. Debes reemplazarlos:

1. **Elimina** el archivo `ContentView.swift` que Xcode creó (no lo necesitas)
2. En Xcode, **arrastra todos los archivos `.swift`** de este directorio al proyecto:
   - `ISAScannerApp.swift` (reemplaza el que Xcode creó)
   - `Models.swift`
   - `APIService.swift`
   - `LoginView.swift`
   - `HomeView.swift`
   - `ScannerView.swift`
3. Cuando te pregunte:
   - ✅ **Copy items if needed**
   - ✅ **Create groups**
   - ✅ **Add to targets: ISAScanner**

## Paso 4: Configurar Backend URL

En `APIService.swift`, cambia la URL si tu backend no está en localhost:8000

```swift
private let baseURL = "http://localhost:8000"
```

Si pruebas en un iPhone físico, usa la IP de tu Mac:
```swift
private let baseURL = "http://192.168.1.X:8000"  // IP de tu Mac
```

## Paso 5: Build & Run

1. Selecciona tu iPhone o simulador
2. Cmd+R para ejecutar
3. Login: `admin` / `admin123`

## Arquitectura

```
ISAScanner/
├── ISAScannerApp.swift       # Entry point
├── Models/
│   ├── User.swift            # Usuario
│   ├── Category.swift        # CCTV, CX, FIRE
│   ├── ScanMode.swift        # INVENTORY vs BOM
│   └── ScanSession.swift     # Sesión de escaneo
├── Services/
│   ├── APIService.swift      # HTTP calls al backend
│   └── ScanService.swift     # Lógica de escaneo
└── Views/
    ├── LoginView.swift       # Pantalla de login
    ├── HomeView.swift        # Selección de categoría/modo
    ├── ScannerView.swift     # Live Text scanner
    └── SessionView.swift     # Estado de sesión actual
```

## Conectividad con Backend

La app se conecta a:
- **POST /auth/login** - Autenticación
- **POST /scan/sessions** - Crear sesión
- **POST /scan** - Enviar scan
- **GET /scan/sessions/{id}** - Estado de sesión

El **panel web** se actualiza automáticamente vía SSE.
