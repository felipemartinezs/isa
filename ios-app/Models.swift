import Foundation

// MARK: - Category
enum Category: String, Codable, CaseIterable {
    case cctv = "CCTV"
    case cx = "CX"
    case fireAlarm = "FIRE & BURG ALARM"
    
    var displayName: String { rawValue }
}

// MARK: - Scan Mode
enum ScanMode: String, Codable, CaseIterable {
    case inventory = "INVENTORY"
    case bom = "BOM"
    
    var displayName: String { rawValue }
}

// MARK: - User
struct User: Codable {
    let id: Int
    let username: String
    let email: String
    let isActive: Bool
    
    enum CodingKeys: String, CodingKey {
        case id, username, email
        case isActive = "is_active"
    }
}

// MARK: - Auth Response
struct AuthResponse: Codable {
    let accessToken: String
    let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
    }
}

// MARK: - Scan Session
struct ScanSession: Codable, Identifiable {
    let id: Int
    let userId: Int
    let mode: ScanMode
    let category: Category?
    let bomId: Int?
    let startedAt: String
    let endedAt: String?
    let isActive: Bool
    var bomName: String?  // ← AGREGAR ESTA LÍNEA
    var bomItemsCount: Int?         // ← AGREGAR
    var scannedItemsCount: Int?

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case mode, category
        case bomId = "bom_id"
        case startedAt = "started_at"
        case endedAt = "ended_at"
        case isActive = "is_active"
        case bomName = "bom_name"  // ← AGREGAR ESTA LÍNEA
        case bomItemsCount = "bom_items_count"        // ← AGREGAR
        case scannedItemsCount = "scanned_items_count"
    }
}

// MARK: - Scan Record
struct ScanRecord: Codable, Identifiable {
    let id: Int
    let sessionId: Int
    let sapArticle: String
    let partNumber: String?
    let description: String?
    let detectedCategory: String?  // ← AGREGAR LÍNEA 85
    let poNumber: String?
    let quantity: Double
    let scannedAt: String
    let manualEntry: Bool
    let expectedQuantity: Double?
    let status: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case sessionId = "session_id"
        case sapArticle = "sap_article"
        case partNumber = "part_number"
        case description
        case detectedCategory = "detected_category"  // ← AGREGAR LÍNEA 98
        case poNumber = "po_number"
        case quantity
        case scannedAt = "scanned_at"
        case manualEntry = "manual_entry"
        case expectedQuantity = "expected_quantity"
        case status
    }
}

// MARK: - Scan Request
struct ScanRequest: Codable {
    let sessionId: Int
    let sapArticle: String
    let poNumber: String?
    let quantity: Double
    let manualEntry: Bool
    
    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case sapArticle = "sap_article"
        case poNumber = "po_number"
        case quantity
        case manualEntry = "manual_entry"
    }
}

// MARK: - BOM
struct BOM: Codable, Identifiable {
    let id: Int
    let name: String
    let category: Category
    let uploadedAt: String
    let isActive: Bool
    let itemsCount: Int  // ← NUEVO
    
    enum CodingKeys: String, CodingKey {
        case id, name, category
        case uploadedAt = "uploaded_at"
        case isActive = "is_active"
        case itemsCount = "items_count"  // ← NUEVO
    }
}
