import SwiftUI
import VisionKit

struct DataScannerView: UIViewControllerRepresentable {
    @EnvironmentObject var scannerManager: ScannerManager
    @Environment(\.dismiss) var dismiss
    
    func makeUIViewController(context: Context) -> DataScannerViewController {
        let scanner = DataScannerViewController(
            recognizedDataTypes: [.text()],
            qualityLevel: .balanced,
            recognizesMultipleItems: true,
            isHighFrameRateTrackingEnabled: false,
            isHighlightingEnabled: true
        )
        
        scanner.delegate = context.coordinator
        return scanner
    }
    
    func updateUIViewController(_ uiViewController: DataScannerViewController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, DataScannerViewControllerDelegate {
        var parent: DataScannerView
        var detectedArticle: String?
        var detectedPO: String?
        var lastProcessedTime: Date?
        
        init(_ parent: DataScannerView) {
            self.parent = parent
        }
        
        func dataScanner(_ dataScanner: DataScannerViewController, didTapOn item: RecognizedItem) {
            switch item {
            case .text(let text):
                processScannedText(text.transcript)
            default:
                break
            }
        }
        
        func dataScanner(_ dataScanner: DataScannerViewController, didAdd addedItems: [RecognizedItem], allItems: [RecognizedItem]) {
            // Auto-process recognized text
            for item in addedItems {
                switch item {
                case .text(let text):
                    processScannedText(text.transcript)
                default:
                    break
                }
            }
        }
        
        private func processScannedText(_ text: String) {
            // Throttle processing to avoid rapid-fire scans
            if let last = lastProcessedTime, Date().timeIntervalSince(last) < 2.0 {
                return
            }
            
            // Extract article number
            if let article = parent.scannerManager.extractArticleNumber(from: text) {
                detectedArticle = article
                
                // Also try to find PO number
                let po = parent.scannerManager.extractPONumber(from: text)
                detectedPO = po
                
                // Dismiss and show confirmation
                lastProcessedTime = Date()
                
                DispatchQueue.main.async {
                    self.parent.dismiss()
                    // Submit the scan
                    Task {
                        await self.parent.scannerManager.submitScan(
                            articleNumber: article,
                            poNumber: po,
                            quantity: 1.0,
                            isManual: false
                        )
                    }
                }
            }
        }
    }
    
    static func dismantleUIViewController(_ uiViewController: DataScannerViewController, coordinator: Coordinator) {
        if uiViewController.isScanning {
            uiViewController.stopScanning()
        }
    }
}

// MARK: - Scanner Container View (with overlay UI)
struct ScannerContainerView: View {
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        ZStack {
            DataScannerView()
                .ignoresSafeArea()
            
            VStack {
                // Top Bar
                HStack {
                    Button(action: { dismiss() }) {
                        Image(systemName: "xmark")
                            .font(.title2)
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.black.opacity(0.5))
                            .clipShape(Circle())
                    }
                    .padding()
                    
                    Spacer()
                }
                
                Spacer()
                
                // Instructions
                VStack(spacing: 12) {
                    Text("Scan Article Label")
                        .font(.headline)
                        .foregroundColor(.white)
                    
                    Text("Point camera at label with 'Article #' text")
                        .font(.subheadline)
                        .foregroundColor(.white.opacity(0.8))
                        .multilineTextAlignment(.center)
                }
                .padding()
                .background(Color.black.opacity(0.7))
                .cornerRadius(12)
                .padding()
            }
        }
    }
}
