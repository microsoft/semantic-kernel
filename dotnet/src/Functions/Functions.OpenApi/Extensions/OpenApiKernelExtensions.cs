// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="Kernel"/> to create and import plugins from OpenAPI specifications.
/// </summary>
public static class OpenApiKernelExtensions
{
    /// <summary>
    /// Creates <see cref="KernelPlugin"/> from an OpenAPI specification and adds it to <see cref="Kernel.Plugins"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="filePath">The file path to the OpenAPI specification.</param>
    /// <param name="executionParameters">The OpenAPI specification parsing and function execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance that contains functions corresponding to the operations defined in the OpenAPI specification.</returns>
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
    /// Creates <see cref="KernelPlugin"/> from an OpenAPI specification and adds it to <see cref="Kernel.Plugins"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="uri">A URI referencing the OpenAPI specification.</param>
    /// <param name="executionParameters">The OpenAPI specification parsing and function execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance that contains functions corresponding to the operations defined in the OpenAPI specification.</returns>
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
    /// Creates <see cref="KernelPlugin"/> from an OpenAPI specification and adds it to <see cref="Kernel.Plugins"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="stream">A stream representing the OpenAPI specification.</param>
    /// <param name="executionParameters">The OpenAPI specification parsing and function execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance that contains functions corresponding to the operations defined in the OpenAPI specification.</returns>
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
    /// Creates <see cref="KernelPlugin"/> from an OpenAPI specification and adds it to <see cref="Kernel.Plugins"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="specification">The specification model.</param>
    /// <param name="executionParameters">The OpenAPI specification parsing and function execution parameters.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance that contains functions corresponding to the operations defined in the OpenAPI specification.</returns>
    public static KernelPlugin ImportPluginFromOpenApi(
        this Kernel kernel,
        string pluginName,
        RestApiSpecification specification,
        OpenApiFunctionExecutionParameters? executionParameters = null)
    {
        KernelPlugin plugin = kernel.CreatePluginFromOpenApi(pluginName, specification, executionParameters);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Creates <see cref="KernelPlugin"/> from an OpenAPI specification.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="filePath">The file path to the OpenAPI specification.</param>
    /// <param name="executionParameters">The OpenAPI specification parsing and function execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance that contains functions corresponding to the operations defined in the OpenAPI specification.</returns>
    public static async Task<KernelPlugin> CreatePluginFromOpenApiAsync(
        this Kernel kernel,
        string pluginName,
        string filePath,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        KernelVerify.ValidPluginName(pluginName, kernel.Plugins);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(executionParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

        ILoggerFactory loggerFactory = executionParameters?.LoggerFactory ?? kernel.LoggerFactory;

        var openApiSpec = await DocumentLoader.LoadDocumentFromFilePathAsync(
            filePath,
            loggerFactory.CreateLogger(typeof(OpenApiKernelExtensions)) ?? NullLogger.Instance,
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
    /// Creates <see cref="KernelPlugin"/> from an OpenAPI specification.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="uri">A URI referencing the OpenAPI specification.</param>
    /// <param name="executionParameters">The OpenAPI specification parsing and function execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance that contains functions corresponding to the operations defined in the OpenAPI specification.</returns>
    public static async Task<KernelPlugin> CreatePluginFromOpenApiAsync(
        this Kernel kernel,
        string pluginName,
        Uri uri,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        KernelVerify.ValidPluginName(pluginName, kernel.Plugins);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(executionParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

        ILoggerFactory loggerFactory = executionParameters?.LoggerFactory ?? kernel.LoggerFactory;

        var openApiSpec = await DocumentLoader.LoadDocumentFromUriAsync(
            uri,
            loggerFactory.CreateLogger(typeof(OpenApiKernelExtensions)) ?? NullLogger.Instance,
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
    /// Creates <see cref="KernelPlugin"/> from an OpenAPI specification.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="stream">A stream representing the OpenAPI specification.</param>
    /// <param name="executionParameters">The OpenAPI specification parsing and function execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance that contains functions corresponding to the operations defined in the OpenAPI specification.</returns>
    public static async Task<KernelPlugin> CreatePluginFromOpenApiAsync(
        this Kernel kernel,
        string pluginName,
        Stream stream,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        KernelVerify.ValidPluginName(pluginName, kernel.Plugins);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(executionParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

        var openApiSpec = await DocumentLoader.LoadDocumentFromStreamAsync(stream, cancellationToken).ConfigureAwait(false);

        return await CreateOpenApiPluginAsync(
            kernel,
            pluginName,
            executionParameters,
            httpClient,
            openApiSpec,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Creates <see cref="KernelPlugin"/> from an OpenAPI specification.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="specification">The specification model.</param>
    /// <param name="executionParameters">The OpenAPI specification parsing and function execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance that contains functions corresponding to the operations defined in the OpenAPI specification.</returns>
    public static KernelPlugin CreatePluginFromOpenApi(
        this Kernel kernel,
        string pluginName,
        RestApiSpecification specification,
        OpenApiFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        KernelVerify.ValidPluginName(pluginName, kernel.Plugins);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(executionParameters?.HttpClient ?? kernel.Services.GetService<HttpClient>());
#pragma warning restore CA2000

        return OpenApiKernelPluginFactory.CreateOpenApiPlugin(
            pluginName: pluginName,
            executionParameters: executionParameters,
            httpClient: httpClient,
            specification: specification,
            loggerFactory: kernel.LoggerFactory);
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
        ILoggerFactory loggerFactory = executionParameters?.LoggerFactory ?? kernel.LoggerFactory;

        return await OpenApiKernelPluginFactory.CreateOpenApiPluginAsync(pluginName, executionParameters, httpClient, pluginJson, documentUri, loggerFactory, cancellationToken).ConfigureAwait(false); ;
    }

    #endregion
}
