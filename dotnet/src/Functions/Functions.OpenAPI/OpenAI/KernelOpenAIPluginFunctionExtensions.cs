// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.OpenAI;

/// <summary>
/// Provides extension methods for importing Open AI functions.
/// </summary>
public static class KernelOpenAIPluginFunctionExtensions
{
    /// <summary>
    /// Imports an Open AI function.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="filePath">The file path to the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportOpenAIPluginFunctionsAsync(
        this IKernel kernel,
        string pluginName,
        string filePath,
        OpenAIPluginFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName);

        var openAIManifest = await DocumentLoader.LoadDocumentFromFilePathAsync(
            filePath,
            kernel.LoggerFactory.CreateLogger(typeof(KernelOpenAIPluginFunctionExtensions)),
            cancellationToken).ConfigureAwait(false);

        return await ImportAsync(
            kernel,
            openAIManifest,
            pluginName,
            executionParameters,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Imports an Open AI function.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="uri">A local or remote URI referencing the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportOpenAIPluginFunctionsAsync(
        this IKernel kernel,
        string pluginName,
        Uri uri,
        OpenAIPluginFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName);

#pragma warning disable CA2000 // Dispose objects before losing scope. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
        var httpClient = HttpClientProvider.GetHttpClient(kernel.HttpHandlerFactory, executionParameters?.HttpClient, kernel.LoggerFactory);
#pragma warning restore CA2000

        var openAIManifest = await DocumentLoader.LoadDocumentFromUriAsync(
            uri,
            kernel.LoggerFactory.CreateLogger(typeof(KernelOpenAIPluginFunctionExtensions)),
            httpClient,
            null, // auth is not needed when loading the manifest
            executionParameters?.UserAgent,
            cancellationToken).ConfigureAwait(false);

        return await ImportAsync(
            kernel,
            openAIManifest,
            pluginName,
            executionParameters,
            cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Imports an Open AI function.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance.</param>
    /// <param name="pluginName">Plugin name.</param>
    /// <param name="stream">A stream representing the AI Plugin</param>
    /// <param name="executionParameters">Plugin execution parameters.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A collection of invocable functions</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportOpenAIPluginFunctionsAsync(
        this IKernel kernel,
        string pluginName,
        Stream stream,
        OpenAIPluginFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.ValidPluginName(pluginName);

        var openAIManifest = await DocumentLoader.LoadDocumentFromStreamAsync(stream).ConfigureAwait(false);

        return await ImportAsync(
            kernel,
            openAIManifest,
            pluginName,
            executionParameters,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    #region private

    private static async Task<IDictionary<string, ISKFunction>> ImportAsync(
        IKernel kernel,
        string openAIManifest,
        string pluginName,
        OpenAIPluginFunctionExecutionParameters? executionParameters = null,
        CancellationToken cancellationToken = default)
    {
        if (executionParameters?.AuthCallback is not null &&
            ParseOpenAIManifestForAuth(openAIManifest, out var openAIManifestAuth) &&
            openAIManifestAuth!.Type != OpenAIAuthenticationType.None)
        {
            var callback = executionParameters.AuthCallback;
            ((OpenApiPluginFunctionExecutionParameters)executionParameters).AuthCallback = async (request) =>
            {
                await callback(request, openAIManifestAuth).ConfigureAwait(false);
            };
        }

        return await kernel.ImportOpenApiPluginFunctionsAsync(
            pluginName,
            ParseOpenAIManifestForOpenApiSpecUrl(openAIManifest),
            executionParameters,
            cancellationToken).ConfigureAwait(false);
    }

    private static Uri ParseOpenAIManifestForOpenApiSpecUrl(string openAIManifest)
    {
        try
        {
            JsonNode? pluginJson = JsonNode.Parse(openAIManifest);

            string? apiType = pluginJson?["api"]?["type"]?.ToString();
            if (string.IsNullOrWhiteSpace(apiType) || apiType != "openapi")
            {
                throw new Exception("");
            }

            string? apiUrl = pluginJson?["api"]?["url"]?.ToString();
            if (string.IsNullOrWhiteSpace(apiUrl))
            {
                throw new Exception("");
            }

            return new Uri(apiUrl);
        }
        catch (System.UriFormatException)
        {
            throw new Exception("");
        }
        catch (System.Text.Json.JsonException)
        {
            throw new Exception("");
        }
    }

    private static bool ParseOpenAIManifestForAuth(string openAIManifest, out OpenAIManifestAuthentication? openAIManifestAuth)
    {
        try
        {
            JsonNode? pluginJson = JsonNode.Parse(openAIManifest);
            openAIManifestAuth = pluginJson?["auth"].Deserialize<OpenAIManifestAuthentication>();
            return openAIManifestAuth is not null;
        }
        catch (System.Text.Json.JsonException)
        {
            openAIManifestAuth = null;
            return false;
        }
    }

    #endregion
}
