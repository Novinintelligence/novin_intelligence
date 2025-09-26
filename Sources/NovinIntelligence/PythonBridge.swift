import Foundation
import NovinPythonBridge

/// Python bridge for AI engine communication
public class PythonBridge {
    public static let shared = PythonBridge()
    
    private var isInitialized = false
    private let bridgeQueue = DispatchQueue(label: "com.novinintelligence.bridge", qos: .userInitiated)
    
    private init() {}
    
    /// Initialize Python runtime and AI engine via embedded CPython
    public func initialize() throws {
        guard !isInitialized else { return }

        // Resolve the framework bundle that contains the resources
        // Use the NovinIntelligence type to find the module bundle when embedded via SPM/xcframework
        let bundle = Bundle(for: NovinIntelligence.self)
        guard let pythonRoot = bundle.resourceURL?.appendingPathComponent("python") else {
            throw NovinIntelligenceError.processingFailed("Python resources not found in framework bundle")
        }

        let home = pythonRoot.path
        let stdlib = pythonRoot.appendingPathComponent("stdlib").path
        let site = pythonRoot.appendingPathComponent("site-packages").path
        let pathList = [home, stdlib, site].joined(separator: ":")

        // Call into C bridge to perform early PyConfig-based initialization
        let ok = home.withCString { homeC in
            pathList.withCString { pathC in
                novin_python_initialize(homeC, pathC)
            }
        }
        if !ok {
            throw NovinIntelligenceError.processingFailed("Failed to initialize embedded Python runtime")
        }
        isInitialized = true
    }
    
    /// Process security request through Python AI engine
    public func processRequest(_ requestJson: String, clientId: String = "ios_client") -> Result<String, NovinIntelligenceError> {
        guard isInitialized else {
            return .failure(.notInitialized)
        }
        // Basic validation
        if requestJson.data(using: .utf8) == nil {
            return .failure(.invalidInput("Request is not valid UTF-8"))
        }

        var errPtr: UnsafePointer<CChar>? = nil
        let responsePtr = requestJson.withCString { reqC in
            clientId.withCString { clientC in
                novin_python_process_request(reqC, clientC, nil, &errPtr)
            }
        }

        if let err = errPtr {
            let message = String(cString: err)
            novin_python_free_string(err)
            return .failure(.pythonError(message))
        }
        guard let resp = responsePtr else {
            return .failure(.processingFailed("No response from Python engine"))
        }
        let json = String(cString: resp)
        novin_python_free_string(resp)
        return .success(json)
    }
    
    // Remove simulated processing; all requests go through the C/Python bridge
    
    // Intentionally left out: real AI runs in Python now
    
    // Error response helpers now handled by Python side; Swift only maps errors
}
