import XCTest
@testable import NovinIntelligence

@available(iOS 15.0, *)
final class IOSIntegrationTests: XCTestCase {
    func testProcessSingleEvent() async throws {
        try await NovinIntelligence.shared.initialize()

        let timestamp = ISO8601DateFormatter().string(from: Date())

        let request = """
        {
            "systemMode": "away",
            "location": {"lat": 40.7128, "lon": -74.0060},
            "deviceInfo": {"battery": 85},
            "events": [{
                "type": "motion",
                "confidence": 0.89,
                "timestamp": "\(timestamp)",
                "metadata": {"deviceId": "ios_test_sensor"}
            }]
        }
        """

        let assessment = try await NovinIntelligence.shared.assess(requestJson: request)

        XCTAssertNotNil(assessment.requestId)
        XCTAssertGreaterThan(assessment.confidence, 0.0)
    }
}
