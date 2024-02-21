// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Core;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.TextGeneration;

/// <summary>
/// HuggingFace text generation service.
/// </summary>
public sealed class HuggingFaceTextGenerationService : ITextGenerationService
{
    private Dictionary<string, object?> AttributesInternal { get; } = new();

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextGenerationService"/> class.
    /// </summary>
    /// <param name="model">The HuggingFace model for the text generation service.</param>
    /// <param name="baseUri">The base uri including the port where HuggingFace server is hosted</param>
    /// <param name="apiKey">Optional API key for accessing the HuggingFace service.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the HuggingFace API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public HuggingFaceTextGenerationService(
        string model,
        Uri baseUri,
        string? apiKey = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);

        this.Client = new HuggingFaceClient(
            modelId: model,
            apiKey: apiKey,
            httpRequestFactory: new HuggingFaceHttpRequestFactory(),
#pragma warning disable CA2000
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000
            endpointProvider: new HuggingFaceEndpointProvider(baseUri),
            logger: loggerFactory?.CreateLogger(this.GetType())
        );

        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    private HuggingFaceClient Client { get; }

    /// <inheritdoc />
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this.Client.GenerateTextAsync(prompt, executionSettings, cancellationToken);

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this.Client.StreamGenerateTextAsync(prompt, executionSettings, cancellationToken);
}
