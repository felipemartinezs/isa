import SwiftUI
import VisionKit

struct ScannerView: View {
    @EnvironmentObject var scannerManager: ScannerManager
    @State private var showingScanner = false
    @State private var showingManualEntry = false
    @State private var showingSessionConfig = false
    
    var body: some View {
        NavigationView {
            ZStack {
                if scannerManager.currentSession == nil {
                    // Session Configuration
                    SessionConfigView(showingSessionConfig: $showingSessionConfig)
                } else {
                    // Active Session View
                    ActiveSessionView(
                        showingScanner: $showingScanner,
                        showingManualEntry: $showingManualEntry
                    )
                }
            }
            .navigationTitle("Scanner")
            .navigationBarTitleDisplayMode(.large)
            .sheet(isPresented: $showingScanner) {
                if scannerManager.isDataScannerAvailable {
                    DataScannerView()
                } else {
                    Text("Data Scanner not available on this device")
                        .padding()
                }
            }
            .sheet(isPresented: $showingManualEntry) {
                ManualEntryView()
            }
        }
    }
}

// MARK: - Session Configuration View
struct SessionConfigView: View {
    @EnvironmentObject var scannerManager: ScannerManager
    @Binding var showingSessionConfig: Bool
    @State private var isLoading = false
    
    var body: some View {
        VStack(spacing: 24) {
            // Mode Selection
            VStack(alignment: .leading, spacing: 12) {
                Text("Mode")
                    .font(.headline)
                
                Picker("Mode", selection: $scannerManager.selectedMode) {
                    ForEach(ScanMode.allCases, id: \.self) { mode in
                        Text(mode.displayName).tag(mode)
                    }
                }
                .pickerStyle(SegmentedPickerStyle())
            }
            .padding(.horizontal)
            
            // Category Selection
            VStack(alignment: .leading, spacing: 12) {
                Text("Category")
                    .font(.headline)
                
                Picker("Category", selection: $scannerManager.selectedCategory) {
                    ForEach(Category.allCases, id: \.self) { category in
                        Text(category.displayName).tag(category)
                    }
                }
                .pickerStyle(MenuPickerStyle())
                .onChange(of: scannerManager.selectedCategory) { _ in
                    Task {
                        await scannerManager.loadBOMs()
                    }
                }
            }
            .padding(.horizontal)
            
            // BOM Selection (only in BOM mode)
            if scannerManager.selectedMode == .bom {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Select BOM")
                        .font(.headline)
                    
                    if scannerManager.availableBOMs.isEmpty {
                        Text("No BOMs available for this category")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(Color.gray.opacity(0.1))
                            .cornerRadius(8)
                    } else {
                        Picker("BOM", selection: $scannerManager.selectedBOM) {
                            Text("Select a BOM").tag(nil as BOM?)
                            ForEach(scannerManager.availableBOMs) { bom in
                                Text(bom.name).tag(bom as BOM?)
                            }
                        }
                        .pickerStyle(MenuPickerStyle())
                    }
                }
                .padding(.horizontal)
            }
            
            Spacer()
            
            // Start Session Button
            Button(action: {
                Task {
                    isLoading = true
                    await scannerManager.startSession()
                    isLoading = false
                }
            }) {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                } else {
                    Text("Start Session")
                        .fontWeight(.semibold)
                }
            }
            .frame(maxWidth: .infinity)
            .frame(height: 56)
            .background(canStartSession ? Color.blue : Color.gray)
            .foregroundColor(.white)
            .cornerRadius(12)
            .disabled(!canStartSession || isLoading)
            .padding(.horizontal)
            .padding(.bottom, 32)
            
            if let error = scannerManager.errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }
        }
        .padding(.top)
        .onAppear {
            Task {
                await scannerManager.loadBOMs()
            }
        }
    }
    
    private var canStartSession: Bool {
        if scannerManager.selectedMode == .bom {
            return scannerManager.selectedBOM != nil
        }
        return true
    }
}

// MARK: - Active Session View
struct ActiveSessionView: View {
    @EnvironmentObject var scannerManager: ScannerManager
    @Binding var showingScanner: Bool
    @Binding var showingManualEntry: Bool
    @State private var showingEndConfirmation = false
    
    var body: some View {
        VStack(spacing: 0) {
            // Session Info Header
            VStack(spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(scannerManager.selectedMode.displayName)
                            .font(.title2)
                            .fontWeight(.bold)
                        
                        Text(scannerManager.selectedCategory.displayName)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    Button("End Session") {
                        showingEndConfirmation = true
                    }
                    .font(.subheadline)
                    .foregroundColor(.red)
                }
                .padding()
                .background(Color.blue.opacity(0.1))
                
                // Last Scan Result
                if let lastScan = scannerManager.lastScanResult {
                    LastScanResultCard(record: lastScan)
                        .padding(.horizontal)
                }
            }
            
            // Scanned Items List
            ScrollView {
                LazyVStack(spacing: 12) {
                    ForEach(scannerManager.scannedItems) { item in
                        ScannedItemRow(item: item)
                    }
                }
                .padding()
            }
            
            Spacer()
            
            // Action Buttons
            HStack(spacing: 16) {
                Button(action: { showingScanner = true }) {
                    Label("Scan Label", systemImage: "viewfinder")
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                }
                
                Button(action: { showingManualEntry = true }) {
                    Label("Manual Entry", systemImage: "keyboard")
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                }
            }
            .padding()
        }
        .confirmationDialog("End Session", isPresented: $showingEndConfirmation) {
            Button("End Session", role: .destructive) {
                Task {
                    await scannerManager.endSession()
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Are you sure you want to end this session?")
        }
    }
}

// MARK: - Last Scan Result Card
struct LastScanResultCard: View {
    let record: ScanRecord
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Last Scan")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                if let status = record.status {
                    StatusBadge(status: status)
                }
            }
            
            Text(record.sapArticle)
                .font(.title3)
                .fontWeight(.bold)
            
            if let description = record.description {
                Text(description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            HStack {
                Text("Quantity: \(Int(record.quantity))")
                    .font(.subheadline)
                
                if let expected = record.expectedQuantity {
                    Text("Expected: \(Int(expected))")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(statusColor(record.status).opacity(0.1))
        .cornerRadius(12)
    }
    
    private func statusColor(_ status: ComparisonStatus?) -> Color {
        switch status {
        case .match: return .green
        case .over, .under: return .orange
        default: return .blue
        }
    }
}

// MARK: - Status Badge
struct StatusBadge: View {
    let status: ComparisonStatus
    
    var body: some View {
        Text(status.rawValue)
            .font(.caption)
            .fontWeight(.semibold)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(statusColor)
            .foregroundColor(.white)
            .cornerRadius(6)
    }
    
    private var statusColor: Color {
        switch status {
        case .match: return .green
        case .over, .under: return .orange
        case .pending: return .blue
        }
    }
}

// MARK: - Scanned Item Row
struct ScannedItemRow: View {
    let item: ScannedItem
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Article: \(item.articleNumber)")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                if let po = item.poNumber {
                    Text("PO: \(po)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Text(item.timestamp, style: .time)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Image(systemName: "checkmark.circle.fill")
                .foregroundColor(.green)
        }
        .padding()
        .background(Color.gray.opacity(0.05))
        .cornerRadius(8)
    }
}

#Preview {
    ScannerView()
        .environmentObject(ScannerManager())
}
