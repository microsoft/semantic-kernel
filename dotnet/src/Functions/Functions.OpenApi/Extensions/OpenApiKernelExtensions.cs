// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Provides extension methods for importing plugins exposed as OpenAPI v3 endpoints.
/// </summary>
public static class OpenApiKernelExtensions
{
    // TODO: Revise XML comments

    /// <summary>
    /// Creates a plugin from an OpenAPI v3 endpoint and adds it to the kernel's plugins collection.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="filePath">The file path to the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<KernelPlugin> ImportPluginFromOpenApiAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        KernelPlugin plugin = await kernel.CreatePluginFromOpenApiAsync(pluginName, filePath, executionParameters, cancellationToken).ConfigureAwait(false);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Creates a plugin from an OpenAPI v3 endpoint and adds it to the kernel's plugins collection.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="uri">A local or remote URI referencing the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<KernelPlugin> ImportPluginFromOpenApiAsync(
        this Kernel kernel,
        string pluginName,
        Uri uri,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        KernelPlugin plugin = await kernel.CreatePluginFromOpenApiAsync(pluginName, uri, executionParameters, cancellationToken).ConfigureAwait(false);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Creates a plugin from an OpenAPI v3 endpoint and adds it to the kernel's plugins collection.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="stream">A stream representing the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<KernelPlugin> ImportPluginFromOpenApiAsync(
        this Kernel kernel,
        string pluginName,
        Stream stream,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        KernelPlugin plugin = await kernel.CreatePluginFromOpenApiAsync(pluginName, stream, executionParameters, cancellationToken).ConfigureAwait(false);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Creates a plugin from an OpenAPI v3 endpoint.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="filePath">The file path to the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<KernelPlugin> CreatePluginFromOpenApiAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName, kernel.Plugins);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(executionParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

        var openApiSpec = await DocumentLoader.LoadDocumentFromFilePathAsync(
            filePath,
            kernel.LoggerFactory.CreateLogger(typeof(OpenApiKernelExtensions)),
            cancellationToken).ConfigureAwait(false);

        return await CreateOpenApiPluginAsync(
            kernel,
            pluginName,
            executionParameters,
            httpClient,
            openApiSpec,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Creates a plugin from an OpenAPI v3 endpoint.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="uri">A local or remote URI referencing the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<KernelPlugin> CreatePluginFromOpenApiAsync(
        this Kernel kernel,
        string pluginName,
        Uri uri,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName, kernel.Plugins);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(executionParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

        var openApiSpec = await DocumentLoader.LoadDocumentFromUriAsync(
            uri,
            kernel.LoggerFactory.CreateLogger(typeof(OpenApiKernelExtensions)),
            httpClient,
            executionParameters?.AuthCallback,
            executionParameters?.UserAgent,
            cancellationToken).ConfigureAwait(false);

        return await CreateOpenApiPluginAsync(
            kernel,
            pluginName,
            executionParameters,
            httpClient,
            openApiSpec,
            uri,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Creates a plugin from an OpenAPI v3 endpoint.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="stream">A stream representing the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<KernelPlugin> CreatePluginFromOpenApiAsync(
        this Kernel kernel,
        string pluginName,
        Stream stream,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName, kernel.Plugins);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(executionParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

        var openApiSpec = await DocumentLoader.LoadDocumentFromStreamAsync(stream).ConfigureAwait(false);

        return await CreateOpenApiPluginAsync(
            kernel,
            pluginName,
            executionParameters,
            httpClient,
            openApiSpec,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    #region private

    private static async Task<KernelPlugin> CreateOpenApiPluginAsync(
        Kernel kernel,
        string pluginName,
        OpenApiFunctionExecutionParameters? executionParameters,
        HttpClient httpClient,
        string pluginJson,
        Uri? documentUri = null,
        CancellationToken cancellationToken = default)
    {
        using var documentStream = new MemoryStream(System.Text.Encoding.UTF8.GetBytes(pluginJson));

        ILoggerFactory loggerFactory = kernel.LoggerFactory;

        var parser = new OpenApiDocumentParser(loggerFactory);

        var operations = await parser.ParseAsync(
            documentStream,
            executionParameters?.IgnoreNonCompliantErrors ?? false,
            executionParameters?.OperationsToExclude,
            cancellationToken).ConfigureAwait(false);

        var runner = new RestApiOperationRunner(
            httpClient,
            executionParameters?.AuthCallback,
            executionParameters?.UserAgent,
            executionParameters?.EnableDynamicPayload ?? false,
            executionParameters?.EnablePayloadNamespacing ?? false);

        var functions = new List<KernelFunction>();
        ILogger logger = loggerFactory.CreateLogger(typeof(OpenApiKernelExtensions));
        foreach (var operation in operations)
        {
            try
            {
                logger.LogTrace("Registering Rest function {0}.{1}", pluginName, operation.Id);
                functions.Add(CreateRestApiFunction(pluginName, runner, operation, executionParameters, documentUri, loggerFactory));
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                //Logging the exception and keep registering other Rest functions
                logger.LogWarning(ex, "Something went wrong while rendering the Rest function. Function: {0}.{1}. Error: {2}",
                    pluginName, operation.Id, ex.Message);
            }
        }

        return KernelPluginFactory.CreateFromFunctions(pluginName, null, functions);
    }

    /// <summary>
    /// Registers KernelFunctionFactory for a REST API operation.
    /// </summary>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="runner">The REST API operation runner.</param>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="executionParameters">Function execution parameters.</param>
    /// <param name="documentUri">The URI of OpenAPI document.</param>
    /// <param name="loggerFactory">The logger factory.</param>
    /// <returns>An instance of <see cref="KernelFunctionFromPrompt"/> class.</returns>
    private static KernelFunction CreateRestApiFunction(
        string pluginName,
        RestApiOperationRunner runner,
        RestApiOperation operation,
        OpenApiFunctionExecutionParameters? executionParameters,
        Uri? documentUri = null,
        ILoggerFactory? loggerFactory = null)
    {
        IReadOnlyList<RestApiOperationParameter> restOperationParameters = operation.GetParameters(
            executionParameters?.EnableDynamicPayload ?? false,
            executionParameters?.EnablePayloadNamespacing ?? false
        );

        var logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(OpenApiKernelExtensions)) : NullLogger.Instance;

        async Task<RestApiOperationResponse> ExecuteAsync(KernelArguments variables, CancellationToken cancellationToken)
        {
            try
            {
                // Extract function arguments from context
                var arguments = new KernelArguments();
                foreach (var parameter in restOperationParameters)
                {
                    // A try to resolve argument by alternative parameter name
                    if (!string.IsNullOrEmpty(parameter.AlternativeName) &&
                        variables.TryGetValue(parameter.AlternativeName!, out object? value) &&
                        value is not null)
                    {
                        arguments.Add(parameter.Name, value);
                        continue;
                    }

                    // A try to resolve argument by original parameter name
                    if (variables.TryGetValue(parameter.Name, out value) &&
                        value is not null)
                    {
                        arguments.Add(parameter.Name, value);
                        continue;
                    }

                    if (parameter.IsRequired)
                    {
                        throw new KeyNotFoundException(
                            $"No variable found in context to use as an argument for the '{parameter.Name}' parameter of the '{pluginName}.{operation.Id}' Rest function.");
                    }
                }

                var options = new RestApiOperationRunOptions
                {
                    ServerUrlOverride = executionParameters?.ServerUrlOverride,
                    ApiHostUrl = documentUri is not null ? new Uri(documentUri.GetLeftPart(UriPartial.Authority)) : null
                };

                return await runner.RunAsync(operation, arguments, options, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                logger!.LogError(ex, "RestAPI function {Plugin}.{Name} execution failed with error {Error}", pluginName, operation.Id, ex.Message);
                throw;
            }
        }

        var parameters = restOperationParameters
            .Select(p => new KernelParameterMetadata(p.AlternativeName ?? p.Name)
            {
                Description = $"{p.Description ?? p.Name}",
                DefaultValue = p.DefaultValue ?? string.Empty,
                IsRequired = p.IsRequired,
                Schema = p.Schema ?? (p.Type is null ? null : KernelJsonSchema.Parse($"{{\"type\":\"{p.Type}\"}}")),
            })
            .ToList();

        var returnParameter = operation.GetDefaultReturnParameter();

        return KernelFunctionFactory.CreateFromMethod(
            method: ExecuteAsync,
            parameters: parameters,
            returnParameter: returnParameter,
            description: operation.Description,
            functionName: ConvertOperationIdToValidFunctionName(operation.Id, logger),
            loggerFactory: loggerFactory);
    }

    /// <summary>
    /// Converts operation id to valid SK Function name.
    /// A function name can contain only ASCII letters, digits, and underscores.
    /// </summary>
    /// <param name="operationId">The operation id.</param>
    /// <param name="logger">The logger.</param>
    /// <returns>Valid SK Function name.</returns>
    private static string ConvertOperationIdToValidFunctionName(string operationId, ILogger logger)
    {
        try
        {
            Verify.ValidFunctionName(operationId);
            return operationId;
        }
        catch (KernelException)
        {
        }

        // Tokenize operation id on forward and back slashes
        string[] tokens = operationId.Split('/', '\\');
        string result = string.Empty;

        foreach (string token in tokens)
        {
            // Removes all characters that are not ASCII letters, digits, and underscores.
            string formattedToken = s_removeInvalidCharsRegex.Replace(token, "");
            result += CultureInfo.CurrentCulture.TextInfo.ToTitleCase(formattedToken.ToLower(CultureInfo.CurrentCulture));
        }

        logger.LogInformation("Operation name \"{0}\" converted to \"{1}\" to comply with SK Function name requirements. Use \"{2}\" when invoking function.", operationId, result, result);

        return result;
    }

    /// <summary>
    /// Used to convert operationId to SK function names.
    /// </summary>
    private static readonly Regex s_removeInvalidCharsRegex = new("[^0-9A-Za-z_]");

    #endregion
}
