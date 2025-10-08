import SwiftUI

struct HistoryView: View {
    @EnvironmentObject var scannerManager: ScannerManager
    @State private var sessions: [ScanSession] = []
    @State private var isLoading = false
    
    var body: some View {
        NavigationView {
            Group {
                if isLoading {
                    ProgressView("Loading sessions...")
                } else if sessions.isEmpty {
                    VStack(spacing: 16) {
                        Image(systemName: "clock")
                            .font(.system(size: 60))
                            .foregroundColor(.gray.opacity(0.5))
                        
                        Text("No Sessions Yet")
                            .font(.title2)
                            .fontWeight(.medium)
                        
                        Text("Your scan sessions will appear here")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                } else {
                    List {
                        ForEach(sessions) { session in
                            NavigationLink(destination: SessionDetailView(session: session)) {
                                SessionRow(session: session)
                            }
                        }
                    }
                    .listStyle(InsetGroupedListStyle())
                }
            }
            .navigationTitle("History")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: loadSessions) {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .onAppear {
                loadSessions()
            }
        }
    }
    
    private func loadSessions() {
        isLoading = true
        Task {
            do {
                sessions = try await APIService.shared.getActiveSessions()
            } catch {
                print("Failed to load sessions: \(error)")
            }
            isLoading = false
        }
    }
}

struct SessionRow: View {
    let session: ScanSession
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Session #\(session.id)")
                    .font(.headline)
                
                Spacer()
                
                if session.isActive {
                    Text("Active")
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.green.opacity(0.2))
                        .foregroundColor(.green)
                        .cornerRadius(6)
                }
            }
            
            HStack {
                Label(session.mode.displayName, systemImage: "doc.text")
                    .font(.subheadline)
                
                Spacer()
                
                Label(session.category.displayName, systemImage: "tag")
                    .font(.subheadline)
            }
            .foregroundColor(.secondary)
            
            Text("Started: \(formatDate(session.startedAt))")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateStyle = .medium
            displayFormatter.timeStyle = .short
            return displayFormatter.string(from: date)
        }
        return dateString
    }
}

struct SessionDetailView: View {
    let session: ScanSession
    @State private var records: [ScanRecord] = []
    @State private var isLoading = true
    
    var body: some View {
        Group {
            if isLoading {
                ProgressView("Loading records...")
            } else if records.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "tray")
                        .font(.system(size: 60))
                        .foregroundColor(.gray.opacity(0.5))
                    
                    Text("No Records")
                        .font(.title2)
                        .fontWeight(.medium)
                    
                    Text("No items scanned in this session")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
            } else {
                List(records) { record in
                    RecordRow(record: record)
                }
                .listStyle(InsetGroupedListStyle())
            }
        }
        .navigationTitle("Session #\(session.id)")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            loadRecords()
        }
    }
    
    private func loadRecords() {
        Task {
            do {
                records = try await APIService.shared.getSessionRecords(sessionId: session.id)
            } catch {
                print("Failed to load records: \(error)")
            }
            isLoading = false
        }
    }
}

struct RecordRow: View {
    let record: ScanRecord
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(record.sapArticle)
                    .font(.headline)
                
                Spacer()
                
                if let status = record.status {
                    StatusBadge(status: status)
                }
            }
            
            if let description = record.description {
                Text(description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            HStack {
                if let partNumber = record.partNumber {
                    Text("PN: \(partNumber)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Text("Qty: \(Int(record.quantity))")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                if let expected = record.expectedQuantity {
                    Text("Expected: \(Int(expected))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            if record.manualEntry {
                Text("Manual Entry")
                    .font(.caption)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.purple.opacity(0.2))
                    .foregroundColor(.purple)
                    .cornerRadius(4)
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    HistoryView()
        .environmentObject(ScannerManager())
}
