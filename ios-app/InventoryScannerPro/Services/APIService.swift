import Foundation

enum APIError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case unauthorized
    case serverError(String)
    case decodingError
    case networkError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .unauthorized:
            return "Unauthorized. Please login again."
        case .serverError(let message):
            return message
        case .decodingError:
            return "Failed to decode response"
        case .networkError(let error):
            return error.localizedDescription
        }
    }
}

class APIService {
    static let shared = APIService()
    
    // Change this to your backend URL
    private let baseURL = "http://localhost:8000"
    
    private var authToken: String? {
        get { UserDefaults.standard.string(forKey: "authToken") }
        set { UserDefaults.standard.set(newValue, forKey: "authToken") }
    }
    
    // MARK: - Auth
    func login(username: String, password: String) async throws -> LoginResponse {
        let request = LoginRequest(username: username, password: password)
        let response: LoginResponse = try await post("/auth/login", body: request, requiresAuth: false)
        authToken = response.accessToken
        return response
    }
    
    func getCurrentUser() async throws -> User {
        return try await get("/auth/me")
    }
    
    func logout() {
        authToken = nil
    }
    
    // MARK: - BOMs
    func getBOMs(category: Category) async throws -> [BOM] {
        return try await get("/boms/?category=\(category.rawValue)")
    }
    
    // MARK: - Scan Sessions
    func createSession(mode: ScanMode, category: Category, bomId: Int?) async throws -> ScanSession {
        let request = CreateSessionRequest(mode: mode, category: category, bomId: bomId)
        return try await post("/scan/sessions", body: request)
    }
    
    func getActiveSessions() async throws -> [ScanSession] {
        return try await get("/scan/sessions?active_only=true")
    }
    
    func endSession(id: Int) async throws {
        let _: EmptyResponse = try await post("/scan/sessions/\(id)/end", body: EmptyRequest())
    }
    
    // MARK: - Scan Records
    func createScanRecord(sessionId: Int, sapArticle: String, poNumber: String?, quantity: Double, manualEntry: Bool) async throws -> ScanRecord {
        let request = CreateScanRecordRequest(
            sessionId: sessionId,
            sapArticle: sapArticle,
            poNumber: poNumber,
            quantity: quantity,
            manualEntry: manualEntry
        )
        return try await post("/scan/records", body: request)
    }
    
    func getSessionRecords(sessionId: Int) async throws -> [ScanRecord] {
        return try await get("/scan/sessions/\(sessionId)/records")
    }
    
    // MARK: - Generic Request Methods
    private func get<T: Decodable>(_ path: String) async throws -> T {
        guard let url = URL(string: baseURL + path) else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        return try await performRequest(request)
    }
    
    private func post<T: Decodable, B: Encodable>(_ path: String, body: B, requiresAuth: Bool = true) async throws -> T {
        guard let url = URL(string: baseURL + path) else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if requiresAuth, let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        request.httpBody = try encoder.encode(body)
        
        return try await performRequest(request)
    }
    
    private func performRequest<T: Decodable>(_ request: URLRequest) async throws -> T {
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            switch httpResponse.statusCode {
            case 200...299:
                let decoder = JSONDecoder()
                decoder.keyDecodingStrategy = .convertFromSnakeCase
                do {
                    return try decoder.decode(T.self, from: data)
                } catch {
                    print("Decoding error: \(error)")
                    if let jsonString = String(data: data, encoding: .utf8) {
                        print("Response JSON: \(jsonString)")
                    }
                    throw APIError.decodingError
                }
            case 401:
                throw APIError.unauthorized
            default:
                if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                    throw APIError.serverError(errorResponse.detail)
                }
                throw APIError.serverError("Server error: \(httpResponse.statusCode)")
            }
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }
}

// MARK: - Helper Types
struct EmptyRequest: Codable {}
struct EmptyResponse: Codable {}
struct ErrorResponse: Codable {
    let detail: String
}
