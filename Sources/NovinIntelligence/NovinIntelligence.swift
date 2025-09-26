import Foundation

/// Main NovinIntelligence SDK class
@available(iOS 15.0, macOS 12.0, *)
public final class NovinIntelligence: @unchecked Sendable {
    
    /// Shared singleton instance
    public static let shared = NovinIntelligence()
    
    private var isInitialized = false
    private let pythonBridge = PythonBridge.shared
    private let processingQueue = DispatchQueue(label: "com.novinintelligence.processing", qos: .userInitiated)
    
    private init() {}
    
    // MARK: - Initialization
    
    /// Initialize the NovinIntelligence SDK
    public func initialize(brandConfig: String? = nil) async throws {
        guard !isInitialized else { return }
        
        return try await withCheckedThrowingContinuation { continuation in
            processingQueue.async(execute: {
                do {
                    try self.pythonBridge.initialize()
                    self.isInitialized = true
                    print("✅ NovinIntelligence SDK initialized successfully")
                    continuation.resume(returning: ())
                } catch {
                    continuation.resume(throwing: NovinIntelligenceError.processingFailed("Initialization failed: \(error)"))
                }
            })
        }
    }
    
    // MARK: - Main API
    
    /// Process security event and return threat assessment
    public func assess(requestJson: String) async throws -> SecurityAssessment {
        guard isInitialized else {
            throw NovinIntelligenceError.notInitialized
        }
        
        return try await withCheckedThrowingContinuation { continuation in
            processingQueue.async(execute: {
                let result = self.pythonBridge.processRequest(requestJson)
                
                switch result {
                case .success(let responseJson):
                    do {
                        let assessment = try self.parseAssessment(from: responseJson)
                        continuation.resume(returning: assessment)
                    } catch {
                        continuation.resume(throwing: NovinIntelligenceError.processingFailed("Failed to parse response: \(error)"))
                    }
                case .failure(let error):
                    continuation.resume(throwing: error)
                }
            })
        }
    }
    
    /// Feed any security event to the AI engine
    public func feedSecurityEvent(_ event: Any) async {
        guard isInitialized else {
            print("⚠️ NovinIntelligence not initialized")
            return
        }
        
        if let jsonString = event as? String {
            _ = try? await assess(requestJson: jsonString)
        } else if let dictionary = event as? [String: Any],
                  let jsonData = try? JSONSerialization.data(withJSONObject: dictionary),
                  let jsonString = String(data: jsonData, encoding: .utf8) {
            _ = try? await assess(requestJson: jsonString)
        }
    }
    
    /// Set system mode for threat assessment context
    public func setSystemMode(_ mode: String) {
        print("🏠 System mode set to: \(mode)")
    }
    
    // MARK: - Private Helpers
    
    private func parseAssessment(from jsonString: String) throws -> SecurityAssessment {
        guard let data = jsonString.data(using: .utf8),
              let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw NovinIntelligenceError.processingFailed("Invalid JSON response")
        }
        
        // Extract fields from response
        guard let threatLevelString = json["threatLevel"] as? String,
              let threatLevel = ThreatLevel(rawValue: threatLevelString),
              let confidence = json["confidence"] as? Double,
              let processingTimeMs = json["processingTimeMs"] as? Double,
              let reasoning = json["reasoning"] as? String else {
            throw NovinIntelligenceError.processingFailed("Missing required fields in response")
        }
        
        let requestId = json["requestId"] as? String
        let timestamp = json["timestamp"].flatMap { "\($0)" }
        
        return SecurityAssessment(
            threatLevel: threatLevel,
            confidence: confidence,
            processingTimeMs: processingTimeMs,
            reasoning: reasoning,
            requestId: requestId,
            timestamp: timestamp
        )
    }
    
    /// Assess a motion event
    public func assessMotion(confidence: Double, location: String = "unknown") async throws -> SecurityAssessment {
        let motionJson = """
        {
            "type": "motion",
            "confidence": \(confidence),
            "timestamp": \(Date().timeIntervalSince1970),
            "metadata": {
                "location": "\(location)",
                "sensor_type": "motion_detector",
                "home_mode": "standard"
            }
        }
        """
        
        return try await assess(requestJson: motionJson)
    }
    
    /// Assess a door event
    public func assessDoorEvent(isOpening: Bool, location: String = "frontDoor") async throws -> SecurityAssessment {
        let doorJson = """
        {
            "type": "door_motion",
            "confidence": 0.9,
            "timestamp": \(Date().timeIntervalSince1970),
            "metadata": {
                "location": "\(location)",
                "motion_type": "\(isOpening ? "opening" : "closing")",
                "sensor_type": "contact_sensor",
                "home_mode": "standard"
            }
        }
        """
        
        return try await assess(requestJson: doorJson)
    }
}
