# 🚀 ISA Scanner - Quick Start

## ✅ Lo que ya está listo

### Backend (FastAPI)
- ✅ API REST completo
- ✅ Autenticación (admin/admin123)
- ✅ Upload de Articles Database (113 items)
- ✅ Upload de BOMs (51 items CCTV visibles)
- ✅ Server-Sent Events (SSE) para tiempo real
- ✅ Sesiones de escaneo
- ✅ Filtrado automático de filas ocultas en Excel

### Web Panel (Next.js)
- ✅ Dashboard con stats en tiempo real
- ✅ Article Database management
- ✅ BOM Management con preview
- ✅ Real-time Feed (SSE)
- ✅ Sessions tracking
- ✅ Renombrado a "ISA"

### iOS App (Swift + Live Text) - NUEVO
- ✅ 6 archivos Swift listos para usar
- ✅ Live Text de Apple (VisionKit)
- ✅ Autenticación
- ✅ Selección de categoría (CCTV, CX, FIRE)
- ✅ Selección de modo (INVENTORY vs BOM)
- ✅ Scanner en tiempo real
- ✅ Entrada manual alternativa
- ✅ Conexión al backend vía HTTP

---

## 📱 Próximos Pasos (5 minutos)

### 1. Crear Proyecto en Xcode
```bash
# Ya están los archivos en:
cd ~/Desktop/isa/inventory-scanner-pro/ios-app/

# Lee SETUP.md para instrucciones detalladas
```

### 2. Seguir SETUP.md
1. Abre Xcode
2. Crea nuevo proyecto iOS App
3. Arrastra los 6 archivos .swift al proyecto
4. Configura permisos de cámara
5. Build & Run

### 3. Probar el Flujo Completo

**Terminal 1 - Backend:**
```bash
cd ~/Desktop/isa/inventory-scanner-pro/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Web Panel:**
```bash
cd ~/Desktop/isa/inventory-scanner-pro/web-panel
npm run dev
```

**iPhone/Simulador:**
1. Abre ISAScanner
2. Login: `admin` / `admin123`
3. Selecciona CCTV
4. Selecciona INVENTORY o BOM
5. Start Scanning
6. Apunta a un código de barras o número

**Navegador (http://localhost:3000):**
1. Login con admin/admin123
2. Ve a "Real-time Feed"
3. **Verás los scans aparecer en tiempo real** ✨

---

## 🎯 Arquitectura Final

```
┌─────────────────┐
│   iPhone App    │  Swift + Live Text (VisionKit)
│  (ISAScanner)   │  Escanea códigos en tiempo real
└────────┬────────┘
         │ HTTP POST /scan
         ↓
┌─────────────────┐
│  Backend API    │  FastAPI (Python)
│ localhost:8000  │  Procesa scans, gestiona sesiones
└────────┬────────┘
         │ SSE (Server-Sent Events)
         ↓
┌─────────────────┐
│   Web Panel     │  Next.js + React
│ localhost:3000  │  Dashboard en tiempo real
└─────────────────┘
```

---

## 🔧 Configuración para iPhone Físico

Si pruebas en un iPhone real (no simulador):

1. **Obtén la IP de tu Mac:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

2. **En APIService.swift cambia:**
```swift
private let baseURL = "http://192.168.1.XXX:8000"  // Tu IP
```

3. **Asegúrate que el iPhone esté en la misma red WiFi**

---

## 🎨 Características de la App

### Live Text de Apple
- ✅ Reconocimiento de texto nativo (súper rápido)
- ✅ Detecta números de 9-10 dígitos (SAP Articles)
- ✅ Funciona offline para reconocimiento
- ✅ Optimizado por hardware Apple

### UI/UX
- ✅ Diseño moderno con SwiftUI
- ✅ Región de escaneo visual (rectángulo verde)
- ✅ Feedback visual inmediato
- ✅ Pausa/Resume para verificar
- ✅ Entrada manual como backup
- ✅ Contador de items escaneados

### Sincronización
- ✅ Cada scan se envía instantáneamente al backend
- ✅ El panel web se actualiza en tiempo real (SSE)
- ✅ Múltiples usuarios pueden ver el mismo feed
- ✅ Historial de sesiones

---

## 📊 Casos de Uso

### Modo INVENTORY
1. Selecciona categoría (CCTV, CX, o FIRE)
2. Modo INVENTORY
3. Escanea artículos libremente
4. El sistema registra todo sin validación contra BOM

### Modo BOM
1. Selecciona categoría (CCTV)
2. Modo BOM
3. **Selecciona un BOM de la lista** (ej: "WM1587 MODESTO, CA CCTV - 51 items")
4. Escanea artículos
5. El sistema **valida contra el BOM**:
   - ✅ Item esperado
   - ⚠️ Cantidad incorrecta
   - ❌ Item no esperado

---

## 🐛 Troubleshooting

### "No items found for category CCTV"
- Asegúrate de haber subido un BOM para esa categoría en el web panel

### "Network error"
- Verifica que el backend esté corriendo (puerto 8000)
- Si usas iPhone físico, verifica la IP en APIService.swift

### "Camera permission denied"
- Ve a Settings → ISAScanner → Camera → Enable

### Live Text no detecta nada
- Asegúrate que el número esté dentro del rectángulo verde
- La cámara debe estar enfocada (espera un segundo)
- Los números deben ser de 9-10 dígitos
- Intenta con mejor iluminación

---

## 🎉 ¡Listo!

Ya tienes un **sistema completo de escaneo de inventario** con:
- 📱 App iOS nativa con Live Text de Apple
- 🖥️ Panel web en tiempo real
- ⚡ Backend robusto
- 🔄 Sincronización instantánea

**Siguiente paso:** Abre Xcode y sigue `SETUP.md` para crear el proyecto.

¿Dudas? Todos los archivos están documentados y listos para usar.
