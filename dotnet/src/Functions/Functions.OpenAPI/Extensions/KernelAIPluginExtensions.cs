// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Functions.OpenAPI.OpenApi;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;

/// <summary>
/// Provides extension methods for importing AI plugins exposed as OpenAPI v3 endpoints or through OpenAI's ChatGPT format.
/// </summary>
public static class KernelAIPluginExtensions
{
    [Obsolete("Methods and classes which includes Skill in the name have been renamed to use Plugin. Use Kernel.ImportPluginFunctionsAsync instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public static async Task<IDictionary<string, ISKFunction>> ImportAIPluginAsync(
        this IKernel kernel,
        string pluginName,
        string filePath,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        return await kernel.ImportPluginFunctionsAsync(pluginName, filePath, executionParameters, cancellationToken).ConfigureAwait(false);
    }
#pragma warning restore CS1591

    /// <summary>
    /// Imports an AI plugin that is exposed as an OpenAPI v3 endpoint or through OpenAI's ChatGPT format.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="filePath">The file path to the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportPluginFunctionsAsync(
        this IKernel kernel,
        string pluginName,
        string filePath,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(kernel.HttpHandlerFactory, executionParameters?.HttpClient, kernel.LoggerFactory);
#pragma warning restore CA2000

        var pluginContents = await LoadDocumentFromFilePathAsync(
            kernel,
            filePath,
            executionParameters,
            httpClient,
            cancellationToken).ConfigureAwait(false);

        return await CompleteImportAsync(
            kernel,
            pluginContents,
            pluginName,
            httpClient,
            executionParameters,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    [Obsolete("Methods and classes which includes Skill in the name have been renamed to use Plugin. Use Kernel.ImportPluginFunctionsAsync instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public static async Task<IDictionary<string, ISKFunction>> ImportAIPluginAsync(
        this IKernel kernel,
        string pluginName,
        Uri uri,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        return await kernel.ImportPluginFunctionsAsync(pluginName, uri, executionParameters, cancellationToken).ConfigureAwait(false);
    }
#pragma warning restore CS1591

    /// <summary>
    /// Imports an AI plugin that is exposed as an OpenAPI v3 endpoint or through OpenAI's ChatGPT format.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="uri">A local or remote URI referencing the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportPluginFunctionsAsync(
        this IKernel kernel,
        string pluginName,
        Uri uri,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(kernel.HttpHandlerFactory, executionParameters?.HttpClient, kernel.LoggerFactory);
#pragma warning restore CA2000

        var pluginContents = await LoadDocumentFromUriAsync(
            kernel,
            uri,
            executionParameters,
            httpClient,
            cancellationToken).ConfigureAwait(false);

        return await CompleteImportAsync(
            kernel,
            pluginContents,
            pluginName,
            httpClient,
            executionParameters,
            uri,
            cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Imports an AI plugin that is exposed as an OpenAPI v3 endpoint or through OpenAI's ChatGPT format.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="stream">A stream representing the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportPluginFunctionsAsync(
        this IKernel kernel,
        string pluginName,
        Stream stream,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(kernel.HttpHandlerFactory, executionParameters?.HttpClient, kernel.LoggerFactory);
#pragma warning restore CA2000

        var pluginContents = await LoadDocumentFromStreamAsync(kernel, stream).ConfigureAwait(false);

        return await CompleteImportAsync(
            kernel,
            pluginContents,
            pluginName,
            httpClient,
            executionParameters,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    #region private

    private static async Task<IDictionary<string, ISKFunction>> CompleteImportAsync(
        IKernel kernel,
        string pluginContents,
        string pluginName,
        HttpClient httpClient,
        OpenApiFunctionExecutionParameters? executionParameters,
        Uri? documentUri = null,
        CancellationToken cancellationToken = default)
    {
        if (TryParseAIPluginForUrl(pluginContents, out var openApiUrl))
        {
            return await kernel
                .ImportPluginFunctionsAsync(
                    pluginName,
                    new Uri(openApiUrl),
                    executionParameters,
                    cancellationToken: cancellationToken)
                .ConfigureAwait(false);
        }

        return await LoadPluginAsync(
            kernel,
            pluginName,
            executionParameters,
            httpClient,
            pluginContents,
            documentUri,
            cancellationToken).ConfigureAwait(false);
    }

    private static async Task<IDictionary<string, ISKFunction>> LoadPluginAsync(
        IKernel kernel,
        string pluginName,
        OpenApiFunctionExecutionParameters? executionParameters,
        HttpClient httpClient,
        string pluginJson,
        Uri? documentUri = null,
        CancellationToken cancellationToken = default)
    {
        var parser = new OpenApiDocumentParser(kernel.LoggerFactory);

        using (var documentStream = new MemoryStream(System.Text.Encoding.UTF8.GetBytes(pluginJson)))
        {
            var operations = await parser.ParseAsync(documentStream, executionParameters?.IgnoreNonCompliantErrors ?? false, cancellationToken).ConfigureAwait(false);

            var runner = new RestApiOperationRunner(
                httpClient,
                executionParameters?.AuthCallback,
                executionParameters?.UserAgent,
                executionParameters?.EnableDynamicPayload ?? false,
                executionParameters?.EnablePayloadNamespacing ?? false);

            var plugin = new Dictionary<string, ISKFunction>();

            ILogger logger = kernel.LoggerFactory.CreateLogger(typeof(KernelAIPluginExtensions));
            foreach (var operation in operations)
            {
                try
                {
                    logger.LogTrace("Registering Rest function {0}.{1}", pluginName, operation.Id);
                    var function = kernel.RegisterRestApiFunction(pluginName, runner, operation, executionParameters, documentUri, cancellationToken);
                    plugin[function.Name] = function;
                }
                catch (Exception ex) when (!ex.IsCriticalException())
                {
                    //Logging the exception and keep registering other Rest functions
                    logger.LogWarning(ex, "Something went wrong while rendering the Rest function. Function: {0}.{1}. Error: {2}",
                        pluginName, operation.Id, ex.Message);
                }
            }

            return plugin;
        }
    }

    private static async Task<string> LoadDocumentFromUriAsync(
        IKernel kernel,
        Uri uri,
        OpenApiFunctionExecutionParameters? executionParameters,
        HttpClient httpClient,
        CancellationToken cancellationToken)
    {
        using var requestMessage = new HttpRequestMessage(HttpMethod.Get, uri.ToString());

        if (!string.IsNullOrEmpty(executionParameters?.UserAgent))
        {
            requestMessage.Headers.UserAgent.Add(ProductInfoHeaderValue.Parse(executionParameters!.UserAgent));
        }

        using var response = await httpClient.SendWithSuccessCheckAsync(requestMessage, cancellationToken).ConfigureAwait(false);

        return await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);
    }

    private static async Task<string> LoadDocumentFromFilePathAsync(
        IKernel kernel,
        string filePath,
        OpenApiFunctionExecutionParameters? executionParameters,
        HttpClient httpClient,
        CancellationToken cancellationToken)
    {
        var pluginJson = string.Empty;

        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"Invalid URI. The specified path '{filePath}' does not exist.");
        }

        kernel.LoggerFactory.CreateLogger(typeof(KernelAIPluginExtensions)).LogTrace("Importing AI Plugin from {0}", filePath);

        using (var sr = File.OpenText(filePath))
        {
            return await sr.ReadToEndAsync().ConfigureAwait(false); //must await here to avoid stream reader being disposed before the string is read
        }
    }

    private static async Task<string> LoadDocumentFromStreamAsync(
        IKernel kernel,
        Stream stream)
    {
        using StreamReader reader = new(stream);
        return await reader.ReadToEndAsync().ConfigureAwait(false);
    }

    private static bool TryParseAIPluginForUrl(string gptPluginJson, out string? openApiUrl)
    {
        try
        {
            JsonNode? gptPlugin = JsonNode.Parse(gptPluginJson);

            string? apiType = gptPlugin?["api"]?["type"]?.ToString();

            if (string.IsNullOrWhiteSpace(apiType) || apiType != "openapi")
            {
                openApiUrl = null;

                return false;
            }

            openApiUrl = gptPlugin?["api"]?["url"]?.ToString();

            if (string.IsNullOrWhiteSpace(openApiUrl))
            {
                return false;
            }

            return true;
        }
        catch (System.Text.Json.JsonException)
        {
            openApiUrl = null;

            return false;
        }
    }

    /// <summary>
    /// Registers SKFunction for a REST API operation.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="runner">The REST API operation runner.</param>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="executionParameters">Function execution parameters.</param>
    /// <param name="documentUri">The URI of OpenApi document.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>An instance of <see cref="SKFunction"/> class.</returns>
    private static ISKFunction RegisterRestApiFunction(
        this IKernel kernel,
        string pluginName,
        RestApiOperationRunner runner,
        RestApiOperation operation,
        OpenApiFunctionExecutionParameters? executionParameters,
        Uri? documentUri = null,
        CancellationToken cancellationToken = default)
    {
        var restOperationParameters = operation.GetParameters(
            executionParameters?.ServerUrlOverride,
            executionParameters?.EnableDynamicPayload ?? false,
            executionParameters?.EnablePayloadNamespacing ?? false,
            documentUri
        );

        var logger = kernel.LoggerFactory is not null ? kernel.LoggerFactory.CreateLogger(typeof(KernelAIPluginExtensions)) : NullLogger.Instance;

        async Task<RestApiOperationResponse> ExecuteAsync(SKContext context)
        {
            try
            {
                // Extract function arguments from context
                var arguments = new Dictionary<string, string>();
                foreach (var parameter in restOperationParameters)
                {
                    // A try to resolve argument by alternative parameter name
                    if (!string.IsNullOrEmpty(parameter.AlternativeName) && context.Variables.TryGetValue(parameter.AlternativeName!, out string? value))
                    {
                        arguments.Add(parameter.Name, value);
                        continue;
                    }

                    // A try to resolve argument by original parameter name
                    if (context.Variables.TryGetValue(parameter.Name, out value))
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
                logger.LogError(ex, "RestAPI function {Plugin}.{Name} execution failed with error {Error}", pluginName, operation.Id, ex.Message);
                throw;
            }
        }

        var parameters = restOperationParameters
            .Select(p => new ParameterView(p.AlternativeName ?? p.Name)
            {
                Description = $"{p.Description ?? p.Name}{(p.IsRequired ? " (required)" : string.Empty)}",
                DefaultValue = p.DefaultValue ?? string.Empty,
                Type = string.IsNullOrEmpty(p.Type) ? null : new ParameterViewType(p.Type),
                IsRequired = p.IsRequired,
            })
            .ToList();

        var function = SKFunction.FromNativeFunction(
            nativeFunction: ExecuteAsync,
            parameters: parameters,
            description: operation.Description,
            pluginName: pluginName,
            functionName: ConvertOperationIdToValidFunctionName(operation.Id, logger),
            loggerFactory: kernel.LoggerFactory);

        return kernel.RegisterCustomFunction(function);
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
        catch (SKException)
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
