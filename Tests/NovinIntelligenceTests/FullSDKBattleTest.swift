import XCTest
import Foundation
@testable import NovinIntelligence

/// FULL SDK BATTLE TEST - Tests the COMPLETE Swift→C→Python→AI stack
/// This simulates exactly how brands would download and use the SDK
/// NO SHORTCUTS - Every event goes through the full integration
class FullSDKBattleTest: XCTestCase {
    
    private var sdk: NovinIntelligence!
    private var initialMemory: UInt64 = 0
    private var testResults: [String: Any] = [:]
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        print("🚀 FULL SDK BATTLE TEST - REAL INTEGRATION")
        print("=" * 60)
        print("📱 Simulating brand downloading and using SDK...")
        
        // Simulate brand getting SDK instance (exactly as they would)
        sdk = NovinIntelligence.shared
        initialMemory = getMemoryUsage()
        
        // Initialize SDK exactly as brands would
        let expectation = expectation(description: "SDK Initialization")
        Task {
            do {
                print("🔧 Brand initializing SDK...")
                try await sdk.initialize()
                print("✅ SDK initialized - ready for brand events")
                expectation.fulfill()
            } catch {
                XCTFail("❌ SDK initialization failed: \(error)")
                expectation.fulfill()
            }
        }
        
        wait(for: [expectation], timeout: 30.0)
        XCTAssertTrue(sdk.isInitialized, "SDK must be initialized for full stack test")
    }
    
    override func tearDown() {
        let finalMemory = getMemoryUsage()
        let memoryDelta = Int64(finalMemory) - Int64(initialMemory)
        let memoryDeltaMB = Double(memoryDelta) / 1024 / 1024
        
        print("\n💾 Full SDK Memory Impact: \(String(format: "%.1f", memoryDeltaMB))MB")
        
        // Record memory results
        testResults["memory_delta_mb"] = memoryDeltaMB
        testResults["memory_leak_detected"] = abs(memoryDeltaMB) > 100
        
        super.tearDown()
    }
    
    // MARK: - SINGLE EVENT TESTS (Full Stack)
    
    func testBrandMotionEventThroughFullSDK() async throws {
        print("\n🎯 TEST: Brand Motion Event → Full SDK Stack")
        
        // Exactly what a brand would send
        let brandMotionJson = """
        {
            "systemMode": "away",
            "location": {"lat": 40.7128, "lon": -74.0060},
            "deviceInfo": {"battery": 85, "model": "iPhone 15 Pro"},
            "events": [{
                "type": "motion",
                "confidence": 0.89,
                "timestamp": "\(Date().ISO8601Format())",
                "metadata": {
                    "deviceId": "brand_accelerometer_01",
                    "accelerometer": {"x": 0.2, "y": 0.1, "z": 9.8},
                    "sensor_type": "core_motion"
                }
            }]
        }
        """
        
        print("📱 Brand sending motion event through SDK...")
        
        let startTime = Date()
        // THIS IS THE REAL SDK CALL - Swift→C→Python→AI
        let assessment = try await sdk.assess(requestJson: brandMotionJson)
        let totalTime = Date().timeIntervalSince(startTime) * 1000
        
        print("📊 FULL SDK RESULTS:")
        print("   ✅ Threat Level: \(assessment.threatLevel)")
        print("   ✅ Confidence: \(String(format: "%.3f", assessment.confidence))")
        print("   ✅ Full Stack Time: \(String(format: "%.1f", totalTime))ms")
        print("   ✅ AI Processing Time: \(String(format: "%.1f", assessment.processingTimeMs))ms")
        print("   ✅ Bridge Overhead: \(String(format: "%.1f", totalTime - assessment.processingTimeMs))ms")
        
        // Verify this went through the complete stack
        XCTAssertNotNil(assessment.threatLevel)
        XCTAssertGreaterThan(assessment.confidence, 0.0)
        XCTAssertGreaterThan(assessment.processingTimeMs, 0)
        XCTAssertLessThan(totalTime, 500) // Full stack should be <500ms
        
        testResults["single_motion_total_time_ms"] = totalTime
        testResults["single_motion_bridge_overhead_ms"] = totalTime - assessment.processingTimeMs
    }
    
    func testBrandFaceEventThroughFullSDK() async throws {
        print("\n🎯 TEST: Brand Face Event → Full SDK Stack")
        
        let brandFaceJson = """
        {
            "systemMode": "away",
            "location": {"lat": 40.7128, "lon": -74.0060},
            "deviceInfo": {"battery": 92, "camera_active": true},
            "events": [{
                "type": "face",
                "confidence": 0.91,
                "timestamp": "\(Date().ISO8601Format())",
                "metadata": {
                    "deviceId": "brand_front_camera",
                    "is_known": false,
                    "face_count": 1,
                    "detection_source": "vision_framework"
                }
            }]
        }
        """
        
        print("📱 Brand sending face detection through SDK...")
        
        let startTime = Date()
        let assessment = try await sdk.assess(requestJson: brandFaceJson)
        let totalTime = Date().timeIntervalSince(startTime) * 1000
        
        print("📊 FACE DETECTION RESULTS:")
        print("   ✅ Threat Level: \(assessment.threatLevel)")
        print("   ✅ Unknown Person Logic: \(assessment.threatLevel == .elevated || assessment.threatLevel == .critical ? "WORKING" : "FAILED")")
        print("   ✅ Full Stack Time: \(String(format: "%.1f", totalTime))ms")
        
        // Unknown face in away mode should be elevated/critical
        XCTAssertTrue(assessment.threatLevel == .elevated || assessment.threatLevel == .critical)
        XCTAssertGreaterThan(assessment.confidence, 0.7)
    }
    
    func testBrandFireEmergencyThroughFullSDK() async throws {
        print("\n🎯 TEST: Brand Fire Emergency → Full SDK Stack")
        
        let brandFireJson = """
        {
            "systemMode": "home",
            "location": {"lat": 40.7128, "lon": -74.0060},
            "deviceInfo": {"battery": 95},
            "events": [{
                "type": "fire",
                "confidence": 0.98,
                "timestamp": "\(Date().ISO8601Format())",
                "metadata": {
                    "deviceId": "brand_smoke_detector",
                    "room": "kitchen",
                    "detector_type": "photoelectric"
                }
            }]
        }
        """
        
        print("📱 Brand sending fire emergency through SDK...")
        
        let startTime = Date()
        let assessment = try await sdk.assess(requestJson: brandFireJson)
        let totalTime = Date().timeIntervalSince(startTime) * 1000
        
        print("📊 EMERGENCY OVERRIDE RESULTS:")
        print("   ✅ Threat Level: \(assessment.threatLevel) (MUST BE CRITICAL)")
        print("   ✅ Emergency Speed: \(String(format: "%.1f", totalTime))ms (MUST BE <200ms)")
        print("   ✅ Confidence: \(String(format: "%.3f", assessment.confidence))")
        
        // Fire MUST be critical with high confidence and fast processing
        XCTAssertEqual(assessment.threatLevel, .critical)
        XCTAssertGreaterThan(assessment.confidence, 0.9)
        XCTAssertLessThan(totalTime, 200) // Emergency must be <200ms
    }
    
    // MARK: - HIGH VOLUME TESTS (Full Stack)
    
    func testBrandHighVolumeEventsThroughFullSDK() async throws {
        print("\n🔥 HIGH VOLUME TEST: 500 Events → Full SDK Stack")
        
        let eventCount = 500
        var processingTimes: [Double] = []
        var bridgeOverheads: [Double] = []
        var successCount = 0
        var memoryReadings: [Double] = []
        
        print("📱 Brand sending \(eventCount) events through SDK...")
        
        for i in 0..<eventCount {
            let brandEventJson = """
            {
                "systemMode": "\(i % 2 == 0 ? "home" : "away")",
                "location": {"lat": 40.7128, "lon": -74.0060},
                "deviceInfo": {"battery": \(85 - i % 20)},
                "events": [{
                    "type": "motion",
                    "confidence": \(0.5 + Double(i % 50) / 100),
                    "timestamp": "\(Date().ISO8601Format())",
                    "metadata": {
                        "deviceId": "brand_sensor_\(i % 10)",
                        "test_iteration": \(i),
                        "accelerometer": {
                            "x": \(0.1 + Double(i % 20) / 100),
                            "y": \(0.1 + Double(i % 15) / 100),
                            "z": \(9.8 + Double(i % 10) / 100)
                        }
                    }
                }]
            }
            """
            
            do {
                let startTime = Date()
                // REAL SDK CALL - Full Stack
                let assessment = try await sdk.assess(requestJson: brandEventJson)
                let totalTime = Date().timeIntervalSince(startTime) * 1000
                let bridgeOverhead = totalTime - assessment.processingTimeMs
                
                processingTimes.append(totalTime)
                bridgeOverheads.append(bridgeOverhead)
                successCount += 1
                
                // Memory sampling every 50 events
                if i % 50 == 0 {
                    let currentMemory = Double(getMemoryUsage()) / 1024 / 1024
                    memoryReadings.append(currentMemory)
                    print("   Event \(i): \(String(format: "%.1f", totalTime))ms, Memory: \(String(format: "%.1f", currentMemory))MB")
                }
                
                // Verify each response
                XCTAssertNotNil(assessment.threatLevel)
                XCTAssertGreaterThan(assessment.confidence, 0.0)
                
            } catch {
                XCTFail("Event \(i) failed through full SDK: \(error)")
            }
        }
        
        let avgProcessingTime = processingTimes.reduce(0, +) / Double(processingTimes.count)
        let maxProcessingTime = processingTimes.max() ?? 0
        let avgBridgeOverhead = bridgeOverheads.reduce(0, +) / Double(bridgeOverheads.count)
        let successRate = Double(successCount) / Double(eventCount) * 100
        
        print("\n📊 HIGH VOLUME RESULTS:")
        print("   ✅ Events Processed: \(successCount)/\(eventCount)")
        print("   ✅ Success Rate: \(String(format: "%.1f", successRate))%")
        print("   ✅ Avg Full Stack Time: \(String(format: "%.1f", avgProcessingTime))ms")
        print("   ✅ Max Processing Time: \(String(format: "%.1f", maxProcessingTime))ms")
        print("   ✅ Avg Bridge Overhead: \(String(format: "%.1f", avgBridgeOverhead))ms")
        print("   ✅ Memory Growth: \(String(format: "%.1f", memoryReadings.last! - memoryReadings.first!))MB")
        
        // Production requirements for full stack
        XCTAssertEqual(successCount, eventCount, "All events must process through full SDK")
        XCTAssertLessThan(avgProcessingTime, 300, "Avg full stack time must be <300ms")
        XCTAssertLessThan(maxProcessingTime, 1500, "Max processing time must be <1500ms")
        XCTAssertLessThan(avgBridgeOverhead, 50, "Bridge overhead must be <50ms average")
        
        testResults["high_volume_success_rate"] = successRate
        testResults["high_volume_avg_time_ms"] = avgProcessingTime
        testResults["high_volume_bridge_overhead_ms"] = avgBridgeOverhead
    }
    
    // MARK: - CONCURRENT ACCESS TESTS (Full Stack)
    
    func testBrandConcurrentAccessThroughFullSDK() async throws {
        print("\n⚡ CONCURRENT TEST: 100 Parallel Events → Full SDK Stack")
        
        let concurrentCount = 100
        var results: [SecurityAssessment] = []
        let resultsLock = NSLock()
        
        print("📱 Brand sending \(concurrentCount) concurrent events through SDK...")
        
        await withTaskGroup(of: Void.self) { group in
            for i in 0..<concurrentCount {
                group.addTask {
                    let brandEventJson = """
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
                                "thread_id": \(i),
                                "concurrent_test": true
                            }
                        }]
                    }
                    """
                    
                    do {
                        // REAL CONCURRENT SDK CALLS - Testing GIL handling
                        let assessment = try await self.sdk.assess(requestJson: brandEventJson)
                        
                        resultsLock.lock()
                        results.append(assessment)
                        resultsLock.unlock()
                        
                    } catch {
                        XCTFail("Concurrent event \(i) failed through full SDK: \(error)")
                    }
                }
            }
        }
        
        print("📊 CONCURRENT ACCESS RESULTS:")
        print("   ✅ Concurrent Events: \(results.count)/\(concurrentCount)")
        print("   ✅ Thread Safety: \(results.count == concurrentCount ? "PASS" : "FAIL")")
        print("   ✅ GIL Handling: \(results.count == concurrentCount ? "WORKING" : "BROKEN")")
        
        // Verify no corruption or deadlocks
        XCTAssertEqual(results.count, concurrentCount, "All concurrent events must complete")
        
        for (index, result) in results.enumerated() {
            XCTAssertNotNil(result.threatLevel, "Concurrent result \(index) corrupted")
            XCTAssertGreaterThan(result.confidence, 0.0, "Concurrent result \(index) invalid")
        }
        
        testResults["concurrent_success_count"] = results.count
        testResults["concurrent_thread_safety"] = results.count == concurrentCount
    }
    
    // MARK: - MEMORY STRESS TEST (Full Stack)
    
    func testBrandMemoryStabilityThroughFullSDK() async throws {
        print("\n💾 MEMORY STRESS: 1000 Events → Full SDK Memory Analysis")
        
        let stressCount = 1000
        var memoryReadings: [Double] = []
        let initialMemory = Double(getMemoryUsage()) / 1024 / 1024
        
        print("📱 Brand stress testing SDK memory with \(stressCount) events...")
        print("   Initial Memory: \(String(format: "%.1f", initialMemory))MB")
        
        for i in 0..<stressCount {
            let brandEventJson = """
            {
                "systemMode": "home",
                "location": {"lat": 40.7128, "lon": -74.0060},
                "deviceInfo": {"battery": 85},
                "events": [{
                    "type": "sound",
                    "confidence": 0.7,
                    "timestamp": "\(Date().ISO8601Format())",
                    "metadata": {
                        "deviceId": "memory_stress_mic",
                        "decibels": \(60 + i % 20),
                        "stress_iteration": \(i)
                    }
                }]
            }
            """
            
            // REAL SDK CALL - Testing memory across bridge
            let _ = try await sdk.assess(requestJson: brandEventJson)
            
            // Sample memory every 100 events
            if i % 100 == 0 {
                let currentMemory = Double(getMemoryUsage()) / 1024 / 1024
                memoryReadings.append(currentMemory)
                let memoryGrowth = currentMemory - initialMemory
                print("   Event \(i): \(String(format: "%.1f", currentMemory))MB (\(String(format: "%+.1f", memoryGrowth))MB)")
            }
        }
        
        let finalMemory = Double(getMemoryUsage()) / 1024 / 1024
        let totalMemoryGrowth = finalMemory - initialMemory
        let memoryPerEvent = totalMemoryGrowth / Double(stressCount)
        
        print("📊 MEMORY STRESS RESULTS:")
        print("   ✅ Final Memory: \(String(format: "%.1f", finalMemory))MB")
        print("   ✅ Total Growth: \(String(format: "%+.1f", totalMemoryGrowth))MB")
        print("   ✅ Per Event: \(String(format: "%.3f", memoryPerEvent))MB")
        print("   ✅ Memory Leak: \(abs(totalMemoryGrowth) > 200 ? "DETECTED" : "NONE")")
        
        // Production memory requirements
        XCTAssertLessThan(abs(totalMemoryGrowth), 200, "Memory growth too high: \(totalMemoryGrowth)MB")
        XCTAssertLessThan(memoryPerEvent, 0.5, "Per-event memory too high: \(memoryPerEvent)MB")
        
        testResults["memory_stress_total_growth_mb"] = totalMemoryGrowth
        testResults["memory_stress_per_event_mb"] = memoryPerEvent
    }
    
    // MARK: - ERROR HANDLING TESTS (Full Stack)
    
    func testBrandErrorHandlingThroughFullSDK() async throws {
        print("\n🚨 ERROR HANDLING: Malformed Events → Full SDK Stack")
        
        let malformedEvents = [
            // Invalid JSON
            "{ invalid json }",
            
            // Missing fields
            """{"systemMode": "home"}""",
            
            // Invalid types
            """{"systemMode": 123, "location": "invalid"}""",
            
            // Extreme values
            """{"systemMode": "home", "location": {"lat": 999, "lon": 999}, "events": []}""",
            
            // Empty string
            "",
            
            // Null
            "null"
        ]
        
        print("📱 Brand sending malformed events through SDK...")
        
        var handledGracefully = 0
        
        for (index, malformedJson) in malformedEvents.enumerated() {
            do {
                // REAL SDK CALL with malformed data
                let assessment = try await sdk.assess(requestJson: malformedJson)
                
                // If we get here, SDK handled it gracefully
                if assessment.threatLevel == .ignore {
                    handledGracefully += 1
                    print("   ✅ Malformed \(index): Handled gracefully")
                }
                
            } catch {
                // Expected - SDK should throw errors for malformed input
                handledGracefully += 1
                print("   ✅ Malformed \(index): Rejected with error")
            }
        }
        
        let errorHandlingRate = Double(handledGracefully) / Double(malformedEvents.count) * 100
        
        print("📊 ERROR HANDLING RESULTS:")
        print("   ✅ Malformed Tests: \(malformedEvents.count)")
        print("   ✅ Handled Gracefully: \(handledGracefully)")
        print("   ✅ Error Handling Rate: \(String(format: "%.1f", errorHandlingRate))%")
        
        XCTAssertEqual(handledGracefully, malformedEvents.count, "All malformed inputs must be handled")
        
        testResults["error_handling_rate"] = errorHandlingRate
    }
    
    // MARK: - COMPREHENSIVE BATTLE TEST
    
    func testFullSDKBattleTest() async throws {
        print("\n🚀 COMPREHENSIVE FULL SDK BATTLE TEST")
        print("=" * 60)
        
        var allTestsPassed = true
        let testStartTime = Date()
        
        // Run all tests
        do {
            try await testBrandMotionEventThroughFullSDK()
            try await testBrandFaceEventThroughFullSDK()
            try await testBrandFireEmergencyThroughFullSDK()
            try await testBrandHighVolumeEventsThroughFullSDK()
            try await testBrandConcurrentAccessThroughFullSDK()
            try await testBrandMemoryStabilityThroughFullSDK()
            try await testBrandErrorHandlingThroughFullSDK()
        } catch {
            allTestsPassed = false
            print("❌ Battle test failed: \(error)")
        }
        
        let totalTestTime = Date().timeIntervalSince(testStartTime)
        
        print("\n" + "=" * 60)
        print("🎯 FULL SDK BATTLE TEST RESULTS")
        print("=" * 60)
        print("✅ All Tests Passed: \(allTestsPassed ? "YES" : "NO")")
        print("✅ Total Test Time: \(String(format: "%.1f", totalTestTime))s")
        print("✅ Stack Tested: Swift → C Bridge → Python GIL → AI Engine")
        print("✅ Integration Verified: COMPLETE")
        
        // Final assessment
        let productionReady = allTestsPassed && 
                            (testResults["memory_leak_detected"] as? Bool == false) &&
                            (testResults["concurrent_thread_safety"] as? Bool == true)
        
        print("\n🎯 PRODUCTION READY: \(productionReady ? "✅ YES" : "❌ NO")")
        
        if productionReady {
            print("🚀 The NovinIntelligence SDK is BATTLE-TESTED and ready for brand integration!")
        } else {
            print("⚠️  The SDK needs fixes before production release.")
        }
        
        XCTAssertTrue(productionReady, "Full SDK must be production ready")
    }
    
    // MARK: - Helper Functions
    
    private func getMemoryUsage() -> UInt64 {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size)/4
        
        let kerr: kern_return_t = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        
        return kerr == KERN_SUCCESS ? info.resident_size : 0
    }
}
