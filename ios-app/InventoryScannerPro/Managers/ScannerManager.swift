import Foundation
import VisionKit

@MainActor
class ScannerManager: NSObject, ObservableObject {
    @Published var scannedItems: [ScannedItem] = []
    @Published var isScanning = false
    @Published var errorMessage: String?
    @Published var lastScanResult: ScanRecord?
    
    // Current session
    @Published var currentSession: ScanSession?
    @Published var selectedMode: ScanMode = .inventory
    @Published var selectedCategory: Category = .cctv
    @Published var selectedBOM: BOM?
    @Published var availableBOMs: [BOM] = []
    
    private var dataScanner: DataScannerViewController?
    
    var isDataScannerAvailable: Bool {
        DataScannerViewController.isSupported && DataScannerViewController.isAvailable
    }
    
    // MARK: - Session Management
    func loadBOMs() async {
        do {
            availableBOMs = try await APIService.shared.getBOMs(category: selectedCategory)
        } catch {
            errorMessage = "Failed to load BOMs: \(error.localizedDescription)"
        }
    }
    
    func startSession() async {
        do {
            let bomId = (selectedMode == .bom) ? selectedBOM?.id : nil
            currentSession = try await APIService.shared.createSession(
                mode: selectedMode,
                category: selectedCategory,
                bomId: bomId
            )
            errorMessage = nil
        } catch {
            errorMessage = "Failed to start session: \(error.localizedDescription)"
        }
    }
    
    func endSession() async {
        guard let session = currentSession else { return }
        
        do {
            try await APIService.shared.endSession(id: session.id)
            currentSession = nil
            scannedItems.removeAll()
        } catch {
            errorMessage = "Failed to end session: \(error.localizedDescription)"
        }
    }
    
    // MARK: - Scanning
    func submitScan(articleNumber: String, poNumber: String?, quantity: Double, isManual: Bool) async {
        guard let session = currentSession else {
            errorMessage = "No active session"
            return
        }
        
        do {
            let record = try await APIService.shared.createScanRecord(
                sessionId: session.id,
                sapArticle: articleNumber,
                poNumber: poNumber,
                quantity: quantity,
                manualEntry: isManual
            )
            
            lastScanResult = record
            
            // Add to local list
            let item = ScannedItem(
                articleNumber: articleNumber,
                poNumber: poNumber,
                timestamp: Date()
            )
            scannedItems.insert(item, at: 0)
            
            errorMessage = nil
        } catch {
            errorMessage = "Failed to submit scan: \(error.localizedDescription)"
        }
    }
    
    // MARK: - Text Extraction
    func extractArticleNumber(from text: String) -> String? {
        // Pattern: "Article # 87654321" or "Articulo # 87654321"
        let patterns = [
            "(?i)article\\s*#\\s*(\\d+)",
            "(?i)articulo\\s*#\\s*(\\d+)",
            "(?i)art\\.?\\s*#\\s*(\\d+)"
        ]
        
        for pattern in patterns {
            if let regex = try? NSRegularExpression(pattern: pattern, options: []),
               let match = regex.firstMatch(in: text, options: [], range: NSRange(text.startIndex..., in: text)),
               let range = Range(match.range(at: 1), in: text) {
                return String(text[range])
            }
        }
        
        return nil
    }
    
    func extractPONumber(from text: String) -> String? {
        // Pattern: "PO # 12345678"
        let patterns = [
            "(?i)po\\s*#\\s*(\\d+)",
            "(?i)p\\.?o\\.?\\s*#\\s*(\\d+)"
        ]
        
        for pattern in patterns {
            if let regex = try? NSRegularExpression(pattern: pattern, options: []),
               let match = regex.firstMatch(in: text, options: [], range: NSRange(text.startIndex..., in: text)),
               let range = Range(match.range(at: 1), in: text) {
                return String(text[range])
            }
        }
        
        return nil
    }
}
