import SwiftUI

struct HomeView: View {
    @EnvironmentObject var apiService: APIService
    @State private var selectedCategory: Category = .cctv
    @State private var selectedMode: ScanMode = .inventory
    @State private var selectedBOM: BOM?
    @State private var availableBOMs: [BOM] = []
    @State private var isLoadingBOMs = false
    @State private var isCreatingSession = false
    @State private var currentSession: ScanSession?
    //@State private var showScanner = false
    @State private var showSessionPicker = false
    @State private var availableSessions: [ScanSession] = []
    @State private var errorMessage: String?
    
        var body: some View {
            NavigationView {
                ScrollView {
                    VStack(spacing: 24) {
                        userInfoSection
                        categorySelectionSection
                        modeSelectionSection
                        if selectedMode == .bom {
                            bomSelectionSection
                        }
                        Spacer()
                        errorMessageSection
                        startButton
                    }
                    .padding()
                }
                .navigationTitle("ISA Scanner")
                .navigationBarTitleDisplayMode(.inline)
                .onAppear {
                    loadBOMs()
                }
                .fullScreenCover(item: $currentSession) { session in
                    ScannerView(session: session, onEnd: {
                        print("🛑 Scanner ended - closing session #\(session.id)")
                        currentSession = nil
                    })
                    .environmentObject(apiService)
                    .onAppear {
                        print("✅ fullScreenCover opened with session #\(session.id)")
                        print("   Mode: \(session.mode), Category: \(session.category)")
                    }
                }
                .sheet(isPresented: $showSessionPicker) {
                    if !availableSessions.isEmpty {  // ← AGREGA ESTA LÍNEA
                        SessionPickerView(
                            activeSessions: availableSessions,
                            onResumeSession: { session in
                                showSessionPicker = false  // Cierra la sheet
                                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {  // Espera 0.5s
                                    resumeSession(session)  // LUEGO asigna y muestra scanner
                                }
                            },
                            onStartNew: {
                                createNewSession()
                            }
                        )
                        .environmentObject(apiService)
                    }  // ← AGREGA ESTA LÍNEA
                }
        
            }
        }
        // MARK: - View Components
        
        private var userInfoSection: some View {
            Group {
                if let user = apiService.currentUser {
                    HStack {
                        VStack(alignment: .leading) {
                            Text("Welcome, \(user.username)")
                                .font(.headline)
                            Text(user.email)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        Spacer()
                        Button("Logout") {
                            apiService.logout()
                        }
                        .foregroundColor(.red)
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(10)
                }
            }
        }
        
        private var categorySelectionSection: some View {
            VStack(alignment: .leading, spacing: 12) {
                Text("Select Category")
                    .font(.headline)
                
                Picker("Category", selection: $selectedCategory) {
                    ForEach(Category.allCases, id: \.self) { category in
                        Text(category.displayName).tag(category)
                    }
                }
                .pickerStyle(.segmented)
                .onChange(of: selectedCategory) { _ in
                    loadBOMs()
                }
            }
        }
        
        private var modeSelectionSection: some View {
            VStack(alignment: .leading, spacing: 12) {
                Text("Select Mode")
                    .font(.headline)
                
                Picker("Mode", selection: $selectedMode) {
                    ForEach(ScanMode.allCases, id: \.self) { mode in
                        Text(mode.displayName).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .onChange(of: selectedMode) { _ in
                    if selectedMode == .bom {
                        loadBOMs()
                    }
                }
            }
        }
        
        private var bomSelectionSection: some View {
            VStack(alignment: .leading, spacing: 12) {
                Text("Select BOM")
                    .font(.headline)
                
                if isLoadingBOMs {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                } else if availableBOMs.isEmpty {
                    Text("No BOMs available for \(selectedCategory.displayName)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding()
                        .background(Color(.systemGray6))
                        .cornerRadius(8)
                } else {
                    ScrollView {
                        VStack(spacing: 8) {
                            ForEach(availableBOMs) { bom in
                                bomCard(bom)
                            }
                        }
                    }
                    .frame(maxHeight: 200)
                }
            }
        }
        
        private func bomCard(_ bom: BOM) -> some View {
            Button(action: { selectedBOM = bom }) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(bom.name)
                            .font(.body)
                            .foregroundColor(.primary)
                        
                        HStack(spacing: 8) {
                            Text("\(bom.itemsCount) items")
                                .font(.caption)
                                .foregroundColor(.blue)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 2)
                                .background(Color.blue.opacity(0.1))
                                .cornerRadius(4)
                            
                            Text("Uploaded: \(formatDate(bom.uploadedAt))")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    Spacer()
                    if selectedBOM?.id == bom.id {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.blue)
                    }
                }
                .padding()
                .background(selectedBOM?.id == bom.id ? Color.blue.opacity(0.1) : Color(.systemGray6))
                .cornerRadius(8)
            }
        }
        
        @ViewBuilder
        private var errorMessageSection: some View {
            if let error = errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
                    .multilineTextAlignment(.center)
            }
        }
        
        private var startButton: some View {
            Button(action: checkForActiveSessions) {
                if isCreatingSession {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                } else {
                    Label("Start Scanning", systemImage: "barcode.viewfinder")
                        .fontWeight(.semibold)
                }
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(canStartSession ? Color.blue : Color.gray)
            .foregroundColor(.white)
            .cornerRadius(10)
            .disabled(!canStartSession || isCreatingSession)
        }
            
    
    private var canStartSession: Bool {
        if selectedMode == .bom {
            return selectedBOM != nil
        }
        return true
    }
    
    private func loadBOMs() {
        guard selectedMode == .bom else { return }
        
        isLoadingBOMs = true
        Task {
            do {
                availableBOMs = try await apiService.getBOMs(category: selectedCategory)
                if !availableBOMs.isEmpty && selectedBOM == nil {
                    selectedBOM = availableBOMs.first
                }
            } catch {
                errorMessage = "Failed to load BOMs: \(error.localizedDescription)"
            }
            isLoadingBOMs = false
        }
    }
    
    private func checkForActiveSessions() {
        Task {
            do {
                let sessions = try await apiService.getSessions(activeOnly: true)
                
                print("📱 Received \(sessions.count) active sessions:")
                for session in sessions {
                    print("   Session #\(session.id): bomName = '\(session.bomName ?? "nil")', scanned=\(session.scannedItemsCount ?? 0)/\(session.bomItemsCount ?? 0)")
                }
                
                if !sessions.isEmpty {
                    availableSessions = sessions
                    showSessionPicker = true
                } else {
                    // No active sessions, proceed with new session
                    createNewSession()
                }
            } catch {
                errorMessage = "Failed to check sessions: \(error.localizedDescription)"
            }
        }
    }
    
    private func createNewSession() {
        isCreatingSession = true
        errorMessage = nil
        
        Task {
            do {
                print("🆕 Creating new session")
                let session = try await apiService.createSession(
                    mode: selectedMode,
                    category: selectedCategory,
                    bomId: selectedBOM?.id
                )
                currentSession = session
                print("   ✅ Session created, fullScreenCover should open automatically")
            } catch {
                errorMessage = "Failed to start session: \(error.localizedDescription)"
            }
            isCreatingSession = false
        }
    }
    
    private func resumeSession(_ session: ScanSession) {
    print("🔄 Resuming existing session #\(session.id)")
    print("   Session data: mode=\(session.mode), category=\(session.category)")
    currentSession = session
    print("   ✅ currentSession assigned: \(currentSession?.id ?? -1)")
    print("   📱 fullScreenCover should open automatically via item binding")
}
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }
        
        let displayFormatter = DateFormatter()
        displayFormatter.dateStyle = .short
        displayFormatter.timeStyle = .short
        return displayFormatter.string(from: date)
    }
}

#Preview {
    HomeView()
        .environmentObject(APIService())
}
