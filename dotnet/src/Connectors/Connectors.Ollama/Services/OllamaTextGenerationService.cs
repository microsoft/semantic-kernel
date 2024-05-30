// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;
using OllamaSharp;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Represents a text generation service using Ollama Original API.
/// </summary>
public sealed class OllamaTextGenerationService : ITextGenerationService
{
    private Dictionary<string, object?> AttributesInternal { get; } = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextGenerationService"/> class.
    /// </summary>
    /// <param name="model">The Ollama model for the text generation service.</param>
    /// <param name="baseUri">The base uri including the port where Ollama server is hosted</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Ollama API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextGenerationService(
        string model,
        Uri baseUri,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);

        this.Client = new OllamaApiClient(baseUri, model);

        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    private OllamaApiClient Client { get; }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc />
    public async Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        var completionResponse = await this.Client.GetCompletion(prompt, null, cancellationToken).ConfigureAwait(false);

        TextContent stc = new TextContent(completionResponse.Response);
        return new List<TextContent> { stc };
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        var completionResponse = await this.Client.StreamCompletion(prompt, null, cancellationToken).ConfigureAwait(false);

        yield return new StreamingTextContent(completionResponse.Response);
    }
}
