import XCTest
@testable import NovinIntelligence

final class NovinIntelligenceTests: XCTestCase {

    override func setUpWithError() throws {
        // Put setup code here. This method is called before the invocation of each test method in the class.
        try super.setUpWithError()

        // Initialize SDK for testing
        let brandConfig = createTestBrandConfig()
        try NovinIntelligence.shared.initialize(brandConfig: brandConfig)
    }

    override func tearDownWithError() throws {
        // Put teardown code here. This method is called after the invocation of each test method in the class.
        try super.tearDownWithError()
    }

    func testSdkInitialization() throws {
        XCTAssertTrue(NovinIntelligence.shared.isReady, "SDK should be ready after initialization")
        XCTAssertEqual(NovinIntelligence.shared.version, "1.0.0", "Version should be 1.0.0")
    }

    func testMotionDetectionAssessment() async throws {
        let requestJson = createMotionDetectionRequest()

        let assessment = try await NovinIntelligence.shared.assess(requestJson: requestJson)

        // Validate assessment structure
        XCTAssertNotNil(assessment.requestId, "Should have request ID")
        XCTAssertTrue(["ignore", "standard", "elevated", "critical"].contains(assessment.threatAssessment.level.rawValue),
                     "Threat level should be valid")
        XCTAssertTrue((0.0...1.0).contains(assessment.threatAssessment.confidence),
                     "Confidence should be between 0 and 1")
        XCTAssertTrue(assessment.processingTimeMs >= 0, "Processing time should be non-negative")
    }

    func testFaceDetectionAssessment() async throws {
        let requestJson = createFaceDetectionRequest()

        let assessment = try await NovinIntelligence.shared.assess(requestJson: requestJson)

        // Face detection should typically result in higher threat levels
        XCTAssertTrue(["elevated", "critical"].contains(assessment.threatAssessment.level.rawValue),
                     "Face detection should trigger elevated or critical threat")
    }

    func testEmergencyEventAssessment() async throws {
        let requestJson = createEmergencyRequest()

        let assessment = try await NovinIntelligence.shared.assess(requestJson: requestJson)

        // Emergency events should always result in critical threat
        XCTAssertEqual(assessment.threatAssessment.level, .critical,
                      "Emergency events should always be critical")
    }

    func testAwayModeAssessment() async throws {
        let requestJson = createAwayModeRequest()

        let assessment = try await NovinIntelligence.shared.assess(requestJson: requestJson)

        XCTAssertEqual(assessment.context.systemMode, "away", "System mode should be away")

        // Away mode should generally increase sensitivity
        XCTAssertTrue(assessment.threatAssessment.level != .ignore,
                     "Away mode should not ignore potential threats")
    }

    func testInvalidJsonHandling() async throws {
        let invalidJson = "{ invalid json }"

        do {
            _ = try await NovinIntelligence.shared.assess(requestJson: invalidJson)
            XCTFail("Should throw exception for invalid JSON")
        } catch let error as NovinIntelligenceError {
            XCTAssertTrue(error.errorDescription?.contains("JSON") == true,
                         "Error should mention JSON parsing")
        }
    }

    func testLocationBasedAssessment() async throws {
        let requestJson = createLocationBasedRequest()

        let assessment = try await NovinIntelligence.shared.assess(requestJson: requestJson)

        // Should include location risk assessment
        XCTAssertFalse(assessment.context.locationRisk.isEmpty,
                      "Should include location risk assessment")
    }

    func testConvenienceMethods() async throws {
        // Test motion detection convenience method
        let motionAssessment = try await NovinIntelligence.shared.assessMotion(confidence: 0.8)
        XCTAssertTrue(["ignore", "standard", "elevated", "critical"].contains(motionAssessment.threatAssessment.level.rawValue),
                     "Motion assessment should return valid threat level")

        // Test face detection convenience method
        let faceAssessment = try await NovinIntelligence.shared.assessFaceDetection(confidence: 0.9, isKnown: false)
        XCTAssertTrue(["elevated", "critical"].contains(faceAssessment.threatAssessment.level.rawValue),
                     "Unknown face should trigger elevated or critical threat")
    }

    func testConcurrentRequests() async throws {
        let requestJson = createMotionDetectionRequest()

        // Create multiple concurrent requests
        async let request1 = NovinIntelligence.shared.assess(requestJson: requestJson)
        async let request2 = NovinIntelligence.shared.assess(requestJson: requestJson)
        async let request3 = NovinIntelligence.shared.assess(requestJson: requestJson)

        let results = try await [request1, request2, request3]

        XCTAssertEqual(results.count, 3, "Should complete all concurrent requests")

        // All results should have valid threat levels
        for result in results {
            XCTAssertTrue(["ignore", "standard", "elevated", "critical"].contains(result.threatAssessment.level.rawValue),
                         "All concurrent requests should return valid threat levels")
        }
    }

    func testPerformanceUnderLoad() async throws {
        let requestJson = createMotionDetectionRequest()
        var totalTime: TimeInterval = 0
        let iterations = 10

        for _ in 1...iterations {
            let startTime = Date()
            _ = try await NovinIntelligence.shared.assess(requestJson: requestJson)
            let endTime = Date()
            totalTime += endTime.timeIntervalSince(startTime)
        }

        let averageTime = totalTime / Double(iterations)
        XCTAssertTrue(averageTime < 0.2, "Average processing time should be under 200ms: \(averageTime)")
    }

    func testThreatLevelEnum() {
        // Test all threat levels
        XCTAssertEqual(ThreatLevel.ignore.rawValue, "ignore")
        XCTAssertEqual(ThreatLevel.standard.rawValue, "standard")
        XCTAssertEqual(ThreatLevel.elevated.rawValue, "elevated")
        XCTAssertEqual(ThreatLevel.critical.rawValue, "critical")
    }

    func testErrorHandling() async {
        // Test with empty request
        let emptyRequest = "{}"

        do {
            _ = try await NovinIntelligence.shared.assess(requestJson: emptyRequest)
            XCTFail("Should throw error for empty request")
        } catch let error as NovinIntelligenceError {
            XCTAssertNotNil(error.errorDescription, "Error should have description")
        }
    }

    // MARK: - Helper Methods

    private func createTestBrandConfig() -> String {
        return """
        {
            "brand": {
                "name": "TestBrand",
                "version": "1.0.0"
            },
            "ai": {
                "model": {
                    "confidenceThreshold": 0.5,
                    "emergencyThreshold": 0.9
                }
            },
            "security": {
                "rateLimiting": {
                    "requestsPerMinute": 100
                }
            }
        }
        """
    }

    private func createMotionDetectionRequest() -> String {
        return """
        {
            "systemMode": "home",
            "location": {"lat": 37.7749, "lon": -122.4194},
            "deviceInfo": {"battery": 85, "deviceId": "test-device-ios-001"},
            "events": [
                {
                    "type": "motion",
                    "confidence": 0.8,
                    "timestamp": "\(ISO8601DateFormatter().string(from: Date()))",
                    "metadata": {"zone": "living_room"}
                }
            ]
        }
        """
    }

    private func createFaceDetectionRequest() -> String {
        return """
        {
            "systemMode": "home",
            "location": {"lat": 37.7749, "lon": -122.4194},
            "events": [
                {
                    "type": "face",
                    "confidence": 0.9,
                    "timestamp": "\(ISO8601DateFormatter().string(from: Date()))",
                    "metadata": {"is_known": "false", "person_id": "unknown"}
                }
            ]
        }
        """
    }

    private func createEmergencyRequest() -> String {
        return """
        {
            "systemMode": "home",
            "events": [
                {
                    "type": "fire",
                    "confidence": 0.95,
                    "timestamp": "\(ISO8601DateFormatter().string(from: Date()))",
                    "metadata": {"alarm_type": "fire_detector"}
                }
            ]
        }
        """
    }

    private func createAwayModeRequest() -> String {
        return """
        {
            "systemMode": "away",
            "events": [
                {
                    "type": "motion",
                    "confidence": 0.6,
                    "timestamp": "\(ISO8601DateFormatter().string(from: Date()))"
                }
            ]
        }
        """
    }

    private func createLocationBasedRequest() -> String {
        return """
        {
            "systemMode": "home",
            "location": {"lat": 40.7128, "lon": -74.0060},
            "events": [
                {
                    "type": "motion",
                    "confidence": 0.7,
                    "timestamp": "\(ISO8601DateFormatter().string(from: Date()))"
                }
            ]
        }
        """
    }
}