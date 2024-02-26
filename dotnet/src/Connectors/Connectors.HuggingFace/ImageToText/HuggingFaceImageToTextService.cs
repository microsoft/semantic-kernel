// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Core;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.ImageToText;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.ImageToText;

internal class HuggingFaceImageToTextService : IImageToTextService
{
    private Dictionary<string, object?> AttributesInternal { get; } = new();
    private HuggingFaceClient Client { get; }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceImageToTextService"/> class.
    /// </summary>
    /// <param name="model">The HuggingFace model for image-to-text conversion.</param>
    /// <param name="endpoint">The endpoint uri including the port where HuggingFace server is hosted</param>
    /// <param name="apiKey">Optional API key for accessing the HuggingFace service.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the HuggingFace API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public HuggingFaceImageToTextService(
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);

        this.Client = new HuggingFaceClient(
            modelId: model,
            endpoint: endpoint ?? httpClient?.BaseAddress,
            apiKey: apiKey,
#pragma warning disable CA2000 // Dispose objects before losing scope
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000 // Dispose objects before losing scope
            logger: loggerFactory?.CreateLogger(this.GetType())
        );

        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    /// <inheritdoc />
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(ImageContent content, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this.Client.GenerateTextFromImageAsync(content, executionSettings, kernel, cancellationToken);
}
