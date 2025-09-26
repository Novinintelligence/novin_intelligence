import Foundation

/// Error types for NovinIntelligence SDK
public enum NovinIntelligenceError: Error {
    case notInitialized
    case invalidInput(String)
    case processingFailed(String)
    case pythonError(String)
    
    public var localizedDescription: String {
        switch self {
        case .notInitialized:
            return "NovinIntelligence SDK is not initialized. Call initialize() first."
        case .invalidInput(let message):
            return "Invalid input: \(message)"
        case .processingFailed(let message):
            return "Processing failed: \(message)"
        case .pythonError(let message):
            return "Python error: \(message)"
        }
    }
}
