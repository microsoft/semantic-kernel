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

namespace Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;
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
    /// <param name="executionParameters">Optional execution parameters for the plugin.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>The imported plugin.</returns>
    public static async Task<KernelPlugin> ImportPluginFromApiManifestAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        KernelPlugin plugin = await kernel.CreatePluginFromApiManifestAsync(pluginName, filePath, executionParameters, cancellationToken).ConfigureAwait(false);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Creates a kernel plugin from an API manifest file asynchronously.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="pluginName">The name of the plugin.</param>
    /// <param name="filePath">The file path of the API manifest.</param>
    /// <param name="executionParameters">Optional execution parameters for the API functions.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the created kernel plugin.</returns>
    public static async Task<KernelPlugin> CreatePluginFromApiManifestAsync(
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

        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"ApiManifest file not found: {filePath}");
        }

        var loggerFactory = kernel.LoggerFactory;
        var logger = loggerFactory.CreateLogger(typeof(ApiManifestKernelExtensions)) ?? NullLogger.Instance;
        string apiManifestFileJsonContents = await DocumentLoader.LoadDocumentFromFilePathAsync(filePath,
            logger,
            cancellationToken).ConfigureAwait(false);
        JsonDocument jsonDocument = JsonDocument.Parse(apiManifestFileJsonContents);

        ApiManifestDocument document = ApiManifestDocument.Load(jsonDocument.RootElement);

        var functions = new List<KernelFunction>();
        foreach (var apiDependency in document.ApiDependencies)
        {
            var apiName = apiDependency.Key;
            var apiDependencyDetails = apiDependency.Value;

            var apiDescriptionUrl = apiDependencyDetails.ApiDescriptionUrl;

            var openApiDocumentString = await DocumentLoader.LoadDocumentFromUriAsync(new Uri(apiDescriptionUrl),
                logger,
                httpClient,
                authCallback: null,
                executionParameters?.UserAgent,
                cancellationToken).ConfigureAwait(false);

            OpenApiDiagnostic diagnostic = new();
            var openApiDocument = new OpenApiStringReader(new()
            {
                BaseUrl = new(apiDescriptionUrl)
            }
            ).Read(openApiDocumentString, out diagnostic);

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

                requestUrls.Add(UriTemplate, new List<string>() { Method });
            }

            var predicate = OpenApiFilterService.CreatePredicate(null, null, requestUrls, openApiDocument);
            var filteredOpenApiDocument = OpenApiFilterService.CreateFilteredDocument(openApiDocument, predicate);

            var serverUrl = filteredOpenApiDocument.Servers.FirstOrDefault()?.Url;

            var runner = new RestApiOperationRunner(
                httpClient,
                executionParameters?.AuthCallback,
                executionParameters?.UserAgent,
                executionParameters?.EnableDynamicPayload ?? true,
                executionParameters?.EnablePayloadNamespacing ?? false);

            foreach (var path in filteredOpenApiDocument.Paths)
            {
                var operations = OpenApiDocumentParser.CreateRestApiOperations(serverUrl, path.Key, path.Value);
                foreach (RestApiOperation operation in operations)
                {
                    try
                    {
                        logger.LogTrace("Registering Rest function {0}.{1}", pluginName, operation.Id);
                        functions.Add(OpenApiKernelExtensions.CreateRestApiFunction(pluginName, runner, operation, executionParameters, new Uri(serverUrl), loggerFactory));
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

        return KernelPluginFactory.CreateFromFunctions(pluginName, null, functions);
    }
}
