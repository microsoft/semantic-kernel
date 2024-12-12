// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
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
        KernelPlugin plugin = await kernel.CreatePluginFromCopilotAgentPluginAsync(pluginName, filePath, pluginParameters, null, cancellationToken).ConfigureAwait(false);
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
    /// <param name="pluginPolicy">The operation policy to use for the plugin.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the created kernel plugin.</returns>
    public static async Task<KernelPlugin> CreatePluginFromCopilotAgentPluginAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        CopilotAgentPluginParameters? pluginParameters = null,
        CopilotAgentPluginPolicy? pluginPolicy = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName, kernel.Plugins);

        pluginPolicy ??= new CopilotAgentPluginPolicy();

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(pluginParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"CopilotAgent file not found: {filePath}");
        }

        var loggerFactory = kernel.LoggerFactory;
        var logger = loggerFactory.CreateLogger(typeof(CopilotAgentPluginKernelExtensions)) ?? NullLogger.Instance;

        var document = await pluginPolicy.LoadManifestAsync(filePath, logger, cancellationToken).ConfigureAwait(false);

        var openAPIRuntimes = document.Runtimes?.Where(runtime => runtime.Type == RuntimeType.OpenApi).ToList();
        if (openAPIRuntimes is null || openAPIRuntimes.Count == 0)
        {
            throw new InvalidOperationException("No OpenAPI runtimes found in the manifest.");
        }

        var functions = new List<KernelFunction>();

        foreach (var runtime in openAPIRuntimes)
        {
            var manifestFunctions = document?.Functions?.Where(f => runtime.RunForFunctions.Contains(f.Name)).ToList(); ;
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

            var filteredOpenApiDocument = await pluginPolicy.LoadNormalizeAndFilterOpenApiDocumentAsync(
                manifestFunctions,
                apiDescriptionUrl,
                filePath,
                logger,
                httpClient,
                pluginParameters?.UserAgent ?? string.Empty,
                cancellationToken).ConfigureAwait(false);

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
                    EnableDynamicPayload = true,
                    EnablePayloadNamespacing = true,
                    ParameterFilter = (RestApiParameterFilterContext context) => context.Parameter.Name == "@odata.type" ? null : context.Parameter,
                };

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
            var operationRunnerHttpClient = HttpClientProvider.GetHttpClient(openApiFunctionExecutionParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

            var runner = new RestApiOperationRunner(
                operationRunnerHttpClient,
                openApiFunctionExecutionParameters?.AuthCallback,
                openApiFunctionExecutionParameters?.UserAgent,
                openApiFunctionExecutionParameters?.EnableDynamicPayload ?? true,
                openApiFunctionExecutionParameters?.EnablePayloadNamespacing ?? true,
                pluginPolicy.ReadHttpResponseContent,
                pluginPolicy.CreateRestApiOperationUrl,
                pluginPolicy.CreateRestApiOperationHeaders,
                pluginPolicy.CreateRestApiOperationPayload);

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
                        functions.Add(pluginPolicy.CreateKernelFunction(pluginName, server, runner, info, security, operation, openApiFunctionExecutionParameters, new Uri(server.Url), loggerFactory));
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
