// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Functions.Grpc.Model;
using Microsoft.SemanticKernel.Functions.Grpc.Protobuf;
using Microsoft.SemanticKernel.Orchestration;

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
    /// <param name="httpClient">HttpClient to use for sending requests.</param>
    /// <returns>A list of all the semantic functions representing the plugin.</returns>
    public static ISKPlugin ImportPluginFromGrpcDirectory(
        this Kernel kernel,
        string parentDirectory,
        string pluginDirectoryName,
        HttpClient? httpClient = null)
    {
        ISKPlugin plugin = CreatePluginFromGrpcDirectory(kernel, parentDirectory, pluginDirectoryName, httpClient);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Imports gRPC document from a file.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="filePath">File path to .proto document.</param>
    /// <param name="pluginName">Name of the plugin to register.</param>
    /// <param name="httpClient">HttpClient to use for sending requests.</param>
    /// <returns>A list of all the semantic functions representing the plugin.</returns>
    public static ISKPlugin ImportPluginFromGrpcFile(
        this Kernel kernel,
        string filePath,
        string pluginName,
        HttpClient? httpClient = null)
    {
        ISKPlugin plugin = CreatePluginFromGrpcFile(kernel, filePath, pluginName, httpClient);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Registers an gRPC plugin.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="documentStream">.proto document stream.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="httpClient">HttpClient to use for sending requests.</param>
    /// <returns>A list of all the semantic functions representing the plugin.</returns>
    public static ISKPlugin ImportPluginFromGrpc(
        this Kernel kernel,
        Stream documentStream,
        string pluginName,
        HttpClient? httpClient = null)
    {
        ISKPlugin plugin = CreatePluginFromGrpc(kernel, documentStream, pluginName, httpClient);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Imports gRPC document from a directory.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="parentDirectory">Directory containing the plugin directory.</param>
    /// <param name="pluginDirectoryName">Name of the directory containing the selected plugin.</param>
    /// <param name="httpClient">HttpClient to use for sending requests.</param>
    /// <returns>A list of all the semantic functions representing the plugin.</returns>
    public static ISKPlugin CreatePluginFromGrpcDirectory(
        this Kernel kernel,
        string parentDirectory,
        string pluginDirectoryName,
        HttpClient? httpClient = null)
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

        kernel.LoggerFactory
              .CreateLogger(typeof(KernelGrpcExtensions))
              .LogTrace("Registering gRPC functions from {0} .proto document", filePath);

        using var stream = File.OpenRead(filePath);

        return kernel.CreatePluginFromGrpc(stream, pluginDirectoryName, httpClient);
    }

    /// <summary>
    /// Imports gRPC document from a file.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="filePath">File path to .proto document.</param>
    /// <param name="pluginName">Name of the plugin to register.</param>
    /// <param name="httpClient">HttpClient to use for sending requests.</param>
    /// <returns>A list of all the semantic functions representing the plugin.</returns>
    public static ISKPlugin CreatePluginFromGrpcFile(
        this Kernel kernel,
        string filePath,
        string pluginName,
        HttpClient? httpClient = null)
    {
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"No .proto document for the specified path - {filePath} is found.");
        }

        kernel.LoggerFactory
              .CreateLogger(typeof(KernelGrpcExtensions))
              .LogTrace("Registering gRPC functions from {0} .proto document", filePath);

        using var stream = File.OpenRead(filePath);

        return kernel.CreatePluginFromGrpc(stream, pluginName, httpClient);
    }

    /// <summary>
    /// Registers an gRPC plugin.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="documentStream">.proto document stream.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="httpClient">HttpClient to use for sending requests.</param>
    /// <returns>A list of all the semantic functions representing the plugin.</returns>
    public static ISKPlugin CreatePluginFromGrpc(
        this Kernel kernel,
        Stream documentStream,
        string pluginName,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName, kernel.Plugins);

        // Parse
        var parser = new ProtoDocumentParser();

        var operations = parser.Parse(documentStream, pluginName);

        var plugin = new SKPlugin(pluginName);

        var client = HttpClientProvider.GetHttpClient(kernel.HttpHandlerFactory, httpClient, kernel.LoggerFactory);

        var runner = new GrpcOperationRunner(client);

        ILogger logger = kernel.LoggerFactory.CreateLogger(typeof(KernelGrpcExtensions));
        foreach (var operation in operations)
        {
            try
            {
                logger.LogTrace("Registering gRPC function {0}.{1}", pluginName, operation.Name);
                plugin.AddFunction(CreateGrpcFunction(runner, operation, kernel.LoggerFactory));
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
    /// Registers SKFunction for a gRPC operation.
    /// </summary>
    /// <param name="runner">gRPC operation runner.</param>
    /// <param name="operation">The gRPC operation.</param>
    /// <param name="loggerFactory">The logger factory.</param>
    /// <returns>An instance of <see cref="SKFunctionFromPrompt"/> class.</returns>
    private static ISKFunction CreateGrpcFunction(
        GrpcOperationRunner runner,
        GrpcOperation operation,
        ILoggerFactory loggerFactory)
    {
        var operationParameters = operation.GetParameters();

        async Task<SKContext> ExecuteAsync(SKContext context, CancellationToken cancellationToken)
        {
            try
            {
                var arguments = new Dictionary<string, string>();

                //Extract function arguments from context
                foreach (var parameter in operationParameters)
                {
                    //A try to resolve argument parameter name.
                    if (context.Variables.TryGetValue(parameter.Name, out string? value))
                    {
                        arguments.Add(parameter.Name, value);
                        continue;
                    }

                    throw new KeyNotFoundException($"No variable found in context to use as an argument for the '{parameter.Name}' parameter of the '{operation.Name}' gRPC function.");
                }

                var result = await runner.RunAsync(operation, arguments, cancellationToken).ConfigureAwait(false);

                if (result != null)
                {
                    context.Variables.Update(result.ToString());
                }
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                loggerFactory.CreateLogger(typeof(KernelGrpcExtensions)).LogWarning(ex, "Something went wrong while rendering the gRPC function. Function: {0}. Error: {1}", operation.Name, ex.Message);
                throw;
            }

            return context;
        }

        return SKFunction.FromMethod(
            method: ExecuteAsync,
            parameters: operationParameters.ToList(),
            description: operation.Name,
            functionName: operation.Name,
            loggerFactory: loggerFactory);
    }

    #endregion
}
