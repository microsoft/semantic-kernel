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
using Microsoft.Plugins.Manifest;
using Microsoft.OpenApi.Readers;
using Microsoft.OpenApi.Services;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;
/// <summary>
/// Provides extension methods for the <see cref="Kernel"/> class related to OpenAPI functionality.
/// </summary>
public static class MicrosoftManifestKernelExtensions
{
    /// <summary>
    /// Imports a plugin from an Microsoft manifest asynchronously.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="pluginName">The name of the plugin.</param>
    /// <param name="filePath">The file path of the Microsoft manifest.</param>
    /// <param name="pluginParameters">Optional parameters for the plugin setup.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>The imported plugin.</returns>
    public static async Task<KernelPlugin> ImportPluginFromMicrosoftManifestAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        MicrosoftManifestPluginParameters? pluginParameters = null,
        CancellationToken cancellationToken = default)
    {
        KernelPlugin plugin = await kernel.CreatePluginFromMicrosoftManifestAsync(pluginName, filePath, pluginParameters, cancellationToken).ConfigureAwait(false);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Creates a kernel plugin from an Microsoft manifest file asynchronously.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="pluginName">The name of the plugin.</param>
    /// <param name="filePath">The file path of the Microsoft manifest.</param>
    /// <param name="pluginParameters">Optional parameters for the plugin setup.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the created kernel plugin.</returns>
    public static async Task<KernelPlugin> CreatePluginFromMicrosoftManifestAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        MicrosoftManifestPluginParameters? pluginParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName, kernel.Plugins);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(pluginParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"MicrosoftManifest file not found: {filePath}");
        }

        var loggerFactory = kernel.LoggerFactory;
        var logger = loggerFactory.CreateLogger(typeof(MicrosoftManifestKernelExtensions)) ?? NullLogger.Instance;
        string microsoftManifestFileJsonContents = await DocumentLoader.LoadDocumentFromFilePathAsync(filePath,
            logger,
            cancellationToken).ConfigureAwait(false);
        JsonDocument jsonDocument = JsonDocument.Parse(microsoftManifestFileJsonContents);

        var results = PluginManifestDocument.Load(jsonDocument.RootElement, new ReaderOptions
        {
            ValidationRules = new() // Disable validation rules
        });

        if (!results.IsValid)
        {
            var messages = results.Problems.Select(p => p.Message).Aggregate((a, b) => $"{a}, {b}");
            throw new InvalidOperationException($"Error loading the manifest: {messages}");
        }

        var document = results.Document;
        var openAPIRuntimes = document?.Runtimes?.Where(runtime => runtime.Type == RuntimeType.OpenApi).ToList();
        if (openAPIRuntimes is null || openAPIRuntimes.Count == 0)
        {
            throw new InvalidOperationException("No OpenAPI runtimes found in the manifest.");
        }

        var functions = new List<KernelFunction>();
        foreach (var runtime in openAPIRuntimes)
        {
            var manifestFunctions = document?.Functions?.Where(f => runtime.RunForFunctions.Contains(f.Name)).ToList();
            if (manifestFunctions is null || manifestFunctions.Count == 0)
            {
                throw new InvalidOperationException("No functions found in the manifest.");
            }

            var openApiRuntime = runtime as OpenApiRuntime;
            var apiDescriptionUrl = openApiRuntime?.Spec?.Url ?? string.Empty;
            if (apiDescriptionUrl.Length == 0)
            {
                throw new InvalidOperationException("OpenAPI spec URL is missing in the manifest.");
            }

            var openApiDocumentString = await DocumentLoader.LoadDocumentFromUriAsync(new Uri(apiDescriptionUrl),
                logger,
                httpClient,
                authCallback: null,
                pluginParameters?.UserAgent,
                cancellationToken).ConfigureAwait(false);

            OpenApiDiagnostic diagnostic = new();
            var openApiDocument = new OpenApiStringReader(new()
            {
                BaseUrl = new(apiDescriptionUrl)
            }
            ).Read(openApiDocumentString, out diagnostic);

            var predicate = OpenApiFilterService.CreatePredicate(string.Join(",", manifestFunctions.Select(f => f.Name)), null, null, openApiDocument);
            var filteredOpenApiDocument = OpenApiFilterService.CreateFilteredDocument(openApiDocument, predicate);

            var serverUrl = filteredOpenApiDocument.Servers.FirstOrDefault()?.Url;
            if (serverUrl is null)
            {
                throw new InvalidOperationException("No server URL found in the OpenAPI document.");
            }

            var openApiFunctionExecutionParameters = pluginParameters?.FunctionExecutionParameters?.ContainsKey(apiDescriptionUrl) == true
                ? pluginParameters.FunctionExecutionParameters[apiDescriptionUrl]
                : null;

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
            var operationRunnerHttpClient = HttpClientProvider.GetHttpClient(openApiFunctionExecutionParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

            var runner = new RestApiOperationRunner(
                operationRunnerHttpClient,
                openApiFunctionExecutionParameters?.AuthCallback,
                openApiFunctionExecutionParameters?.UserAgent,
                openApiFunctionExecutionParameters?.EnableDynamicPayload ?? true,
                openApiFunctionExecutionParameters?.EnablePayloadNamespacing ?? false);

            foreach (var path in filteredOpenApiDocument.Paths)
            {
                var operations = OpenApiDocumentParser.CreateRestApiOperations(serverUrl, path.Key, path.Value, null, logger);
                foreach (RestApiOperation operation in operations)
                {
                    try
                    {
                        logger.LogTrace("Registering Rest function {0}.{1}", pluginName, operation.Id);
                        functions.Add(OpenApiKernelExtensions.CreateRestApiFunction(pluginName, runner, operation, openApiFunctionExecutionParameters, new Uri(serverUrl), loggerFactory));
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
