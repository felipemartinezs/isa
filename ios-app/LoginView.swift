import SwiftUI

struct LoginView: View {
    @EnvironmentObject var apiService: APIService
    @State private var username = "admin"
    @State private var password = "admin123"
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    var body: some View {
        NavigationView {
            VStack(spacing: 24) {
                // Logo
                Image(systemName: "barcode.viewfinder")
                    .font(.system(size: 80))
                    .foregroundColor(.blue)
                    .padding(.bottom, 20)
                
                Text("ISA")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Inventory Scanner App")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                // Login Form
                VStack(spacing: 16) {
                    TextField("Username", text: $username)
                        .textFieldStyle(.roundedBorder)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)
                    
                    SecureField("Password", text: $password)
                        .textFieldStyle(.roundedBorder)
                    
                    if let error = errorMessage {
                        Text(error)
                            .font(.caption)
                            .foregroundColor(.red)
                            .multilineTextAlignment(.center)
                    }
                    
                    Button(action: handleLogin) {
                        if isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        } else {
                            Text("Login")
                                .fontWeight(.semibold)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                    .disabled(isLoading || username.isEmpty || password.isEmpty)
                }
                .padding(.horizontal, 40)
                
                Spacer()
                
                Text("Dev Credentials: admin / admin123")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                    .padding(.bottom)
            }
            .padding()
            .navigationTitle("")
            .navigationBarHidden(true)
        }
    }
    
    private func handleLogin() {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                _ = try await apiService.login(username: username, password: password)
            } catch {
                errorMessage = error.localizedDescription
            }
            isLoading = false
        }
    }
}

#Preview {
    LoginView()
        .environmentObject(APIService())
}
