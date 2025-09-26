import XCTest
import Foundation
@testable import NovinIntelligence

/// PRODUCTION BRIDGE TESTS - Tests the complete Swift->C->Python->AI pipeline
/// These are NOT unit tests - these test the REAL system end-to-end
class ProductionBridgeTests: XCTestCase {
    
    private var novinAI: NovinIntelligence!
    private var initialMemory: UInt64 = 0
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        novinAI = NovinIntelligence.shared
        initialMemory = getMemoryUsage()
        
        // Initialize the REAL AI system
        let expectation = expectation(description: "AI Initialization")
        Task {
            do {
                try await novinAI.initialize()
                expectation.fulfill()
            } catch {
                XCTFail("Failed to initialize AI system: \(error)")
                expectation.fulfill()
            }
        }
        
        wait(for: [expectation], timeout: 30.0)
        XCTAssertTrue(novinAI.isInitialized, "AI system must be initialized for production tests")
    }
    
    override func tearDown() {
        let finalMemory = getMemoryUsage()
        let memoryDelta = Int64(finalMemory) - Int64(initialMemory)
        let memoryDeltaMB = Double(memoryDelta) / 1024 / 1024
        
        print("Memory Delta: \(String(format: "%.1f", memoryDeltaMB))MB")
        
        // Fail if memory leak > 50MB
        XCTAssertLessThan(abs(memoryDeltaMB), 50.0, "Memory leak detected: \(memoryDeltaMB)MB")
        
        super.tearDown()
    }
    
    // MARK: - PRODUCTION TESTS - REAL AI ENGINE
    
    func testRealMotionEventProcessing() async throws {
        let motionJson = """
        {
            "systemMode": "away",
            "location": {"lat": 40.7128, "lon": -74.0060},
            "deviceInfo": {"battery": 85},
            "events": [{
                "type": "motion", 
                "confidence": 0.89,
                "timestamp": "\(Date().ISO8601Format())",
                "metadata": {
                    "deviceId": "test_accelerometer",
                    "accelerometer": {"x": 0.2, "y": 0.1, "z": 9.8}
                }
            }]
        }
        """
        
        let startTime = Date()
        let assessment = try await novinAI.assess(requestJson: motionJson)
        let processingTime = Date().timeIntervalSince(startTime) * 1000
        
        // Verify REAL AI response structure
        XCTAssertNotNil(assessment.threatLevel)
        XCTAssertGreaterThan(assessment.confidence, 0.0)
        XCTAssertLessThanOrEqual(assessment.confidence, 1.0)
        XCTAssertGreaterThan(assessment.processingTimeMs, 0)
        
        // Performance requirements
        XCTAssertLessThan(processingTime, 500, "Motion processing took too long: \(processingTime)ms")
        
        print("✅ Motion Event: \(assessment.threatLevel) (\(String(format: "%.1f", assessment.confidence * 100))%) in \(String(format: "%.1f", processingTime))ms")
    }
    
    func testRealFaceDetectionProcessing() async throws {
        let faceJson = """
        {
            "systemMode": "away",
            "location": {"lat": 40.7128, "lon": -74.0060},
            "deviceInfo": {"battery": 92},
            "events": [{
                "type": "face",
                "confidence": 0.91,
                "timestamp": "\(Date().ISO8601Format())",
                "metadata": {
                    "deviceId": "front_camera",
                    "is_known": false,
                    "face_count": 1
                }
            }]
        }
        """
        
        let assessment = try await novinAI.assess(requestJson: faceJson)
        
        // Unknown face in away mode should be elevated or critical
        XCTAssertTrue(
            assessment.threatLevel == .elevated || assessment.threatLevel == .critical,
            "Unknown face in away mode should be elevated/critical, got: \(assessment.threatLevel)"
        )
        
        XCTAssertGreaterThan(assessment.confidence, 0.7, "Face detection confidence too low")
        
        print("✅ Face Detection: \(assessment.threatLevel) (\(String(format: "%.1f", assessment.confidence * 100))%)")
    }
    
    func testRealFireEmergencyProcessing() async throws {
        let fireJson = """
        {
            "systemMode": "home", 
            "location": {"lat": 40.7128, "lon": -74.0060},
            "deviceInfo": {"battery": 95},
            "events": [{
                "type": "fire",
                "confidence": 0.98,
                "timestamp": "\(Date().ISO8601Format())",
                "metadata": {
                    "deviceId": "smoke_detector_01",
                    "room": "kitchen"
                }
            }]
        }
        """
        
        let assessment = try await novinAI.assess(requestJson: fireJson)
        
        // Fire should ALWAYS be critical with high confidence
        XCTAssertEqual(assessment.threatLevel, .critical, "Fire events must be critical")
        XCTAssertGreaterThan(assessment.confidence, 0.9, "Fire detection confidence must be >90%")
        XCTAssertLessThan(assessment.processingTimeMs, 100, "Fire processing must be <100ms")
        
        print("✅ Fire Emergency: \(assessment.threatLevel) (\(String(format: "%.1f", assessment.confidence * 100))%)")
    }
    
    // MARK: - STRESS TESTS - REAL LOAD
    
    func testHighVolumeEventProcessing() async throws {
        let eventCount = 1000
        var processingTimes: [Double] = []
        var successCount = 0
        
        print("🔄 Processing \(eventCount) events...")
        
        for i in 0..<eventCount {
            let eventJson = """
            {
                "systemMode": "home",
                "location": {"lat": 40.7128, "lon": -74.0060},
                "deviceInfo": {"battery": 85},
                "events": [{
                    "type": "motion",
                    "confidence": \(0.5 + Double(i % 50) / 100),
                    "timestamp": "\(Date().ISO8601Format())",
                    "metadata": {
                        "deviceId": "stress_sensor_\(i % 10)",
                        "test_iteration": \(i)
                    }
                }]
            }
            """
            
            do {
                let startTime = Date()
                let assessment = try await novinAI.assess(requestJson: eventJson)
                let processingTime = Date().timeIntervalSince(startTime) * 1000
                
                processingTimes.append(processingTime)
                successCount += 1
                
                // Verify each response is valid
                XCTAssertNotNil(assessment.threatLevel)
                XCTAssertGreaterThan(assessment.confidence, 0.0)
                
                if i % 100 == 0 {
                    print("  Processed \(i) events...")
                }
                
            } catch {
                XCTFail("Event \(i) failed: \(error)")
            }
        }
        
        let avgProcessingTime = processingTimes.reduce(0, +) / Double(processingTimes.count)
        let maxProcessingTime = processingTimes.max() ?? 0
        let successRate = Double(successCount) / Double(eventCount) * 100
        
        print("✅ Stress Test Results:")
        print("  - Events Processed: \(successCount)/\(eventCount)")
        print("  - Success Rate: \(String(format: "%.1f", successRate))%")
        print("  - Avg Processing Time: \(String(format: "%.1f", avgProcessingTime))ms")
        print("  - Max Processing Time: \(String(format: "%.1f", maxProcessingTime))ms")
        
        // Production requirements
        XCTAssertEqual(successCount, eventCount, "All events must be processed successfully")
        XCTAssertLessThan(avgProcessingTime, 200, "Average processing time must be <200ms")
        XCTAssertLessThan(maxProcessingTime, 1000, "Max processing time must be <1000ms")
    }
    
    func testConcurrentEventProcessing() async throws {
        let concurrentEvents = 50
        let expectation = expectation(description: "Concurrent Processing")
        expectation.expectedFulfillmentCount = concurrentEvents
        
        var results: [SecurityAssessment] = []
        let resultsLock = NSLock()
        
        print("🔄 Processing \(concurrentEvents) concurrent events...")
        
        // Launch concurrent tasks
        for i in 0..<concurrentEvents {
            Task {
                let eventJson = """
                {
                    "systemMode": "away",
                    "location": {"lat": 40.7128, "lon": -74.0060},
                    "deviceInfo": {"battery": 85},
                    "events": [{
                        "type": "motion",
                        "confidence": 0.8,
                        "timestamp": "\(Date().ISO8601Format())",
                        "metadata": {
                            "deviceId": "concurrent_sensor_\(i)",
                            "thread_id": \(i)
                        }
                    }]
                }
                """
                
                do {
                    let assessment = try await self.novinAI.assess(requestJson: eventJson)
                    
                    resultsLock.lock()
                    results.append(assessment)
                    resultsLock.unlock()
                    
                    expectation.fulfill()
                } catch {
                    XCTFail("Concurrent event \(i) failed: \(error)")
                    expectation.fulfill()
                }
            }
        }
        
        await fulfillment(of: [expectation], timeout: 30.0)
        
        // Verify all events processed successfully
        XCTAssertEqual(results.count, concurrentEvents, "All concurrent events must be processed")
        
        // Verify no corruption in responses
        for (index, result) in results.enumerated() {
            XCTAssertNotNil(result.threatLevel, "Result \(index) missing threat level")
            XCTAssertGreaterThan(result.confidence, 0.0, "Result \(index) invalid confidence")
        }
        
        print("✅ Concurrent Processing: \(results.count) events processed successfully")
    }
    
    func testMemoryStabilityUnderLoad() async throws {
        let iterationCount = 500
        var memoryReadings: [UInt64] = []
        
        print("💾 Testing memory stability over \(iterationCount) iterations...")
        
        for i in 0..<iterationCount {
            let eventJson = """
            {
                "systemMode": "home",
                "location": {"lat": 40.7128, "lon": -74.0060},
                "deviceInfo": {"battery": 85},
                "events": [{
                    "type": "sound",
                    "confidence": 0.7,
                    "timestamp": "\(Date().ISO8601Format())",
                    "metadata": {
                        "deviceId": "memory_test_mic",
                        "decibels": \(60 + i % 20),
                        "iteration": \(i)
                    }
                }]
            }
            """
            
            let _ = try await novinAI.assess(requestJson: eventJson)
            
            // Sample memory every 50 iterations
            if i % 50 == 0 {
                let currentMemory = getMemoryUsage()
                memoryReadings.append(currentMemory)
                
                if i > 0 {
                    let memoryDelta = Int64(currentMemory) - Int64(memoryReadings[0])
                    let memoryDeltaMB = Double(memoryDelta) / 1024 / 1024
                    print("  Iteration \(i): Memory delta \(String(format: "%.1f", memoryDeltaMB))MB")
                }
            }
        }
        
        let initialMemory = memoryReadings.first!
        let finalMemory = memoryReadings.last!
        let memoryGrowth = Int64(finalMemory) - Int64(initialMemory)
        let memoryGrowthMB = Double(memoryGrowth) / 1024 / 1024
        
        print("✅ Memory Stability Results:")
        print("  - Initial Memory: \(String(format: "%.1f", Double(initialMemory) / 1024 / 1024))MB")
        print("  - Final Memory: \(String(format: "%.1f", Double(finalMemory) / 1024 / 1024))MB")
        print("  - Memory Growth: \(String(format: "%.1f", memoryGrowthMB))MB")
        
        // Production requirement: <20MB growth over 500 operations
        XCTAssertLessThan(abs(memoryGrowthMB), 20.0, "Memory growth too high: \(memoryGrowthMB)MB")
    }
    
    // MARK: - ERROR HANDLING TESTS
    
    func testMalformedInputHandling() async throws {
        let malformedInputs = [
            // Invalid JSON
            "{ invalid json }",
            
            // Missing required fields
            """{"systemMode": "home"}""",
            
            // Invalid data types
            """{"systemMode": 123, "location": "invalid", "events": "not_array"}""",
            
            // Invalid coordinates
            """{"systemMode": "home", "location": {"lat": 999, "lon": 999}, "events": []}""",
            
            // Empty events
            """{"systemMode": "home", "location": {"lat": 40.7128, "lon": -74.0060}, "events": []}"""
        ]
        
        print("🚨 Testing malformed input handling...")
        
        for (index, malformedJson) in malformedInputs.enumerated() {
            do {
                let assessment = try await novinAI.assess(requestJson: malformedJson)
                
                // If we get a response, it should indicate an error or ignore
                XCTAssertTrue(
                    assessment.threatLevel == .ignore || assessment.reasoning.contains("error"),
                    "Malformed input \(index) should be handled gracefully"
                )
                
                print("  ✅ Malformed input \(index) handled gracefully")
                
            } catch {
                // Expected behavior - malformed input should throw an error
                print("  ✅ Malformed input \(index) rejected with error: \(error)")
            }
        }
    }
    
    // MARK: - REAL-WORLD SCENARIO TESTS
    
    func testRealisticBreachScenario() async throws {
        print("🏠 Testing realistic break-in scenario...")
        
        // Simulate nighttime break-in: door → motion → sound sequence
        let breachEvents = [
            // 1. Front door opened at 2:15 AM
            """
            {
                "systemMode": "away",
                "location": {"lat": 40.7489, "lon": -73.9857},
                "deviceInfo": {"battery": 92},
                "events": [{
                    "type": "door",
                    "confidence": 0.97,
                    "timestamp": "2025-01-25T02:15:30Z",
                    "metadata": {
                        "deviceId": "front_door_sensor",
                        "state": "opened",
                        "location": "front_entrance"
                    }
                }]
            }
            """,
            
            // 2. Motion in hallway 3 seconds later
            """
            {
                "systemMode": "away",
                "location": {"lat": 40.7489, "lon": -73.9857},
                "deviceInfo": {"battery": 89},
                "events": [{
                    "type": "motion",
                    "confidence": 0.89,
                    "timestamp": "2025-01-25T02:15:33Z",
                    "metadata": {
                        "deviceId": "hallway_motion_sensor",
                        "accelerometer": {"x": 0.8, "y": 0.3, "z": 9.9},
                        "room": "hallway"
                    }
                }]
            }
            """,
            
            // 3. Sound detected 2 seconds later
            """
            {
                "systemMode": "away",
                "location": {"lat": 40.7489, "lon": -73.9857},
                "deviceInfo": {"battery": 89},
                "events": [{
                    "type": "sound",
                    "confidence": 0.82,
                    "timestamp": "2025-01-25T02:15:35Z",
                    "metadata": {
                        "deviceId": "living_room_microphone",
                        "decibels": 72.5,
                        "sound_type": "footsteps"
                    }
                }]
            }
            """
        ]
        
        var threatLevels: [ThreatLevel] = []
        var confidences: [Double] = []
        
        // Process each event individually
        for (index, eventJson) in breachEvents.enumerated() {
            let assessment = try await novinAI.assess(requestJson: eventJson)
            threatLevels.append(assessment.threatLevel)
            confidences.append(assessment.confidence)
            
            print("  Event \(index + 1): \(assessment.threatLevel) (\(String(format: "%.1f", assessment.confidence * 100))%)")
        }
        
        // The sequence should escalate to critical or elevated
        let finalThreatLevel = threatLevels.last!
        XCTAssertTrue(
            finalThreatLevel == .critical || finalThreatLevel == .elevated,
            "Realistic breach scenario should be critical/elevated, got: \(finalThreatLevel)"
        )
        
        // Confidence should be high for the final assessment
        let finalConfidence = confidences.last!
        XCTAssertGreaterThan(finalConfidence, 0.7, "Final confidence should be >70%")
        
        print("✅ Realistic Breach Scenario: Final threat \(finalThreatLevel) (\(String(format: "%.1f", finalConfidence * 100))%)")
    }
    
    // MARK: - HELPER FUNCTIONS
    
    private func getMemoryUsage() -> UInt64 {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size)/4
        
        let kerr: kern_return_t = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        
        if kerr == KERN_SUCCESS {
            return info.resident_size
        } else {
            return 0
        }
    }
}

// MARK: - PRODUCTION TEST RUNNER

extension ProductionBridgeTests {
    
    /// Run all production tests and generate report
    func testProductionReadiness() async throws {
        var testResults: [String: Any] = [:]
        var failedTests: [String] = []
        
        print("🚀 RUNNING PRODUCTION READINESS TESTS")
        print("=" * 60)
        
        let tests: [(String, () async throws -> Void)] = [
            ("Real Motion Event Processing", testRealMotionEventProcessing),
            ("Real Face Detection Processing", testRealFaceDetectionProcessing),
            ("Real Fire Emergency Processing", testRealFireEmergencyProcessing),
            ("High Volume Event Processing", testHighVolumeEventProcessing),
            ("Concurrent Event Processing", testConcurrentEventProcessing),
            ("Memory Stability Under Load", testMemoryStabilityUnderLoad),
            ("Malformed Input Handling", testMalformedInputHandling),
            ("Realistic Breach Scenario", testRealisticBreachScenario)
        ]
        
        var passedTests = 0
        
        for (testName, testFunc) in tests {
            do {
                print("\n🧪 Running: \(testName)")
                try await testFunc()
                passedTests += 1
                print("✅ PASSED: \(testName)")
            } catch {
                failedTests.append("\(testName): \(error)")
                print("❌ FAILED: \(testName) - \(error)")
            }
        }
        
        let totalTests = tests.count
        let successRate = Double(passedTests) / Double(totalTests) * 100
        
        print("\n" + "=" * 60)
        print("📊 PRODUCTION READINESS RESULTS")
        print("=" * 60)
        print("✅ Passed: \(passedTests)/\(totalTests) (\(String(format: "%.1f", successRate))%)")
        print("❌ Failed: \(failedTests.count)")
        
        if !failedTests.isEmpty {
            print("\n❌ FAILED TESTS:")
            for failure in failedTests {
                print("  - \(failure)")
            }
        }
        
        let productionReady = passedTests == totalTests
        print("\n🎯 PRODUCTION READY: \(productionReady ? "✅ YES" : "❌ NO")")
        
        // Save results
        testResults = [
            "total_tests": totalTests,
            "passed_tests": passedTests,
            "failed_tests": failedTests.count,
            "success_rate": successRate,
            "production_ready": productionReady,
            "failed_test_details": failedTests
        ]
        
        XCTAssertTrue(productionReady, "SDK is not production ready. Failed tests: \(failedTests)")
    }
}
