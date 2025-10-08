import SwiftUI

struct ManualEntryView: View {
    @EnvironmentObject var scannerManager: ScannerManager
    @Environment(\.dismiss) var dismiss
    
    @State private var articleNumber = ""
    @State private var poNumber = ""
    @State private var quantity = "1"
    @State private var isSubmitting = false
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Article Information")) {
                    TextField("Article Number", text: $articleNumber)
                        .keyboardType(.numberPad)
                    
                    TextField("PO Number (Optional)", text: $poNumber)
                        .keyboardType(.numberPad)
                }
                
                Section(header: Text("Quantity")) {
                    HStack {
                        Button(action: { decrementQuantity() }) {
                            Image(systemName: "minus.circle.fill")
                                .font(.title2)
                                .foregroundColor(.red)
                        }
                        
                        Spacer()
                        
                        TextField("Quantity", text: $quantity)
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.center)
                            .font(.title)
                            .frame(width: 100)
                        
                        Spacer()
                        
                        Button(action: { incrementQuantity() }) {
                            Image(systemName: "plus.circle.fill")
                                .font(.title2)
                                .foregroundColor(.green)
                        }
                    }
                }
                
                Section {
                    Button(action: {
                        submitEntry()
                    }) {
                        if isSubmitting {
                            HStack {
                                Spacer()
                                ProgressView()
                                Spacer()
                            }
                        } else {
                            HStack {
                                Spacer()
                                Text("Submit")
                                    .fontWeight(.semibold)
                                Spacer()
                            }
                        }
                    }
                    .disabled(articleNumber.isEmpty || isSubmitting)
                }
                
                if let error = scannerManager.errorMessage {
                    Section {
                        Text(error)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Manual Entry")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func incrementQuantity() {
        if let current = Double(quantity) {
            quantity = String(format: "%.0f", current + 1)
        }
    }
    
    private func decrementQuantity() {
        if let current = Double(quantity), current > 1 {
            quantity = String(format: "%.0f", current - 1)
        }
    }
    
    private func submitEntry() {
        guard let qty = Double(quantity) else { return }
        
        isSubmitting = true
        
        Task {
            await scannerManager.submitScan(
                articleNumber: articleNumber,
                poNumber: poNumber.isEmpty ? nil : poNumber,
                quantity: qty,
                isManual: true
            )
            
            isSubmitting = false
            
            // Close if successful
            if scannerManager.errorMessage == nil {
                dismiss()
            }
        }
    }
}

#Preview {
    ManualEntryView()
        .environmentObject(ScannerManager())
}
