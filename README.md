# novin_intelligence (Swift Package)

This repository distributes the `novin_intelligence` binary as a Swift Package for easy integration.

- Binary: `novin_intelligence.xcframework` (device + simulator)
- Hosting: Raw GitHub URL (can migrate to GitHub Release later)
- Minimum iOS: 15

## Integrate via Swift Package Manager

Use the package URL and optionally the tag `1.0.0` once added:

```
https://github.com/Novinintelligence/novin_intelligence
```

For manual reference, the package manifest declares a binary target using the raw URL:

```swift
// Package.swift (distribution package)
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "novin_intelligence",
    platforms: [
        .iOS(.v15)
    ],
    products: [
        .library(name: "NovinIntelligence", targets: ["novin_intelligence"])
    ],
    targets: [
        .binaryTarget(
            name: "novin_intelligence",
            url: "https://raw.githubusercontent.com/Novinintelligence/novin_intelligence/main/artifacts/novin_intelligence.xcframework.zip",
            checksum: "93158d742b87531b1f77020c6692097b2cc8b09f535e0d41a687d29f517a4f76"
        )
    ]
)
```

## App usage example

```swift
import NovinIntelligence

@main
struct AppMain: App {
    init() {
        Task {
            try? await NovinIntelligence.shared.initialize()
        }
    }
    var body: some Scene { WindowGroup { ContentView() } }
}

// Pushing an example event
let doorEvent = """
{
  "type": "door_motion",
  "confidence": 0.87,
  "timestamp": \(Date().timeIntervalSince1970),
  "metadata": {
    "location": "Front Door",
    "motion_type": "opening",
    "home_mode": "night"
  }
}
"""

Task {
    do {
        let result = try await NovinIntelligence.shared.assess(requestJson: doorEvent)
        print(result)
    } catch {
        print("Assessment error: \(error)")
    }
}
```

## Notes
- For production, consider migrating the binary to a GitHub Release asset and updating the `url` accordingly.
- The current checksum corresponds to the committed zip in `artifacts/`.
- No additional Python setup is required by integrators.
