import Foundation

@MainActor
class AuthManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    init() {
        checkAuthStatus()
    }
    
    func checkAuthStatus() {
        isLoading = true
        Task {
            do {
                let user = try await APIService.shared.getCurrentUser()
                currentUser = user
                isAuthenticated = true
            } catch {
                isAuthenticated = false
                currentUser = nil
            }
            isLoading = false
        }
    }
    
    func login(username: String, password: String) async {
        isLoading = true
        errorMessage = nil
        
        do {
            _ = try await APIService.shared.login(username: username, password: password)
            let user = try await APIService.shared.getCurrentUser()
            currentUser = user
            isAuthenticated = true
        } catch {
            errorMessage = error.localizedDescription
            isAuthenticated = false
        }
        
        isLoading = false
    }
    
    func logout() {
        APIService.shared.logout()
        isAuthenticated = false
        currentUser = nil
    }
}
