// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Grpc;

namespace Plugins;

// This example shows how to use gRPC plugins.
public class ImportPluginFromGrpc(ITestOutputHelper output) : BaseTest(output)
{
    [Fact(Skip = "Setup crendentials")]
    public async Task RunAsync()
    {
        Kernel kernel = new();

        // Import a gRPC plugin using one of the following Kernel extension methods
        // kernel.ImportGrpcPlugin
        // kernel.ImportGrpcPluginFromDirectory
        var plugin = kernel.ImportPluginFromGrpcFile("<path-to-.proto-file>", "<plugin-name>");

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var arguments = new KernelArguments
        {
            ["address"] = "<gRPC-server-address>",
            ["payload"] = "<gRPC-request-message-as-json>"
        };

        // Run
        var result = await kernel.InvokeAsync(plugin["<operation-name>"], arguments);

        Console.WriteLine($"Plugin response: {result.GetValue<string>()}");
    }
}
