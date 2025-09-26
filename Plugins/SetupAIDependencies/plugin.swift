import PackagePlugin
import Foundation

@main
struct SetupAIDependencies: BuildToolPlugin {
    func createBuildCommands(context: PluginContext, target: Target) async throws -> [Command] {
        let setupScript = context.package.directory.appending(subpath: "setup_novin_sdk.sh")
        
        return [
            .buildCommand(
                displayName: "Setup NovinIntelligence AI Dependencies",
                executable: .init("/bin/bash"),
                arguments: [setupScript.string],
                environment: [:],
                inputFiles: [setupScript],
                outputFiles: []
            )
        ]
    }
}
