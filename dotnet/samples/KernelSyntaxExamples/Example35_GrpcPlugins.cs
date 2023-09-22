// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.Grpc.Extensions;
using Microsoft.SemanticKernel.Orchestration;
using RepoUtils;

/**
 * This example shows how to use gRPC plugins.
 */

// ReSharper disable once InconsistentNaming
public static class Example35_GrpcPlugins
{
    public static async Task RunAsync()
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();

        // Import a gRPC plugin using one of the following Kernel extension methods
        // kernel.RegisterGrpcPlugin
        // kernel.ImportGrpcPluginFromDirectory
        var plugin = kernel.ImportGrpcPluginFromFile("<plugin-name>", "<path-to-.proto-file>");

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("address", "<gRPC-server-address>");
        contextVariables.Set("payload", "<gRPC-request-message-as-json>");

        // Run
        var result = await kernel.RunAsync(contextVariables, plugin["<operation-name>"]);

        Console.WriteLine("Skill response: {0}", result);
    }
}
