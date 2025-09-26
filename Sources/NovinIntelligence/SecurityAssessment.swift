import Foundation

/// Threat level classification
public enum ThreatLevel: String, Codable {
    case standard
    case elevated
    case critical
}

/// Security assessment result from AI engine
public struct SecurityAssessment: Codable {
    public let threatLevel: ThreatLevel
    public let confidence: Double
    public let processingTimeMs: Double
    public let reasoning: String
    public let requestId: String?
    public let timestamp: String?
    
    public init(threatLevel: ThreatLevel, confidence: Double, processingTimeMs: Double, reasoning: String, requestId: String? = nil, timestamp: String? = nil) {
        self.threatLevel = threatLevel
        self.confidence = confidence
        self.processingTimeMs = processingTimeMs
        self.reasoning = reasoning
        self.requestId = requestId
        self.timestamp = timestamp
    }
}
