// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Grpc;

/**
 * This example shows how to use gRPC plugins.
 */
// ReSharper disable once InconsistentNaming
public static class Example35_GrpcPlugins
{
    public static async Task RunAsync()
    {
        Kernel kernel = new();

        // Import a gRPC plugin using one of the following Kernel extension methods
        // kernel.ImportGrpcPlugin
        // kernel.ImportGrpcPluginFromDirectory
        var plugin = kernel.ImportPluginFromGrpcFile("<path-to-.proto-file>", "<plugin-name>");

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var arguments = new KernelArguments();
        arguments["address"] = "<gRPC-server-address>";
        arguments["payload"] = "<gRPC-request-message-as-json>";

        // Run
        var result = await kernel.InvokeAsync(plugin["<operation-name>"], arguments);

        Console.WriteLine("Plugin response: {0}", result.GetValue<string>());
    }
}
