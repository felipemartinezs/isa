import Foundation

// MARK: - Category
enum Category: String, CaseIterable, Codable {
    case cctv = "CCTV"
    case cx = "CX"
    case fireBurgAlarm = "FIRE & BURG ALARM"
    
    var displayName: String {
        return self.rawValue
    }
}

// MARK: - Mode
enum ScanMode: String, CaseIterable, Codable {
    case inventory = "INVENTORY"
    case bom = "BOM"
    
    var displayName: String {
        return self.rawValue
    }
}

// MARK: - Status
enum ComparisonStatus: String, Codable {
    case match = "MATCH"
    case over = "OVER"
    case under = "UNDER"
    case pending = "PENDING"
    
    var color: String {
        switch self {
        case .match: return "green"
        case .over, .under: return "orange"
        case .pending: return "blue"
        }
    }
}

// MARK: - User
struct User: Codable {
    let id: Int
    let username: String
    let email: String
    let isActive: Bool
    let createdAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, username, email
        case isActive = "is_active"
        case createdAt = "created_at"
    }
}

// MARK: - Auth
struct LoginRequest: Codable {
    let username: String
    let password: String
}

struct LoginResponse: Codable {
    let accessToken: String
    let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
    }
}

// MARK: - BOM
struct BOM: Codable, Identifiable {
    let id: Int
    let name: String
    let category: Category
    let uploadedBy: Int
    let uploadedAt: String
    let isActive: Bool
    
    enum CodingKeys: String, CodingKey {
        case id, name, category
        case uploadedBy = "uploaded_by"
        case uploadedAt = "uploaded_at"
        case isActive = "is_active"
    }
}

// MARK: - Session
struct ScanSession: Codable, Identifiable {
    let id: Int
    let userId: Int
    let mode: ScanMode
    let category: Category
    let bomId: Int?
    let startedAt: String
    let endedAt: String?
    let isActive: Bool
    
    enum CodingKeys: String, CodingKey {
        case id, mode, category
        case userId = "user_id"
        case bomId = "bom_id"
        case startedAt = "started_at"
        case endedAt = "ended_at"
        case isActive = "is_active"
    }
}

struct CreateSessionRequest: Codable {
    let mode: ScanMode
    let category: Category
    let bomId: Int?
    
    enum CodingKeys: String, CodingKey {
        case mode, category
        case bomId = "bom_id"
    }
}

// MARK: - Scan Record
struct ScanRecord: Codable, Identifiable {
    let id: Int
    let sessionId: Int
    let sapArticle: String
    let partNumber: String?
    let description: String?
    let poNumber: String?
    let quantity: Double
    let scannedAt: String
    let manualEntry: Bool
    let expectedQuantity: Double?
    let status: ComparisonStatus?
    
    enum CodingKeys: String, CodingKey {
        case id
        case sessionId = "session_id"
        case sapArticle = "sap_article"
        case partNumber = "part_number"
        case description
        case poNumber = "po_number"
        case quantity
        case scannedAt = "scanned_at"
        case manualEntry = "manual_entry"
        case expectedQuantity = "expected_quantity"
        case status
    }
}

struct CreateScanRecordRequest: Codable {
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

// MARK: - Scanned Item (for display)
struct ScannedItem: Identifiable {
    let id = UUID()
    let articleNumber: String
    let poNumber: String?
    let timestamp: Date
}
