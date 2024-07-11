// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Ollama.Core;
using Microsoft.SemanticKernel.TextGeneration;
using OllamaSharp;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Represents a text generation service using Ollama Original API.
/// </summary>
public sealed class OllamaTextGenerationService : ServiceBase, ITextGenerationService
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextGenerationService"/> class.
    /// </summary>
    /// <param name="model">The Ollama model for the text generation service.</param>
    /// <param name="endpoint">The endpoint including the port where Ollama server is hosted</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Ollama API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextGenerationService(
        string model,
        Uri endpoint,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
        : base(model, endpoint, httpClient, loggerFactory)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextGenerationService"/> class.
    /// </summary>
    /// <param name="model">The hosted model.</param>
    /// <param name="ollamaClient">The Ollama API client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextGenerationService(
        string model,
        OllamaApiClient ollamaClient,
        ILoggerFactory? loggerFactory = null)
        : base(model, ollamaClient, loggerFactory)
    {
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc />
    public async Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var content = await this._client.GetCompletion(prompt, null, cancellationToken).ConfigureAwait(false);

        return [new(content.Response, modelId: this._client.SelectedModel, innerContent: content, metadata:
            new Dictionary<string, object?>()
            {
                ["Context"] = content.Context
            })];
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var content in this._client.StreamCompletion(prompt, null, cancellationToken).ConfigureAwait(false))
        {
            yield return new StreamingTextContent(content?.Response, modelId: content?.Model, innerContent: content, metadata: new OllamaMetadata(content));
        }
    }
}
