// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System;
using System.Threading.Tasks;
using Microsoft.Plugins.Manifest;
using Microsoft.Extensions.Logging;
using System.Threading;
using System.Collections.Generic;
using Microsoft.OpenApi.Models;
using Microsoft.OpenApi.Readers;
using Microsoft.OpenApi.Services;
using System.Net.Http;
using System.IO;

namespace Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;

/// <summary>
/// Represents a default policy for Copilot Agent plugin.
/// </summary>
public class CopilotAgentPluginPolicy
{
    private static readonly OpenApiWalker s_openApiWalker = new(new OperationIdNormalizationOpenApiVisitor());

    /// <summary>
    /// Loads the manifest asynchronously.
    /// </summary>
    /// <param name="filePath">The file path of the manifest.</param>
    /// <param name="logger">The logger.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The manifest document.</returns>
    protected internal virtual async Task<PluginManifestDocument> LoadManifestAsync(string filePath, ILogger logger, CancellationToken cancellationToken)
    {
        // Different aspects of the manifest loading can be customized here:
        // * Load the manifest from a different source
        // * Validate the manifest
        // * Transform the manifest

        using var CopilotAgentFileJsonContents = DocumentLoader.LoadDocumentFromFilePathAsStream(filePath, logger);

        var results = await PluginManifestDocument.LoadAsync(CopilotAgentFileJsonContents, new ReaderOptions
        {
            ValidationRules = [] // Disable validation rules
        }).ConfigureAwait(false);

        if (!results.IsValid)
        {
            var messages = results.Problems.Select(static p => p.Message).Aggregate(static (a, b) => $"{a}, {b}");
            throw new InvalidOperationException($"Error loading the manifest: {messages}");
        }

        return results.Document!;
    }

    /// <summary>
    /// Loads, normalizes, and filters the OpenAPI document.
    /// </summary>
    protected internal virtual async Task<OpenApiDocument> LoadNormalizeAndFilterOpenApiDocumentAsync(
        IReadOnlyList<Function> manifestFunctions,
#pragma warning disable CA1054 // URI-like parameters should not be strings
        string documentUrl,
#pragma warning restore CA1054 // URI-like parameters should not be strings
        string filePath,
        ILogger logger,
        HttpClient httpClient,
        string userAgent,
        CancellationToken cancellationToken)
    {
        // Different aspects of the OpenAPI document loading can be customized here:
        // * Load the document from a different source
        // * Normalize the document
        // * Filter the document operations

        var (parsedDescriptionUrl, isOnlineDescription) = Uri.TryCreate(documentUrl, UriKind.Absolute, out var result) ?
                (result, true) :
                (new Uri(Path.Combine(Path.GetDirectoryName(filePath) ?? string.Empty, documentUrl)), false);

        using var openApiDocumentStream = isOnlineDescription ?
            await DocumentLoader.LoadDocumentFromUriAsStreamAsync(parsedDescriptionUrl,
                logger,
                httpClient,
                authCallback: null,
                userAgent,
                cancellationToken).ConfigureAwait(false) :
            DocumentLoader.LoadDocumentFromFilePathAsStream(parsedDescriptionUrl.LocalPath,
                logger);

        var documentReadResult = await new OpenApiStreamReader(new()
        {
            BaseUrl = parsedDescriptionUrl
        }
        ).ReadAsync(openApiDocumentStream, cancellationToken).ConfigureAwait(false);

        var openApiDocument = documentReadResult.OpenApiDocument;

        s_openApiWalker.Walk(openApiDocument);

        var predicate = OpenApiFilterService.CreatePredicate(string.Join(",", manifestFunctions.Select(static f => f.Name)), null, null, openApiDocument);

        return OpenApiFilterService.CreateFilteredDocument(openApiDocument, predicate);
    }

    /// <summary>
    /// Creates a kernel function.
    /// </summary>
    protected internal virtual KernelFunction CreateKernelFunction(
        string pluginName,
        OpenApiServer server,
        RestApiOperationRunner runner,
        RestApiInfo info,
        IList<RestApiSecurityRequirement>? security,
        RestApiOperation operation,
        OpenApiFunctionExecutionParameters? executionParameters,
        Uri? documentUri = null,
        ILoggerFactory? loggerFactory = null)
    {
        // Various aspect of kernel function creation done by the CreateRestApiFunction method can customized here:
        // * Transform list of parameters advertised to an AI model - change parameters metadata, remove parameters, add new parameters, etc
        // * Intercept function invocation and transform arguments provided by the AI model or function result.
        // * Override function metadata - name, description, metadata, etc

        return OpenApiKernelPluginFactory.CreateRestApiFunction(pluginName, runner, info, security, operation, executionParameters, new Uri(server.Url), loggerFactory);
    }

    /// <summary>
    /// Creates a REST API operation URL.
    /// </summary>
    protected internal virtual Uri? CreateRestApiOperationUrl(RestApiOperation operation, IDictionary<string, object?> arguments, RestApiOperationRunOptions? options)
    {
        // The URL of the operation can be created here based on operation metadata, arguments, and options.
        return null;
    }

    /// <summary>
    /// Creates headers for a REST API operation.
    /// </summary>
    protected internal virtual IDictionary<string, string>? CreateRestApiOperationHeaders(RestApiOperation operation, IDictionary<string, object?> arguments, RestApiOperationRunOptions? options)
    {
        // The headers of the operation created here based on operation metadata, arguments, and options.
        return null;
    }

    /// <summary>
    /// Creates a payload for a REST API operation.
    /// </summary>
    protected internal virtual HttpContent? CreateRestApiOperationPayload(RestApiOperation operation, IDictionary<string, object?> arguments, bool enableDynamicPayload, bool enablePayloadNamespacing, RestApiOperationRunOptions? options)
    {
        // The operation payload can be customized here based on operation metadata, arguments, and options.
        return null;
    }

    /// <summary>
    /// Reads the HTTP response content.
    /// </summary>
    protected internal virtual Task<object?> ReadHttpResponseContent(HttpResponseContentReaderContext context, CancellationToken cancellationToken = default)
    {
        // The HTTP response content can be read and transformed here.
        return Task.FromResult<object?>(null);
    }
}
