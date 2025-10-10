import Foundation

enum APIError: Error {
    case invalidURL
    case networkError(Error)
    case decodingError(Error)
    case httpError(Int, String)
    case unauthorized
    
    var localizedDescription: String {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        case .httpError(let code, let message):
            return "HTTP \(code): \(message)"
        case .unauthorized:
            return "Unauthorized - please login again"
        }
    }
}

@MainActor
class APIService: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    
    private let baseURL = "http://192.168.1.44:8000"
    private var authToken: String?
    
    // MARK: - Auth
    
    func login(username: String, password: String) async throws -> User {
        let url = URL(string: "\(baseURL)/auth/login")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: String] = [
            "username": username,
            "password": password
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError(NSError(domain: "", code: -1))
        }
        
        guard httpResponse.statusCode == 200 else {
            let message = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw APIError.httpError(httpResponse.statusCode, message)
        }
        
        let authResponse = try JSONDecoder().decode(AuthResponse.self, from: data)
        self.authToken = authResponse.accessToken
        self.isAuthenticated = true
        
        // Get user info
        let user = try await getCurrentUser()
        self.currentUser = user
        return user
    }
    
    func getCurrentUser() async throws -> User {
        let url = URL(string: "\(baseURL)/auth/me")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(authToken ?? "")", forHTTPHeaderField: "Authorization")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError(NSError(domain: "", code: -1))
        }
        
        guard httpResponse.statusCode == 200 else {
            if httpResponse.statusCode == 401 {
                self.isAuthenticated = false
                throw APIError.unauthorized
            }
            throw APIError.httpError(httpResponse.statusCode, "Failed to get user")
        }
        
        return try JSONDecoder().decode(User.self, from: data)
    }
    
    func logout() {
        self.authToken = nil
        self.isAuthenticated = false
        self.currentUser = nil
    }
    
    // MARK: - Scan Sessions
    
    func createSession(mode: ScanMode, category: Category, bomId: Int? = nil) async throws -> ScanSession {
        let url = URL(string: "\(baseURL)/scan/sessions")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(authToken ?? "")", forHTTPHeaderField: "Authorization")
        
        let body: [String: Any] = [
            "mode": mode.rawValue,
            "category": category.rawValue,
            "bom_id": bomId as Any
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError(NSError(domain: "", code: -1))
        }
        
        guard httpResponse.statusCode == 200 else {
            let message = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw APIError.httpError(httpResponse.statusCode, message)
        }
        
        return try JSONDecoder().decode(ScanSession.self, from: data)
    }
    
    func getSessions(activeOnly: Bool = false) async throws -> [ScanSession] {
        var urlString = "\(baseURL)/scan/sessions"
        if activeOnly {
            urlString += "?active_only=true"
        }
        
        let url = URL(string: urlString)!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(authToken ?? "")", forHTTPHeaderField: "Authorization")
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode([ScanSession].self, from: data)
    }
    
    func endSession(id: Int) async throws {
        let url = URL(string: "\(baseURL)/scan/sessions/\(id)/end")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(authToken ?? "")", forHTTPHeaderField: "Authorization")
        
        let (_, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.httpError(0, "Failed to end session")
        }
    }
    
    // MARK: - Scans
    
    func sendScan(sessionId: Int, sapArticle: String, poNumber: String? = nil, quantity: Double = 1.0) async throws -> ScanRecord {
        let url = URL(string: "\(baseURL)/scan/records")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(authToken ?? "")", forHTTPHeaderField: "Authorization")
        
        let scanRequest = ScanRequest(
            sessionId: sessionId,
            sapArticle: sapArticle,
            poNumber: poNumber,
            quantity: quantity,
            manualEntry: false
        )
        
        let encoder = JSONEncoder()
        request.httpBody = try encoder.encode(scanRequest)
        
        // Debug log
        if let jsonString = String(data: request.httpBody!, encoding: .utf8) {
            print("🔷 API Request: POST \(url)")
            print("🔷 Body: \(jsonString)")
            print("🔷 Token: \(authToken?.prefix(20) ?? "nil")...")
        }
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError(NSError(domain: "", code: -1))
        }
        
        print("🔷 Response Status: \(httpResponse.statusCode)")
        
        guard httpResponse.statusCode == 200 else {
            let message = String(data: data, encoding: .utf8) ?? "Unknown error"
            print("🔷 Error Response: \(message)")
            throw APIError.httpError(httpResponse.statusCode, message)
        }
        
        if let jsonString = String(data: data, encoding: .utf8) {
            print("🔷 Success Response: \(jsonString)")
        }
        
        return try JSONDecoder().decode(ScanRecord.self, from: data)
    }
    
    // MARK: - BOMs
    
    func getBOMs(category: Category) async throws -> [BOM] {
        let url = URL(string: "\(baseURL)/boms/?category=\(category.rawValue)")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(authToken ?? "")", forHTTPHeaderField: "Authorization")
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode([BOM].self, from: data)
    }

        // MARK: - Delete Scan Record
        func deleteScanRecord(id: Int) async throws {
            let url = URL(string: "\(baseURL)/scan/records/\(id)")!
            var request = URLRequest(url: url)
            request.httpMethod = "DELETE"
            
            if let token = authToken {
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            }
            
            let (_, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.networkError(NSError(domain: "", code: -1))
            }
            
            guard (200...299).contains(httpResponse.statusCode) else {
                throw APIError.httpError(httpResponse.statusCode, "Failed to delete record")
            }
        }
    }
