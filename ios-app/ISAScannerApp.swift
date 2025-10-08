import SwiftUI

@main
struct ISAScannerApp: App {
    @StateObject private var apiService = APIService()
    
    var body: some Scene {
        WindowGroup {
            if apiService.isAuthenticated {
                HomeView()
                    .environmentObject(apiService)
            } else {
                LoginView()
                    .environmentObject(apiService)
            }
        }
    }
}
