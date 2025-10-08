import SwiftUI

struct SessionPickerView: View {
    @EnvironmentObject var apiService: APIService
    @Environment(\.dismiss) var dismiss
    
    let activeSessions: [ScanSession]
    let onResumeSession: (ScanSession) -> Void
    let onStartNew: () -> Void
    
    @State private var selectedSession: ScanSession?
    
    var body: some View {
        NavigationView {
            VStack(spacing: 24) {
                // Header
                VStack(spacing: 8) {
                    Image(systemName: "arrow.triangle.2.circlepath")
                        .font(.system(size: 50))
                        .foregroundColor(.blue)
                    
                    Text("Active Sessions Found")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    Text("You have \(activeSessions.count) active session\(activeSessions.count == 1 ? "" : "s"). Would you like to resume or start fresh?")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
                .padding(.top, 40)
                
                // Sessions List
                ScrollView {
                    VStack(spacing: 12) {
                        ForEach(activeSessions) { session in
                            SessionCard(
                                session: session,
                                isSelected: selectedSession?.id == session.id,
                                onTap: { selectedSession = session }
                            )
                        }
                    }
                    .padding(.horizontal)
                }
                .onAppear {
                    // Auto-select first session
                    if selectedSession == nil && !activeSessions.isEmpty {
                        selectedSession = activeSessions[0]
                    }
                }
                
                Spacer()
                
                // Action Buttons
                VStack(spacing: 12) {   
                    Button(action: {
                        if let selected = selectedSession {
                            onResumeSession(selected)
                        }
                    }) {
                        Label("Resume Selected Session", systemImage: "play.fill")
                            .fontWeight(.semibold)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(selectedSession != nil ? Color.blue : Color.gray)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                    }
                    .disabled(selectedSession == nil)
                    
                    Button(action: {
                        onStartNew()
                    }) {
                        Label("Start New Session", systemImage: "plus.circle.fill")
                            .fontWeight(.semibold)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.green)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                    }
                }
                .padding()
            }
            .navigationTitle("Session Manager")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

struct SessionCard: View {
    let session: ScanSession
    let isSelected: Bool
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 16) {
                // Category Icon
                ZStack {
                    Circle()
                        .fill(categoryColor.opacity(0.2))
                        .frame(width: 50, height: 50)
                    
                    Image(systemName: categoryIcon)
                        .font(.system(size: 24))
                        .foregroundColor(categoryColor)
                }
                
                // Session Info
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(session.category?.displayName ?? "INVENTORY")
                            .font(.headline)
                            .foregroundColor(.primary)
                        
                        Text("Session #\(session.id)")
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(Color.blue.opacity(0.1))
                            .foregroundColor(.blue)
                            .cornerRadius(4)
                    }
                    
                    if let bomName = session.bomName {
                        Text("📋 \(bomName)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Text("Started \(timeAgo(from: session.startedAt))")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    
                    // Progress Badge (like Image 2)
                    HStack(spacing: 8) {
                        // Mode Badge
                        HStack(spacing: 4) {
                            Image(systemName: "barcode.viewfinder")
                                .font(.caption2)
                            Text(session.mode == .bom ? "BOM Mode" : "Inventory Mode")
                                .font(.caption2)
                        }
                        .foregroundColor(.blue)
                        
                        // Progress Badge (X/Y scanned) - only show if we have the data
                        if let scannedCount = session.scannedItemsCount,
                        let bomItemsCount = session.bomItemsCount,
                        session.mode == .bom {
                            Text("•")
                                .foregroundColor(.secondary)
                                .font(.caption2)
                            
                            HStack(spacing: 4) {
                                Text("\(scannedCount) / \(bomItemsCount)")
                                    .font(.caption2)
                                    .fontWeight(.medium)
                                Text("scanned")
                                    .font(.caption2)
                            }
                            .foregroundColor(.purple)
                        } else if let scannedCount = session.scannedItemsCount {
                            // Inventory mode - just show count
                            Text("•")
                                .foregroundColor(.secondary)
                                .font(.caption2)
                            
                            HStack(spacing: 4) {
                                Text("\(scannedCount)")
                                    .font(.caption2)
                                    .fontWeight(.medium)
                                Text("scanned")
                                    .font(.caption2)
                            }
                            .foregroundColor(.purple)
                        }
                    }
                }
                
                Spacer()
                
                // Selection indicator
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 28))
                        .foregroundColor(.blue)
                } else {
                    Image(systemName: "circle")
                        .font(.system(size: 28))
                        .foregroundColor(.gray.opacity(0.3))
                }
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(isSelected ? Color.blue.opacity(0.1) : Color(.systemGray6))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? Color.blue : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
    
    private var categoryColor: Color {
    switch session.category {
    case .cctv: return .purple
    case .cx: return .orange
    case .fireAlarm: return .red
    case .none: return .green  // INVENTORY mode
    }
}
    
    private var categoryIcon: String {
    switch session.category {
    case .cctv: return "video.fill"
    case .cx: return "network"
    case .fireAlarm: return "flame.fill"
    case .none: return "shippingbox.fill"  // INVENTORY mode
    }
}
    
    private func timeAgo(from dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }
        
        let interval = Date().timeIntervalSince(date)
        let hours = Int(interval / 3600)
        let minutes = Int((interval.truncatingRemainder(dividingBy: 3600)) / 60)
        
        if hours > 0 {
            return "\(hours)h \(minutes)m ago"
        } else {
            return "\(minutes)m ago"
        }
    }
}

#Preview {
    SessionPickerView(
        activeSessions: [
            ScanSession(
                id: 1,
                userId: 1,  // ← Necesario para el modelo
                mode: .bom,
                category: .cctv,
                bomId: 1,
                startedAt: ISO8601DateFormatter().string(from: Date().addingTimeInterval(-7200)),
                endedAt: nil,
                isActive: true,
                bomName: "Example BOM CCTV"  // ← Mock data, no afecta la app real
            ),
            ScanSession(
                id: 2,
                userId: 1,
                mode: .bom,
                category: .cx,
                bomId: 2,
                startedAt: ISO8601DateFormatter().string(from: Date().addingTimeInterval(-3600)),
                endedAt: nil,
                isActive: true,
                bomName: "Example BOM CX"  // ← Mock data, no afecta la app real
            )
        ],
        onResumeSession: { _ in },
        onStartNew: { }
    )
    .environmentObject(APIService())
}

