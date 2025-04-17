// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.OpenApi.ApiManifest;
using Microsoft.OpenApi.Readers;
using Microsoft.OpenApi.Services;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;

namespace Microsoft.SemanticKernel;
/// <summary>
/// Provides extension methods for the <see cref="Kernel"/> class related to OpenAPI functionality.
/// </summary>
public static class ApiManifestKernelExtensions
{
    /// <summary>
    /// Imports a plugin from an API manifest asynchronously.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="pluginName">The name of the plugin.</param>
    /// <param name="filePath">The file path of the API manifest.</param>
    /// <param name="pluginParameters">Optional parameters for the plugin setup.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>The imported plugin.</returns>
    public static async Task<KernelPlugin> ImportPluginFromApiManifestAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        ApiManifestPluginParameters? pluginParameters = null,
        CancellationToken cancellationToken = default)
        => await kernel.ImportPluginFromApiManifestAsync(pluginName, filePath, null, pluginParameters, cancellationToken).ConfigureAwait(false);

    /// <summary>
    /// Imports a plugin from an API manifest asynchronously.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="pluginName">The name of the plugin.</param>
    /// <param name="filePath">The file path of the API manifest.</param>
    /// <param name="description">The description of the plugin.</param>
    /// <param name="pluginParameters">Optional parameters for the plugin setup.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>The imported plugin.</returns>
    public static async Task<KernelPlugin> ImportPluginFromApiManifestAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        string? description,
        ApiManifestPluginParameters? pluginParameters = null,
        CancellationToken cancellationToken = default)
    {
        KernelPlugin plugin = await kernel.CreatePluginFromApiManifestAsync(pluginName, filePath, description, pluginParameters, cancellationToken).ConfigureAwait(false);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Creates a kernel plugin from an API manifest file asynchronously.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="pluginName">The name of the plugin.</param>
    /// <param name="filePath">The file path of the API manifest.</param>
    /// <param name="pluginParameters">Optional parameters for the plugin setup.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the created kernel plugin.</returns>
    public static async Task<KernelPlugin> CreatePluginFromApiManifestAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        ApiManifestPluginParameters? pluginParameters = null,
        CancellationToken cancellationToken = default)
        => await kernel.CreatePluginFromApiManifestAsync(pluginName, filePath, null, pluginParameters, cancellationToken).ConfigureAwait(false);

    /// <summary>
    /// Creates a kernel plugin from an API manifest file asynchronously.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="pluginName">The name of the plugin.</param>
    /// <param name="filePath">The file path of the API manifest.</param>
    /// <param name="description">The description of the plugin.</param>
    /// <param name="pluginParameters">Optional parameters for the plugin setup.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the created kernel plugin.</returns>
    public static async Task<KernelPlugin> CreatePluginFromApiManifestAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        string? description,
        ApiManifestPluginParameters? pluginParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName, kernel.Plugins);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(pluginParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"ApiManifest file not found: {filePath}");
        }

        var loggerFactory = kernel.LoggerFactory;
        var logger = loggerFactory.CreateLogger(typeof(ApiManifestKernelExtensions)) ?? NullLogger.Instance;
        using var apiManifestFileJsonContents = DocumentLoader.LoadDocumentFromFilePathAsStream(filePath,
            logger);
        JsonDocument jsonDocument = await JsonDocument.ParseAsync(apiManifestFileJsonContents, cancellationToken: cancellationToken).ConfigureAwait(false);

        ApiManifestDocument document = ApiManifestDocument.Load(jsonDocument.RootElement);

        var functions = new List<KernelFunction>();
        var documentWalker = new OpenApiWalker(new OperationIdNormalizationOpenApiVisitor());
        foreach (var apiDependency in document.ApiDependencies)
        {
            var apiName = apiDependency.Key;
            var apiDependencyDetails = apiDependency.Value;

            var apiDescriptionUrl = apiDependencyDetails.ApiDescriptionUrl;
            if (apiDescriptionUrl is null)
            {
                logger.LogWarning("ApiDescriptionUrl is missing for API dependency: {ApiName}", apiName);
                continue;
            }

            var (parsedDescriptionUrl, isOnlineDescription) = Uri.TryCreate(apiDescriptionUrl, UriKind.Absolute, out var result) ?
                (result, true) :
                (new Uri(Path.Combine(Path.GetDirectoryName(filePath) ?? string.Empty, apiDescriptionUrl)), false);

            using var openApiDocumentStream = isOnlineDescription ?
                await DocumentLoader.LoadDocumentFromUriAsStreamAsync(new Uri(apiDescriptionUrl),
                    logger,
                    httpClient,
                    authCallback: null,
                    pluginParameters?.UserAgent,
                    cancellationToken).ConfigureAwait(false) :
                DocumentLoader.LoadDocumentFromFilePathAsStream(parsedDescriptionUrl.LocalPath,
                    logger);

            var documentReadResult = await new OpenApiStreamReader(new()
            {
                BaseUrl = new(apiDescriptionUrl)
            }
            ).ReadAsync(openApiDocumentStream, cancellationToken).ConfigureAwait(false);
            var openApiDocument = documentReadResult.OpenApiDocument;
            var openApiDiagnostic = documentReadResult.OpenApiDiagnostic;

            documentWalker.Walk(openApiDocument);

            var requestUrls = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase);
            var pathMethodPairs = apiDependencyDetails.Requests.Select(request => (request.UriTemplate, request.Method?.ToUpperInvariant()));
            foreach (var (UriTemplate, Method) in pathMethodPairs)
            {
                if (UriTemplate is null || Method is null)
                {
                    continue;
                }

                if (requestUrls.TryGetValue(UriTemplate, out List<string>? value))
                {
                    value.Add(Method);
                    continue;
                }

                requestUrls.Add(UriTemplate, [Method]);
            }

            var predicate = OpenApiFilterService.CreatePredicate(null, null, requestUrls, openApiDocument);
            var filteredOpenApiDocument = OpenApiFilterService.CreateFilteredDocument(openApiDocument, predicate);

            var openApiFunctionExecutionParameters = pluginParameters?.FunctionExecutionParameters?.TryGetValue(apiName, out var parameters) == true
                ? parameters
                : new OpenApiFunctionExecutionParameters()
                {
                    EnableDynamicPayload = false,
                    EnablePayloadNamespacing = true,
                };

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
            var operationRunnerHttpClient = HttpClientProvider.GetHttpClient(openApiFunctionExecutionParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

            var runner = new RestApiOperationRunner(
                operationRunnerHttpClient,
                openApiFunctionExecutionParameters?.AuthCallback,
                openApiFunctionExecutionParameters?.UserAgent,
                openApiFunctionExecutionParameters?.EnableDynamicPayload ?? false,
                openApiFunctionExecutionParameters?.EnablePayloadNamespacing ?? false);

            var server = filteredOpenApiDocument.Servers.FirstOrDefault();
            if (server?.Url is null)
            {
                logger.LogWarning("Server URI not found. Plugin: {0}", pluginName);
                continue;
            }
            var info = OpenApiDocumentParser.ExtractRestApiInfo(filteredOpenApiDocument);
            var security = OpenApiDocumentParser.CreateRestApiOperationSecurityRequirements(filteredOpenApiDocument.SecurityRequirements);
            foreach (var path in filteredOpenApiDocument.Paths)
            {
                var operations = OpenApiDocumentParser.CreateRestApiOperations(filteredOpenApiDocument, path.Key, path.Value, null, logger);
                foreach (RestApiOperation operation in operations)
                {
                    try
                    {
                        logger.LogTrace("Registering Rest function {0}.{1}", pluginName, operation.Id);
                        functions.Add(OpenApiKernelPluginFactory.CreateRestApiFunction(pluginName, runner, info, security, operation, openApiFunctionExecutionParameters, new Uri(server.Url), loggerFactory));
                    }
                    catch (Exception ex) when (!ex.IsCriticalException())
                    {
                        //Logging the exception and keep registering other Rest functions
                        logger.LogWarning(ex, "Something went wrong while rendering the Rest function. Function: {0}.{1}. Error: {2}",
                            pluginName, operation.Id, ex.Message);
                    }
                }
            }
        }

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, functions);
    }
}
