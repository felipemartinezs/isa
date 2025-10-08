import SwiftUI
import VisionKit
import AVFoundation
import Vision

struct ScannerView: View {
    @EnvironmentObject var apiService: APIService
    let session: ScanSession
    let onEnd: () -> Void
    
    @State private var isScanning = false  // Pausado por defecto
    @State private var detectedText: String = ""
    @State private var capturedArticles: [(article: String, quantity: String, sent: Bool, status: String?, description: String?, partNumber: String?, detectedCategory: String?, expectedQuantity: Double?, recordId: Int?)] = []
    @State private var scannedItems: [ScanRecord] = []
    @State private var showManualEntry = false
    @State private var showConfirmMultipleScan = false  // Para confirmar múltiples scans
    @State private var manualSAP = ""
    @State private var manualPO = ""
    @State private var errorMessage: String?
    @State private var successMessage: String?
    @State private var detectedCount: Int = 0  // Cantidad de números detectados
    
    var body: some View {
        NavigationView {
            ZStack {
                // Live Text Scanner
                LiveTextScannerView(
                    recognizedText: $detectedText,
                    onTextDetected: handleTextDetected
                )
                .ignoresSafeArea()
                .opacity(isScanning ? 1.0 : 0.5)
                
                // Scan Region Overlay
                VStack {
                    Spacer()
                    
                    Rectangle()
                        .fill(Color.clear)
                        .frame(height: 150)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(isScanning ? Color.green : Color.gray, lineWidth: 3)
                        )
                        .padding(.horizontal, 40)
                    
                    Spacer()
                }
                
                // Camera Status Overlay
                if !isScanning {
                    VStack {
                        Spacer()
                        Text("Camera Paused")
                            .font(.headline)
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.black.opacity(0.7))
                            .cornerRadius(8)
                        Spacer()
                        Spacer()
                        Spacer()
                    }
                }
                
                // Bottom Info Panel
                VStack {
                    Spacer()
                    
                    VStack(spacing: 16) {
                        // Session Info
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(session.category?.displayName ?? "INVENTORY")
                                    .font(.headline)
                                Text("\(session.mode.displayName) Mode")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            Spacer()
                            Text("\(scannedItems.count) scanned")
                                .font(.headline)
                                .foregroundColor(.blue)
                        }
                        
                        // Last detected text
                        if detectedCount > 0 {
                            HStack {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.green)
                                Text("\(detectedCount) article\(detectedCount > 1 ? "s" : "") detected")
                                    .font(.subheadline)
                                    .fontWeight(.semibold)
                            }
                            .padding(8)
                            .background(Color.green.opacity(0.1))
                            .cornerRadius(8)
                        } else if isScanning {
                            VStack(spacing: 4) {
                                Text("Scanning...")
                                    .font(.caption)
                                    .foregroundColor(.orange)
                                if !detectedText.isEmpty {
                                    Text("OCR: \(detectedText.prefix(50))...")
                                        .font(.system(size: 8))
                                        .foregroundColor(.secondary)
                                        .lineLimit(1)
                                }
                            }
                        }
                        
                        // Messages
                        if let error = errorMessage {
                            Text(error)
                                .font(.caption)
                                .foregroundColor(.red)
                                .multilineTextAlignment(.center)
                        }
                        
                        if let success = successMessage {
                            Text(success)
                                .font(.caption)
                                .foregroundColor(.green)
                                .multilineTextAlignment(.center)
                        }
                        
                        // Action Buttons
                        VStack(spacing: 12) {
                            // Botón principal de captura
                            Button(action: captureAndConfirm) {
                                HStack {
                                    Image(systemName: detectedCount > 1 ? "square.stack.3d.up.fill" : "camera.viewfinder")
                                        .font(.title2)
                                    if detectedCount > 0 {
                                        Text("Capture \(detectedCount) Article\(detectedCount > 1 ? "s" : "")")
                                            .font(.headline)
                                    } else {
                                        Text("Capture Scan")
                                            .font(.headline)
                                    }
                                }
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(detectedCount > 0 ? Color.green : Color.blue)
                                .foregroundColor(.white)
                                .cornerRadius(12)
                            }
                            .disabled(detectedCount == 0)
                            
                            HStack(spacing: 16) {
                                Button(action: { showManualEntry = true }) {
                                    Label("Manual", systemImage: "keyboard")
                                        .font(.caption)
                                }
                                .buttonStyle(.bordered)
                                
                                Button(action: toggleScanning) {
                                    Label(isScanning ? "Stop Camera" : "Start Camera", systemImage: isScanning ? "pause.circle.fill" : "play.circle.fill")
                                        .font(.caption)
                                }
                                .buttonStyle(.bordered)
                                
                                Button(action: endSession) {
                                    Label("End", systemImage: "stop.circle.fill")
                                        .font(.caption)
                                }
                                .buttonStyle(.borderedProminent)
                                .tint(.red)
                            }
                        }
                    }
                    .padding()
                    .background(.ultraThinMaterial)
                    .cornerRadius(16)
                    .padding()
                }
            }
            .navigationTitle("Scanning")
            .navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented: $showManualEntry) {
                ManualEntryView(
                    sapArticle: $manualSAP,
                    poNumber: $manualPO,
                    onSubmit: handleManualEntry
                )
            }
            .sheet(isPresented: $showConfirmMultipleScan) {
                ConfirmMultipleScanView(
                    articles: $capturedArticles,
                    onSendIndividual: sendIndividualArticle,
                    onDeleteRecord: deleteScanRecord,  // ← Mover ANTES de onDone
                    onDone: confirmMultipleScan,
                    onCancel: { 
                        showConfirmMultipleScan = false
                        isScanning = true
                    }
                )
            }  
        }
    }
    
    private func toggleScanning() {
        isScanning.toggle()
    }
    
    private func handleTextDetected(_ text: String) {
        guard isScanning else { return }
        
        detectedText = text
        
        // Detectar MÚLTIPLES números de 9-10 dígitos (más flexible)
        let sapPattern = #"\b[0-9]{9,10}\b"#
        var detectedArticles: [String] = []
        
        if let regex = try? NSRegularExpression(pattern: sapPattern) {
            let matches = regex.matches(in: text, range: NSRange(text.startIndex..., in: text))
            
            for match in matches.prefix(5) {  // Límite de 5 artículos por captura
                if let range = Range(match.range, in: text) {
                    let article = String(text[range])
                    // Solo artículos únicos y de exactamente 10 dígitos preferidos
                    if !detectedArticles.contains(article) {
                        detectedArticles.append(article)
                    }
                }
            }
        }
        
        // Actualizar el contador solo si cambió
        DispatchQueue.main.async {
            self.detectedCount = detectedArticles.count
        }
    }
    
    private func captureAndConfirm() {
        guard !detectedText.isEmpty else {
            errorMessage = "No text detected. Start camera and point at list."
            return
        }
        
        // Extraer TODOS los números de 9-10 dígitos
        let sapPattern = #"\b[0-9]{9,10}\b"#
        var articles: [String] = []
        
        if let regex = try? NSRegularExpression(pattern: sapPattern) {
            let matches = regex.matches(in: detectedText, range: NSRange(detectedText.startIndex..., in: detectedText))
            
            for match in matches.prefix(5) {  // Max 5 artículos
                if let range = Range(match.range, in: detectedText) {
                    let article = String(detectedText[range])
                    if !articles.contains(article) && article.count == 10 {  // Preferir 10 dígitos
                        articles.append(article)
                    }
                }
            }
            
            // Si no hay de 10, aceptar de 9
            if articles.isEmpty {
                for match in matches.prefix(5) {
                    if let range = Range(match.range, in: detectedText) {
                        let article = String(detectedText[range])
                        if !articles.contains(article) {
                            articles.append(article)
                        }
                    }
                }
            }
        }
        
        guard !articles.isEmpty else {
            errorMessage = "No valid SAP article numbers detected (9-10 digits)"
            return
        }
        
        // Convertir a tuplas con cantidad inicial = "1" y sin enviar
        capturedArticles = articles.map { (article: $0, quantity: "1", sent: false, status: nil, description: nil, partNumber: nil, detectedCategory: nil, expectedQuantity: nil, recordId: nil) }
        showConfirmMultipleScan = true
        isScanning = false  // Pausa cámara mientras confirma
    }
    
    private func sendIndividualArticle(at index: Int) {
        guard index < capturedArticles.count else { return }
        let item = capturedArticles[index]
        
        guard !item.sent, let quantity = Double(item.quantity), quantity > 0 else { return }
        
        Task {
            do {
                print("📦 Sending individual: \(item.article) x\(quantity)")
                
                let record = try await apiService.sendScan(
                    sessionId: session.id,
                    sapArticle: item.article,
                    poNumber: nil,
                    quantity: quantity
                )
                
                scannedItems.append(record)
                
                // Actualizar el estado del artículo
                capturedArticles[index].sent = true
                capturedArticles[index].status = record.status
                capturedArticles[index].description = record.description
                capturedArticles[index].partNumber = record.partNumber
                capturedArticles[index].detectedCategory = record.detectedCategory  // ← AGREGAR
                capturedArticles[index].expectedQuantity = record.expectedQuantity
                capturedArticles[index].recordId = record.id
                
                print("✅ Success: \(record.sapArticle) - Status: \(record.status)")
                
            } catch {
                errorMessage = "Failed: \(error.localizedDescription)"
                print("❌ Error: \(error)")
            }
        }
    }
    private func deleteScanRecord(at index: Int) {
        guard index < capturedArticles.count else { return }
        let item = capturedArticles[index]
        
        guard let recordId = item.recordId else {
            errorMessage = "Cannot delete: No record ID"
            return
        }
        
        Task {
            do {
                try await apiService.deleteScanRecord(id: recordId)
                
                // Remover de la lista
                capturedArticles.remove(at: index)
                
                // También remover de scannedItems
                if let idx = scannedItems.firstIndex(where: { $0.id == recordId }) {
                    scannedItems.remove(at: idx)
                }
                
                print("🗑️ Record \(recordId) deleted successfully")
                
            } catch {
                errorMessage = "Delete failed: \(error.localizedDescription)"
                print("❌ Delete error: \(error)")
            }
        }
    }
    private func confirmMultipleScan() {
        // Cerrar el diálogo (todos los artículos ya fueron enviados individualmente)
        showConfirmMultipleScan = false
        capturedArticles = []
        detectedCount = 0
    }
    
    private func handleManualEntry() {
        guard !manualSAP.isEmpty else { return }
        
        sendScan(sapArticle: manualSAP, poNumber: manualPO.isEmpty ? nil : manualPO)
        manualSAP = ""
        manualPO = ""
        showManualEntry = false
    }
    
    private func sendScan(sapArticle: String, poNumber: String?, quantity: Double = 1.0) {
        Task {
            do {
                let record = try await apiService.sendScan(
                    sessionId: session.id,
                    sapArticle: sapArticle,
                    poNumber: poNumber,
                    quantity: quantity
                )
                
                scannedItems.append(record)
                successMessage = "✓ \(sapArticle) x\(quantity) scanned"
                errorMessage = nil
                
                // Clear success message after 2 seconds
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                    successMessage = nil
                }
                
            } catch {
                errorMessage = "Failed: \(error.localizedDescription)"
                successMessage = nil
            }
        }
    }
    
    private func endSession() {
        // Solo cierra la vista, mantiene la sesión activa para reanudar después
        print("⏸️ Pausing session #\(session.id) - session remains active")
        onEnd()
    }
}

// MARK: - Live Text Scanner (Using VisionKit)
struct LiveTextScannerView: UIViewControllerRepresentable {
    @Binding var recognizedText: String
    let onTextDetected: (String) -> Void
    
    func makeUIViewController(context: Context) -> LiveTextViewController {
        let controller = LiveTextViewController()
        controller.delegate = context.coordinator
        return controller
    }
    
    func updateUIViewController(_ uiViewController: LiveTextViewController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, LiveTextDelegate {
        let parent: LiveTextScannerView
        
        init(_ parent: LiveTextScannerView) {
            self.parent = parent
        }
        
        func didRecognizeText(_ text: String) {
            DispatchQueue.main.async {
                self.parent.recognizedText = text
                self.parent.onTextDetected(text)
            }
        }
    }
}

// MARK: - Live Text View Controller
protocol LiveTextDelegate: AnyObject {
    func didRecognizeText(_ text: String)
}

class LiveTextViewController: UIViewController, AVCaptureVideoDataOutputSampleBufferDelegate {
    weak var delegate: LiveTextDelegate?
    
    private var captureSession: AVCaptureSession!
    private var previewLayer: AVCaptureVideoPreviewLayer!
    private let textRecognitionRequest = VNRecognizeTextRequest()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupCamera()
    }
    
    private func setupCamera() {
        captureSession = AVCaptureSession()
        captureSession.sessionPreset = .high
        
        guard let videoCaptureDevice = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let videoInput = try? AVCaptureDeviceInput(device: videoCaptureDevice),
              captureSession.canAddInput(videoInput) else {
            return
        }
        
        captureSession.addInput(videoInput)
        
        let videoOutput = AVCaptureVideoDataOutput()
        videoOutput.setSampleBufferDelegate(self, queue: DispatchQueue(label: "videoQueue"))
        
        if captureSession.canAddOutput(videoOutput) {
            captureSession.addOutput(videoOutput)
        }
        
        previewLayer = AVCaptureVideoPreviewLayer(session: captureSession)
        previewLayer.frame = view.bounds
        previewLayer.videoGravity = .resizeAspectFill
        view.layer.addSublayer(previewLayer)
        
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            self?.captureSession.startRunning()
        }
    }
    
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        
        let requestHandler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer, options: [:])
        
        do {
            try requestHandler.perform([textRecognitionRequest])
            
            if let results = textRecognitionRequest.results as? [VNRecognizedTextObservation] {
                let text = results.compactMap { observation in
                    observation.topCandidates(1).first?.string
                }.joined(separator: " ")
                
                if !text.isEmpty {
                    delegate?.didRecognizeText(text)
                }
            }
        } catch {
            print("Error performing text recognition: \(error)")
        }
    }
    
    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        previewLayer?.frame = view.bounds
    }
}

// MARK: - Confirm Multiple Scan View
struct ConfirmMultipleScanView: View {
    @Environment(\.dismiss) var dismiss
    @Binding var articles: [(article: String, quantity: String, sent: Bool, status: String?, description: String?, partNumber: String?, detectedCategory: String?, expectedQuantity: Double?, recordId: Int?)]
    let onSendIndividual: (Int) -> Void
    let onDeleteRecord: (Int) -> Void  // ← NUEVO
    let onDone: () -> Void
    let onCancel: () -> Void
    
    private var allSent: Bool {
        articles.allSatisfy { $0.sent }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Header
                VStack(spacing: 8) {
                    Image(systemName: "list.bullet.clipboard")
                        .font(.system(size: 50))
                        .foregroundColor(.blue)
                    Text("Send One by One")
                        .font(.title2)
                        .fontWeight(.bold)
                    Text("\(articles.filter { $0.sent }.count)/\(articles.count) sent")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding()
                
                Divider()
                
                // Lista de artículos
                ScrollView {
                    VStack(spacing: 12) {
                        ForEach(Array(articles.indices), id: \.self) { index in
                            ArticleRowView(
                                index: index,
                                item: $articles[index],
                                onSend: { onSendIndividual(index) },
                                onDelete: { articles.remove(at: index) },
                                onDeleteRecord: { onDeleteRecord(index) }  // ✅ Usar el callback recibido
                            )
                        }
                    }
                    .padding()
                }
                
                // Botón Done
                VStack(spacing: 12) {
                    if allSent {
                        Button(action: {
                            onDone()
                            dismiss()
                        }) {
                            HStack {
                                Image(systemName: "checkmark.circle.fill")
                                Text("Done")
                                    .fontWeight(.semibold)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.green)
                            .foregroundColor(.white)
                            .cornerRadius(12)
                        }
                    }
                    
                    Button(action: {
                        onCancel()
                        dismiss()
                    }) {
                        Text(allSent ? "Close" : "Cancel")
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color(.systemGray5))
                            .foregroundColor(.primary)
                            .cornerRadius(12)
                    }
                }
                .padding()
            }
            .navigationTitle("Review & Send")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

// MARK: - Article Row View (VERSIÓN MEJORADA CORREGIDA)
struct ArticleRowView: View {
    let index: Int
    @Binding var item: (article: String, quantity: String, sent: Bool, status: String?, description: String?, partNumber: String?, detectedCategory: String?, expectedQuantity: Double?, recordId: Int?)
    let onSend: () -> Void
    let onDelete: () -> Void
    let onDeleteRecord: () -> Void  // ← NUEVO: callback para delete record
    private var statusColor: Color {
        guard let status = item.status else { return .gray }
        switch status.uppercased() {
        case "MATCH": return .green
        case "OVER": return .orange
        case "UNDER": return .red
        default: return .gray
        }
    }
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            // Número de orden
            Text("\(index + 1)")
                .font(.title3)
                .fontWeight(.bold)
                .foregroundColor(.white)
                .frame(width: 40, height: 40)
                .background(item.sent ? Color.green : Color.blue)
                .clipShape(Circle())
            
            // Layout vertical mejorado
            VStack(alignment: .leading, spacing: 14) {
                // NÚMEROS ESCANEADOS ARRIBA (más prominentes)
                VStack(alignment: .leading, spacing: 6) {
                    // Número principal grande
                    HStack(spacing: 8) {
                        Text(item.article)
                            .font(.system(.title2, design: .monospaced))
                            .fontWeight(.bold)
                            .foregroundColor(.primary)
                        
                        // Badge de categoría detectada
                        if let category = item.detectedCategory {
                            Text(category)
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundColor(.white)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(
                                    Capsule()
                                        .fill(Color.purple)
                                )
                        }

                        // Badge de cantidad (solo cuando está enviado)
                        if item.sent, let quantity = Double(item.quantity) {
                            Text("QTY: \(Int(quantity))")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(.white)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(
                                    Capsule()
                                        .fill(Color.blue)
                                )
                        }
                    }
                    // Información adicional después de enviar
                    if item.sent {
                        if let partNumber = item.partNumber {
                            Text(partNumber)
                                .font(.system(.callout, design: .monospaced))
                                .foregroundColor(.secondary)
                        }
                        
                        if let description = item.description {
                            Text(description)
                                .font(.caption)
                                .foregroundColor(.secondary)
                                .lineLimit(2)
                                .padding(.top, 2)
                        }
                    }
                }
                
                                // BOTONES ABAJO - ESTILO MINIMALISTA MODERNO
                if !item.sent {
                    HStack(spacing: 10) {
                        // Botón eliminar - estilo minimalista
                        Button(action: onDelete) {
                            Image(systemName: "arrow.uturn.backward")
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(.secondary)
                                .frame(width: 38, height: 38)
                                .background(
                                    Circle()
                                        .fill(Color(.systemGray6))
                                )
                                .overlay(
                                    Circle()
                                        .strokeBorder(Color(.systemGray4), lineWidth: 1)
                                )
                        }
                        
                        // Botón disminuir - minimalista
                        Button(action: decreaseQuantity) {
                            Image(systemName: "minus")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(.red.opacity(0.85))
                                .frame(width: 38, height: 38)
                                .background(
                                    Circle()
                                        .fill(Color.red.opacity(0.08))
                                )
                                .overlay(
                                    Circle()
                                        .strokeBorder(Color.red.opacity(0.25), lineWidth: 1.5)
                                )
                        }
                        
                        // Campo cantidad
                        TextField("Qty", text: $item.quantity)
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.center)
                            .font(.system(.title3, design: .rounded))
                            .fontWeight(.semibold)
                            .frame(width: 52, height: 38)
                            .background(Color(.systemBackground))
                            .cornerRadius(10)
                            .overlay(
                                RoundedRectangle(cornerRadius: 10)
                                    .strokeBorder(Color(.systemGray4), lineWidth: 1.5)
                            )
                        
                        // Botón aumentar - minimalista
                        Button(action: increaseQuantity) {
                            Image(systemName: "plus")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(.green.opacity(0.85))
                                .frame(width: 38, height: 38)
                                .background(
                                    Circle()
                                        .fill(Color.green.opacity(0.08))
                                )
                                .overlay(
                                    Circle()
                                        .strokeBorder(Color.green.opacity(0.25), lineWidth: 1.5)
                                )
                        }
                        
                        Spacer()
                        
                        // Botón enviar - flecha azul
                        Button(action: onSend) {
                            Image(systemName: "arrow.up.circle.fill")
                                .font(.system(size: 22))
                                .foregroundColor(.blue)
                                .frame(width: 38, height: 38)
                        }
                    }
                } else {
                    // Estado enviado
                    HStack(spacing: 12) {
                        if let status = item.status {
                            HStack(spacing: 6) {
                                Image(systemName: status.uppercased() == "MATCH" ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                                    .font(.subheadline)
                                
                                // Mostrar status con cantidades
                                if let expected = item.expectedQuantity, let scanned = Double(item.quantity) {
                                    Text("\(status.uppercased()) \(Int(scanned)) of \(Int(expected))")
                                        .font(.subheadline)
                                        .fontWeight(.bold)
                                } else {
                                    Text(status.uppercased())
                                        .font(.subheadline)
                                        .fontWeight(.bold)
                                }
                            }
                            .foregroundColor(.white)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(
                                Capsule()
                                    .fill(statusColor)
                                    .shadow(color: statusColor.opacity(0.3), radius: 4, x: 0, y: 2)
                            )
                            
                            // ← NUEVO: Botón Delete solo para OVER/UNDER
                            if status.uppercased() == "OVER" || status.uppercased() == "UNDER" {
                                Button(action: onDeleteRecord) {
                                    Image(systemName: "trash.circle.fill")
                                        .font(.system(size: 20))
                                        .foregroundColor(.red.opacity(0.8))
                                }
                                .padding(.leading, 8)
                            }
                        }
                        
                        Spacer()
                        
                        Image(systemName: "checkmark.circle.fill")
                            .font(.system(size: 32))
                            .foregroundColor(.green)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(18)
        .background(
            RoundedRectangle(cornerRadius: 18)
                .fill(item.sent ? Color.green.opacity(0.08) : Color(.systemBackground))
                .shadow(color: .black.opacity(0.06), radius: 6, x: 0, y: 2)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .strokeBorder(
                    item.sent ? Color.green.opacity(0.4) : Color(.systemGray5),
                    lineWidth: 2
                )
        )
    }
    
    private func increaseQuantity() {
        if let current = Double(item.quantity) {
            item.quantity = String(format: "%.0f", current + 1)
        }
    }
    
    private func decreaseQuantity() {
        if let current = Double(item.quantity), current > 1 {
            item.quantity = String(format: "%.0f", current - 1)
        }
    }
}

// MARK: - Manual Entry View
struct ManualEntryView: View {
    @Environment(\.dismiss) var dismiss
    @Binding var sapArticle: String
    @Binding var poNumber: String
    let onSubmit: () -> Void
    
    var body: some View {
        NavigationView {
            Form {
                Section("Article Information") {
                    TextField("SAP Article *", text: $sapArticle)
                        .keyboardType(.numbersAndPunctuation)
                    
                    TextField("PO Number (optional)", text: $poNumber)
                        .keyboardType(.numbersAndPunctuation)
                }
            }
            .navigationTitle("Manual Entry")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Submit") {
                        onSubmit()
                        dismiss()
                    }
                    .disabled(sapArticle.isEmpty)
                }
            }
        }
    }
}

#Preview {
    ScannerView(
        session: ScanSession(
            id: 1,
            userId: 1,
            mode: .inventory,
            category: .cctv,
            bomId: nil,
            startedAt: "2024-01-01T00:00:00",
            endedAt: nil,
            isActive: true
        ),
        onEnd: {}
    )
    .environmentObject(APIService())
}
