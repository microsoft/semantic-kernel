// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.OpenApi.Readers;
using Microsoft.OpenApi.Services;
using Microsoft.Plugins.Manifest;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;

namespace Microsoft.SemanticKernel;
/// <summary>
/// Provides extension methods for the <see cref="Kernel"/> class related to OpenAPI functionality.
/// </summary>
public static class CopilotAgentPluginKernelExtensions
{
    /// <summary>
    /// Imports a plugin from an Copilot Agent Plugin asynchronously.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="pluginName">The name of the plugin.</param>
    /// <param name="filePath">The file path of the Copilot Agent Plugin.</param>
    /// <param name="pluginParameters">Optional parameters for the plugin setup.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>The imported plugin.</returns>
    public static async Task<KernelPlugin> ImportPluginFromCopilotAgentPluginAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        CopilotAgentPluginParameters? pluginParameters = null,
        CancellationToken cancellationToken = default)
    {
        KernelPlugin plugin = await kernel.CreatePluginFromCopilotAgentPluginAsync(pluginName, filePath, pluginParameters, cancellationToken).ConfigureAwait(false);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Creates a kernel plugin from an Copilot Agent Plugin file asynchronously.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="pluginName">The name of the plugin.</param>
    /// <param name="filePath">The file path of the Copilot Agent Plugin.</param>
    /// <param name="pluginParameters">Optional parameters for the plugin setup.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the created kernel plugin.</returns>
    public static async Task<KernelPlugin> CreatePluginFromCopilotAgentPluginAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        CopilotAgentPluginParameters? pluginParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        KernelVerify.ValidPluginName(pluginName, kernel.Plugins);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(pluginParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"CopilotAgent file not found: {filePath}");
        }

        var loggerFactory = kernel.LoggerFactory;
        var logger = loggerFactory.CreateLogger(typeof(CopilotAgentPluginKernelExtensions)) ?? NullLogger.Instance;
        using var CopilotAgentFileJsonContents = DocumentLoader.LoadDocumentFromFilePathAsStream(filePath,
            logger);

        var results = await PluginManifestDocument.LoadAsync(CopilotAgentFileJsonContents, new ReaderOptions
        {
            ValidationRules = [] // Disable validation rules
        }).ConfigureAwait(false);

        if (!results.IsValid)
        {
            var messages = results.Problems.Select(static p => p.Message).Aggregate(static (a, b) => $"{a}, {b}");
            throw new InvalidOperationException($"Error loading the manifest: {messages}");
        }

        var document = results.Document;
        var openAPIRuntimes = document?.Runtimes?.Where(runtime => runtime.Type == RuntimeType.OpenApi).ToList();
        if (openAPIRuntimes is null || openAPIRuntimes.Count == 0)
        {
            throw new InvalidOperationException("No OpenAPI runtimes found in the manifest.");
        }

        var functions = new List<KernelFunction>();
        var documentWalker = new OpenApiWalker(new OperationIdNormalizationOpenApiVisitor());
        foreach (var runtime in openAPIRuntimes)
        {
            var manifestFunctions = document?.Functions?.Where(f => runtime.RunForFunctions.Contains(f.Name)).ToList();
            if (manifestFunctions is null || manifestFunctions.Count == 0)
            {
                logger.LogWarning("No functions found in the runtime object.");
                continue;
            }

            var openApiRuntime = runtime as OpenApiRuntime;
            var apiDescriptionUrl = openApiRuntime?.Spec?.Url ?? string.Empty;
            if (apiDescriptionUrl.Length == 0)
            {
                logger.LogWarning("No API description URL found in the runtime object.");
                continue;
            }

            var (parsedDescriptionUrl, isOnlineDescription) = Uri.TryCreate(apiDescriptionUrl, UriKind.Absolute, out var result) ?
                (result, true) :
                (new Uri(Path.Combine(Path.GetDirectoryName(filePath) ?? string.Empty, apiDescriptionUrl)), false);

            using var openApiDocumentStream = isOnlineDescription ?
                await DocumentLoader.LoadDocumentFromUriAsStreamAsync(parsedDescriptionUrl,
                    logger,
                    httpClient,
                    authCallback: null,
                    pluginParameters?.UserAgent,
                    cancellationToken).ConfigureAwait(false) :
                DocumentLoader.LoadDocumentFromFilePathAsStream(parsedDescriptionUrl.LocalPath,
                    logger);

            var documentReadResult = await new OpenApiStreamReader(new()
            {
                BaseUrl = parsedDescriptionUrl
            }
            ).ReadAsync(openApiDocumentStream, cancellationToken).ConfigureAwait(false);
            var openApiDocument = documentReadResult.OpenApiDocument;
            var openApiDiagnostic = documentReadResult.OpenApiDiagnostic;

            documentWalker.Walk(openApiDocument);

            var predicate = OpenApiFilterService.CreatePredicate(string.Join(",", manifestFunctions.Select(static f => f.Name)), null, null, openApiDocument);
            var filteredOpenApiDocument = OpenApiFilterService.CreateFilteredDocument(openApiDocument, predicate);

            var server = filteredOpenApiDocument.Servers.FirstOrDefault();
            if (server?.Url is null)
            {
                logger.LogWarning("Server URI not found. Plugin: {0}", pluginName);
                continue;
            }

            var openApiFunctionExecutionParameters = pluginParameters?.FunctionExecutionParameters?.TryGetValue(server.Url, out var parameters) == true
                ? parameters
                : new OpenApiFunctionExecutionParameters()
                {
                    EnableDynamicPayload = false,
                    EnablePayloadNamespacing = true,
                };

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
            var operationRunnerHttpClient = HttpClientProvider.GetHttpClient(openApiFunctionExecutionParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000
            static IDictionary<string, string>? CopilotAgentPluginHeadersFactory(RestApiOperation operation, IDictionary<string, object?> arguments, RestApiOperationRunOptions? options)
            {
                var graphAllowedHosts = new[]
                {
                    "graph.microsoft.com",
                    "graph.microsoft.us",
                    "dod-graph.microsoft.us",
                    "graph.microsoft.de",
                    "microsoftgraph.chinacloudapi.cn",
                    "canary.graph.microsoft.com",
                    "graph.microsoft-ppe.com"
                };
                if (options?.ApiHostUrl?.Host is not { } hostString || !graphAllowedHosts.Contains(hostString))
                {
                    return null;
                }
                string frameworkDescription = RuntimeInformation.FrameworkDescription;
                string osDescription = RuntimeInformation.OSDescription;
                string copilotAgentPluginVersion = HttpHeaderConstant.Values.GetAssemblyVersion(typeof(CopilotAgentPluginKernelExtensions));
                var defaultHeaders = new Dictionary<string, string>
                {
                    // TODO: version and format updates
                    ["SdkVersion"] = $"copilot-agent-plugins/{copilotAgentPluginVersion}, (runtimeEnvironment={frameworkDescription}; hostOS={osDescription})",
                    ["client-request-id"] = Guid.NewGuid().ToString()
                };

                var currentHeaders = operation.BuildHeaders(arguments);
                var finalHeaders = defaultHeaders.Concat(currentHeaders).ToDictionary(k => k.Key, v => v.Value);
                return finalHeaders;
            }

            var runner = new RestApiOperationRunner(
                operationRunnerHttpClient,
                openApiFunctionExecutionParameters?.AuthCallback,
                openApiFunctionExecutionParameters?.UserAgent,
                openApiFunctionExecutionParameters?.EnableDynamicPayload ?? false,
                openApiFunctionExecutionParameters?.EnablePayloadNamespacing ?? true,
                headersFactory: CopilotAgentPluginHeadersFactory);

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
                        TrimOperationDescriptions(operation);
                        functions.Add(OpenApiKernelPluginFactory.CreateRestApiFunction(pluginName, runner, info, security, operation, openApiFunctionExecutionParameters, new Uri(server.Url), loggerFactory));
                    }
                    catch (Exception ex) when (!ex.IsCriticalException())
                    {
                        // Logging the exception and keep registering other Rest functions
                        logger.LogWarning(ex, "Something went wrong while rendering the Rest function. Function: {0}.{1}. Error: {2}",
                            pluginName, operation.Id, ex.Message);
                    }
                }
            }
        }
        return KernelPluginFactory.CreateFromFunctions(pluginName, null, functions);
    }

    #region private
    private const int MaximumDescription = 1000;

    /// <summary>
    /// Trims the operation descriptions to a maximum length.
    /// </summary>
    private static void TrimOperationDescriptions(RestApiOperation operation)
    {
        // Limit the description
        if (operation.Description?.Length > MaximumDescription)
        {
            operation.Description = operation.Description.Substring(0, MaximumDescription);
        }
    }
    #endregion
}
