// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Plugins.Grpc.Model;
using Microsoft.SemanticKernel.Plugins.Grpc.Protobuf;

namespace Microsoft.SemanticKernel.Plugins.Grpc;

/// <summary>
/// <see cref="Kernel"/> extensions methods for gRPC functionality.
/// </summary>
public static class GrpcKernelExtensions
{
    // TODO: Revise XML comments and validate shape of methods is as desired

    /// <summary>
    /// Imports gRPC document from a directory.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="parentDirectory">Directory containing the plugin directory.</param>
    /// <param name="pluginDirectoryName">Name of the directory containing the selected plugin.</param>
    /// <returns>A list of all the prompt functions representing the plugin.</returns>
    public static KernelPlugin ImportPluginFromGrpcDirectory(
        this Kernel kernel,
        string parentDirectory,
        string pluginDirectoryName)
    {
        KernelPlugin plugin = CreatePluginFromGrpcDirectory(kernel, parentDirectory, pluginDirectoryName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Imports gRPC document from a file.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="filePath">File path to .proto document.</param>
    /// <param name="pluginName">Name of the plugin to register.</param>
    /// <returns>A list of all the prompt functions representing the plugin.</returns>
    public static KernelPlugin ImportPluginFromGrpcFile(
        this Kernel kernel,
        string filePath,
        string pluginName)
    {
        KernelPlugin plugin = CreatePluginFromGrpcFile(kernel, filePath, pluginName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Registers an gRPC plugin.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="documentStream">.proto document stream.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <returns>A list of all the prompt functions representing the plugin.</returns>
    public static KernelPlugin ImportPluginFromGrpc(
        this Kernel kernel,
        Stream documentStream,
        string pluginName)
    {
        KernelPlugin plugin = CreatePluginFromGrpc(kernel, documentStream, pluginName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Imports gRPC document from a directory.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="parentDirectory">Directory containing the plugin directory.</param>
    /// <param name="pluginDirectoryName">Name of the directory containing the selected plugin.</param>
    /// <returns>A list of all the prompt functions representing the plugin.</returns>
    public static KernelPlugin CreatePluginFromGrpcDirectory(
        this Kernel kernel,
        string parentDirectory,
        string pluginDirectoryName)
    {
        const string ProtoFile = "grpc.proto";

        KernelVerify.ValidPluginName(pluginDirectoryName, kernel.Plugins);

        var pluginDir = Path.Combine(parentDirectory, pluginDirectoryName);
        Verify.DirectoryExists(pluginDir);

        var filePath = Path.Combine(pluginDir, ProtoFile);
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"No .proto document for the specified path - {filePath} is found.");
        }

        if (kernel.LoggerFactory.CreateLogger(typeof(GrpcKernelExtensions)) is ILogger logger &&
            logger.IsEnabled(LogLevel.Trace))
        {
            logger.LogTrace("Registering gRPC functions from {0} .proto document", filePath);
        }

        using var stream = File.OpenRead(filePath);

        return kernel.CreatePluginFromGrpc(stream, pluginDirectoryName);
    }

    /// <summary>
    /// Imports gRPC document from a file.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="filePath">File path to .proto document.</param>
    /// <param name="pluginName">Name of the plugin to register.</param>
    /// <returns>A list of all the prompt functions representing the plugin.</returns>
    public static KernelPlugin CreatePluginFromGrpcFile(
        this Kernel kernel,
        string filePath,
        string pluginName)
    {
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"No .proto document for the specified path - {filePath} is found.");
        }

        if (kernel.LoggerFactory.CreateLogger(typeof(GrpcKernelExtensions)) is ILogger logger &&
            logger.IsEnabled(LogLevel.Trace))
        {
            logger.LogTrace("Registering gRPC functions from {0} .proto document", filePath);
        }

        using var stream = File.OpenRead(filePath);

        return kernel.CreatePluginFromGrpc(stream, pluginName);
    }

    /// <summary>
    /// Registers an gRPC plugin.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="documentStream">.proto document stream.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <returns>A list of all the prompt functions representing the plugin.</returns>
    public static KernelPlugin CreatePluginFromGrpc(
        this Kernel kernel,
        Stream documentStream,
        string pluginName)
    {
        Verify.NotNull(kernel);
        KernelVerify.ValidPluginName(pluginName, kernel.Plugins);

        // Parse
        var parser = new ProtoDocumentParser();

        var operations = parser.Parse(documentStream, pluginName);

        var functions = new List<KernelFunction>();

        ILoggerFactory loggerFactory = kernel.LoggerFactory;

        using var client = HttpClientProvider.GetHttpClient(kernel.Services.GetService<HttpClient>());

        var runner = new GrpcOperationRunner(client);

        ILogger logger = loggerFactory.CreateLogger(typeof(GrpcKernelExtensions)) ?? NullLogger.Instance;
        foreach (var operation in operations)
        {
            try
            {
                logger.LogTrace("Registering gRPC function {0}.{1}", pluginName, operation.Name);
                functions.Add(CreateGrpcFunction(runner, operation, loggerFactory));
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                //Logging the exception and keep registering other gRPC functions
                logger.LogWarning(ex, "Something went wrong while rendering the gRPC function. Function: {0}.{1}. Error: {2}",
                    pluginName, operation.Name, ex.Message);
            }
        }

        return KernelPluginFactory.CreateFromFunctions(pluginName, null, functions);
    }

    #region private

    /// <summary>
    /// Registers KernelFunctionFactory for a gRPC operation.
    /// </summary>
    /// <param name="runner">gRPC operation runner.</param>
    /// <param name="operation">The gRPC operation.</param>
    /// <param name="loggerFactory">The logger factory.</param>
    /// <returns>An instance of <see cref="KernelFunctionFromPrompt"/> class.</returns>
    private static KernelFunction CreateGrpcFunction(
        GrpcOperationRunner runner,
        GrpcOperation operation,
        ILoggerFactory loggerFactory)
    {
        async Task<JsonObject> ExecuteAsync(KernelArguments arguments, CancellationToken cancellationToken)
        {
            try
            {
                return await runner.RunAsync(operation, arguments, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex) when (!ex.IsCriticalException() && loggerFactory.CreateLogger(typeof(GrpcKernelExtensions)) is ILogger logger && logger.IsEnabled(LogLevel.Warning))
            {
                logger.LogWarning(ex, "Something went wrong while rendering the gRPC function. Function: {0}. Error: {1}", operation.Name, ex.Message);
                throw;
            }
        }

        return KernelFunctionFactory.CreateFromMethod(
            method: ExecuteAsync,
            parameters: GrpcOperation.CreateParameters(),
            description: operation.Name,
            functionName: operation.Name,
            loggerFactory: loggerFactory);
    }

    #endregion
}
