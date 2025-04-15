// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Ollama.Core;
using Microsoft.SemanticKernel.TextGeneration;
using OllamaSharp;
using OllamaSharp.Models;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Represents a text generation service using Ollama Original API.
/// </summary>
public sealed class OllamaTextGenerationService : ServiceBase, ITextGenerationService
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The Ollama model for the text generation service.</param>
    /// <param name="endpoint">The endpoint including the port where Ollama server is hosted</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextGenerationService(
        string modelId,
        Uri endpoint,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, endpoint, null, loggerFactory)
    {
        Verify.NotNull(endpoint);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The Ollama model for the text generation service.</param>
    /// <param name="httpClient">HTTP client to be used for communication with the Ollama API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextGenerationService(
        string modelId,
        HttpClient httpClient,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, null, httpClient, loggerFactory)
    {
        Verify.NotNull(httpClient);
        Verify.NotNull(httpClient.BaseAddress);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The hosted model.</param>
    /// <param name="ollamaClient">The Ollama API client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextGenerationService(
        string modelId,
        OllamaApiClient ollamaClient,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, ollamaClient, loggerFactory)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextGenerationService"/> class.
    /// </summary>
    /// <param name="ollamaClient">The Ollama API client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextGenerationService(
        OllamaApiClient ollamaClient,
        ILoggerFactory? loggerFactory = null)
        : base(ollamaClient.SelectedModel, ollamaClient, loggerFactory)
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
        var fullContent = new StringBuilder();
        List<GenerateResponseStream> innerContent = [];
        string? modelId = null;

        var settings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);
        var request = CreateRequest(settings, this._client.SelectedModel);
        request.Prompt = prompt;

        await foreach (var responseStreamChunk in this._client.GenerateAsync(request, cancellationToken).ConfigureAwait(false))
        {
            if (responseStreamChunk is null)
            {
                continue;
            }

            innerContent.Add(responseStreamChunk);
            fullContent.Append(responseStreamChunk.Response);

            modelId ??= responseStreamChunk.Model;
        }

        return [new TextContent(
                text: fullContent.ToString(),
                modelId: modelId,
                innerContent: innerContent)];
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var settings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);
        var request = CreateRequest(settings, this._client.SelectedModel);
        request.Prompt = prompt;

        await foreach (var content in this._client.GenerateAsync(request, cancellationToken).ConfigureAwait(false))
        {
            yield return new StreamingTextContent(
                text: content?.Response,
                modelId: content?.Model,
                innerContent: content);
        }
    }

    private static GenerateRequest CreateRequest(OllamaPromptExecutionSettings settings, string selectedModel)
    {
        var request = new GenerateRequest
        {
            Options = new()
            {
                Temperature = settings.Temperature,
                TopP = settings.TopP,
                TopK = settings.TopK,
                Stop = settings.Stop?.ToArray(),
                NumPredict = settings.NumPredict
            },
            Model = selectedModel,
            Stream = true
        };

        return request;
    }
}
