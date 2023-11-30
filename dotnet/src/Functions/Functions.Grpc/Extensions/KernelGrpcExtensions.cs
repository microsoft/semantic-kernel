// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Functions.Grpc.Model;
using Microsoft.SemanticKernel.Functions.Grpc.Protobuf;

namespace Microsoft.SemanticKernel.Functions.Grpc.Extensions;

/// <summary>
/// <see cref="Kernel"/> extensions methods for gRPC functionality.
/// </summary>
public static class KernelGrpcExtensions
{
    // TODO: Revise XML comments and validate shape of methods is as desired

    /// <summary>
    /// Imports gRPC document from a directory.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="parentDirectory">Directory containing the plugin directory.</param>
    /// <param name="pluginDirectoryName">Name of the directory containing the selected plugin.</param>
    /// <returns>A list of all the prompt functions representing the plugin.</returns>
    public static IKernelPlugin ImportPluginFromGrpcDirectory(
        this Kernel kernel,
        string parentDirectory,
        string pluginDirectoryName)
    {
        IKernelPlugin plugin = CreatePluginFromGrpcDirectory(kernel, parentDirectory, pluginDirectoryName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Imports gRPC document from a file.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="filePath">File path to .proto document.</param>
    /// <param name="pluginName">Name of the plugin to register.</param>
    /// <returns>A list of all the prompt functions representing the plugin.</returns>
    public static IKernelPlugin ImportPluginFromGrpcFile(
        this Kernel kernel,
        string filePath,
        string pluginName)
    {
        IKernelPlugin plugin = CreatePluginFromGrpcFile(kernel, filePath, pluginName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Registers an gRPC plugin.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="documentStream">.proto document stream.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <returns>A list of all the prompt functions representing the plugin.</returns>
    public static IKernelPlugin ImportPluginFromGrpc(
        this Kernel kernel,
        Stream documentStream,
        string pluginName)
    {
        IKernelPlugin plugin = CreatePluginFromGrpc(kernel, documentStream, pluginName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Imports gRPC document from a directory.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="parentDirectory">Directory containing the plugin directory.</param>
    /// <param name="pluginDirectoryName">Name of the directory containing the selected plugin.</param>
    /// <returns>A list of all the prompt functions representing the plugin.</returns>
    public static IKernelPlugin CreatePluginFromGrpcDirectory(
        this Kernel kernel,
        string parentDirectory,
        string pluginDirectoryName)
    {
        const string ProtoFile = "grpc.proto";

        Verify.ValidPluginName(pluginDirectoryName, kernel.Plugins);

        var pluginDir = Path.Combine(parentDirectory, pluginDirectoryName);
        Verify.DirectoryExists(pluginDir);

        var filePath = Path.Combine(pluginDir, ProtoFile);
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"No .proto document for the specified path - {filePath} is found.");
        }

        kernel.GetService<ILoggerFactory>().CreateLogger(typeof(KernelGrpcExtensions)).LogTrace("Registering gRPC functions from {0} .proto document", filePath);

        using var stream = File.OpenRead(filePath);

        return kernel.CreatePluginFromGrpc(stream, pluginDirectoryName);
    }

    /// <summary>
    /// Imports gRPC document from a file.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="filePath">File path to .proto document.</param>
    /// <param name="pluginName">Name of the plugin to register.</param>
    /// <returns>A list of all the prompt functions representing the plugin.</returns>
    public static IKernelPlugin CreatePluginFromGrpcFile(
        this Kernel kernel,
        string filePath,
        string pluginName)
    {
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"No .proto document for the specified path - {filePath} is found.");
        }

        kernel.GetService<ILoggerFactory>().CreateLogger(typeof(KernelGrpcExtensions)).LogTrace("Registering gRPC functions from {0} .proto document", filePath);

        using var stream = File.OpenRead(filePath);

        return kernel.CreatePluginFromGrpc(stream, pluginName);
    }

    /// <summary>
    /// Registers an gRPC plugin.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="documentStream">.proto document stream.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <returns>A list of all the prompt functions representing the plugin.</returns>
    public static IKernelPlugin CreatePluginFromGrpc(
        this Kernel kernel,
        Stream documentStream,
        string pluginName)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName, kernel.Plugins);

        // Parse
        var parser = new ProtoDocumentParser();

        var operations = parser.Parse(documentStream, pluginName);

        var plugin = new KernelPlugin(pluginName);

        ILoggerFactory loggerFactory = kernel.GetService<ILoggerFactory>();

        var client = HttpClientProvider.GetHttpClient(kernel.Services.GetService<HttpClient>());

        var runner = new GrpcOperationRunner(client);

        ILogger logger = loggerFactory.CreateLogger(typeof(KernelGrpcExtensions));
        foreach (var operation in operations)
        {
            try
            {
                logger.LogTrace("Registering gRPC function {0}.{1}", pluginName, operation.Name);
                plugin.AddFunction(CreateGrpcFunction(runner, operation, loggerFactory));
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                //Logging the exception and keep registering other gRPC functions
                logger.LogWarning(ex, "Something went wrong while rendering the gRPC function. Function: {0}.{1}. Error: {2}",
                    pluginName, operation.Name, ex.Message);
            }
        }

        return plugin;
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
        var operationParameters = operation.GetParameters();

        async Task<JsonObject> ExecuteAsync(KernelArguments arguments, CancellationToken cancellationToken)
        {
            try
            {
                return await runner.RunAsync(operation, arguments, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                loggerFactory.CreateLogger(typeof(KernelGrpcExtensions)).LogWarning(ex, "Something went wrong while rendering the gRPC function. Function: {0}. Error: {1}", operation.Name, ex.Message);
                throw;
            }
        }

        return KernelFunctionFactory.CreateFromMethod(
            method: ExecuteAsync,
            parameters: operationParameters.ToList(),
            description: operation.Name,
            functionName: operation.Name,
            loggerFactory: loggerFactory);
    }

    #endregion
}
