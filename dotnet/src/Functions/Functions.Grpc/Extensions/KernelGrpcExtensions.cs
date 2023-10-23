// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.Grpc.Model;
using Microsoft.SemanticKernel.Functions.Grpc.Protobuf;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Functions.Grpc.Extensions;

/// <summary>
/// <see cref="IKernel"/> extensions methods for gRPC functionality.
/// </summary>
public static class KernelGrpcExtensions
{
    /// <summary>
    /// Imports gRPC document from a directory.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="parentDirectory">Directory containing the plugin directory.</param>
    /// <param name="pluginDirectoryName">Name of the directory containing the selected plugin.</param>
    /// <param name="httpClient">HttpClient to use for sending requests.</param>
    /// <returns>A list of all the semantic functions representing the plugin.</returns>
    public static IDictionary<string, ISKFunction> ImportGrpcFunctionsFromDirectory(
        this IKernel kernel,
        string parentDirectory,
        string pluginDirectoryName,
        HttpClient? httpClient = null)
    {
        const string ProtoFile = "grpc.proto";

        Verify.ValidPluginName(pluginDirectoryName);

        var pluginDir = Path.Combine(parentDirectory, pluginDirectoryName);
        Verify.DirectoryExists(pluginDir);

        var filePath = Path.Combine(pluginDir, ProtoFile);
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"No .proto document for the specified path - {filePath} is found.");
        }

        kernel.LoggerFactory.CreateLogger(typeof(KernelGrpcExtensions)).LogTrace("Registering gRPC functions from {0} .proto document", filePath);

        using var stream = File.OpenRead(filePath);

        return kernel.RegisterGrpcFunctions(stream, pluginDirectoryName, httpClient);
    }

    /// <summary>
    /// Imports gRPC document from a file.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginName">Name of the plugin to register.</param>
    /// <param name="filePath">File path to .proto document.</param>
    /// <param name="httpClient">HttpClient to use for sending requests.</param>
    /// <returns>A list of all the semantic functions representing the plugin.</returns>
    public static IDictionary<string, ISKFunction> ImportGrpcFunctionsFromFile(
        this IKernel kernel,
        string pluginName,
        string filePath,
        HttpClient? httpClient = null)
    {
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"No .proto document for the specified path - {filePath} is found.");
        }

        kernel.LoggerFactory.CreateLogger(typeof(KernelGrpcExtensions)).LogTrace("Registering gRPC functions from {0} .proto document", filePath);

        using var stream = File.OpenRead(filePath);

        return kernel.RegisterGrpcFunctions(stream, pluginName, httpClient);
    }

    /// <summary>
    /// Registers an gRPC plugin.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="documentStream">.proto document stream.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="httpClient">HttpClient to use for sending requests.</param>
    /// <returns>A list of all the semantic functions representing the plugin.</returns>
    public static IDictionary<string, ISKFunction> RegisterGrpcFunctions(
        this IKernel kernel,
        Stream documentStream,
        string pluginName,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName);

        // Parse
        var parser = new ProtoDocumentParser();

        var operations = parser.Parse(documentStream, pluginName);

        var plugin = new Dictionary<string, ISKFunction>();

        var client = HttpClientProvider.GetHttpClient(kernel.HttpHandlerFactory, httpClient, kernel.LoggerFactory);

        var runner = new GrpcOperationRunner(client);

        ILogger logger = kernel.LoggerFactory.CreateLogger(typeof(KernelGrpcExtensions));
        foreach (var operation in operations)
        {
            try
            {
                logger.LogTrace("Registering gRPC function {0}.{1}", pluginName, operation.Name);
                var function = kernel.RegisterGrpcFunction(runner, pluginName, operation);
                plugin[function.Name] = function;
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
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="runner">gRPC operation runner.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="operation">The gRPC operation.</param>
    /// <returns>An instance of <see cref="SKFunction"/> class.</returns>
    private static ISKFunction RegisterGrpcFunction(
        this IKernel kernel,
        GrpcOperationRunner runner,
        string pluginName,
        GrpcOperation operation)
    {
        var operationParameters = operation.GetParameters();

        async Task<SKContext> ExecuteAsync(SKContext context)
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

                    throw new KeyNotFoundException($"No variable found in context to use as an argument for the '{parameter.Name}' parameter of the '{pluginName}.{operation.Name}' gRPC function.");
                }

                //SKFunction should be extended to pass cancellation token for delegateFunction calls.
                var result = await runner.RunAsync(operation, arguments, CancellationToken.None).ConfigureAwait(false);

                if (result != null)
                {
                    context.Variables.Update(result.ToString());
                }
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                kernel.LoggerFactory.CreateLogger(typeof(KernelGrpcExtensions)).LogWarning(ex, "Something went wrong while rendering the gRPC function. Function: {0}.{1}. Error: {2}", pluginName, operation.Name,
                    ex.Message);
                throw;
            }

            return context;
        }

        var function = SKFunction.FromNativeFunction(
            nativeFunction: ExecuteAsync,
            parameters: operationParameters.ToList(),
            description: operation.Name,
            pluginName: pluginName,
            functionName: operation.Name,
            loggerFactory: kernel.LoggerFactory);

        return kernel.RegisterCustomFunction(function);
    }

    #endregion

    #region obsolete

    [Obsolete("Methods and classes which includes Skill in the name have been renamed to use Plugin. Use Kernel.ImportGrpcFunctionsFromDirectory instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public static IDictionary<string, ISKFunction> ImportGrpcSkillFromDirectory(
        this IKernel kernel,
        string parentDirectory,
        string skillDirectoryName,
        HttpClient? httpClient = null)
    {
        return kernel.ImportGrpcFunctionsFromDirectory(parentDirectory, skillDirectoryName, httpClient);
    }
#pragma warning restore CS1591

    [Obsolete("Methods and classes which includes Skill in the name have been renamed to use Plugin. Use Kernel.ImportGrpcFunctionsFromFile instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public static IDictionary<string, ISKFunction> ImportGrpcSkillFromFile(
        this IKernel kernel,
        string skillName,
        string filePath,
        HttpClient? httpClient = null)
    {
        return kernel.ImportGrpcFunctionsFromFile(skillName, filePath, httpClient);
    }
#pragma warning restore CS1591

    [Obsolete("Methods and classes which includes Skill in the name have been renamed to use Plugin. Use Kernel.RegisterGrpcFunctions instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public static IDictionary<string, ISKFunction> RegisterGrpcSkill(
        this IKernel kernel,
        Stream documentStream,
        string skillName,
        HttpClient? httpClient = null)
    {
        return kernel.RegisterGrpcFunctions(documentStream, skillName, httpClient);
    }
#pragma warning restore CS1591

    #endregion
}
