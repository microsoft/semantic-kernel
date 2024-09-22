// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Ollama.Core;
using Microsoft.SemanticKernel.ImageToText;
using OllamaSharp;
using OllamaSharp.Models.Chat;

namespace Microsoft.SemanticKernel.Connectors.Ollama;
/// <summary>
/// Ollama Image To Text Service via Vision Model
/// </summary>
public sealed class OllamaImageToTextService : ServiceBase, IImageToTextService
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaImageToTextService"/> class.
    /// </summary>
    /// <param name="modelId">The hosted model.</param>
    /// <param name="endpoint">The endpoint including the port where Ollama server is hosted</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaImageToTextService(
        string modelId,
        Uri endpoint,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, endpoint, null, loggerFactory)
    {
        Verify.NotNull(endpoint);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaImageToTextService"/> class.
    /// </summary>
    /// <param name="modelId">The hosted model.</param>
    /// <param name="httpClient">HTTP client to be used for communication with the Ollama API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaImageToTextService(
        string modelId,
        HttpClient httpClient,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, null, httpClient, loggerFactory)
    {
        Verify.NotNull(httpClient);
        Verify.NotNull(httpClient.BaseAddress);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaImageToTextService"/> class.
    /// </summary>
    /// <param name="modelId">The hosted model.</param>
    /// <param name="ollamaClient">The Ollama API client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaImageToTextService(
        string modelId,
        OllamaApiClient ollamaClient,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, ollamaClient, loggerFactory)
    {
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc />
    public async Task<IReadOnlyList<TextContent>> GetTextContentsAsync(ImageContent content, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        var settings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);
        var request = CreateChatRequest(content, settings, this._client.SelectedModel);

        List<TextContent> textContents = [];

        await foreach (var stream in this._client.Chat(request, cancellationToken).ConfigureAwait(false))
        {
            textContents.Add(new(stream?.Message.Content));
        }

        return textContents;
    }

    private static ChatRequest CreateChatRequest(ImageContent content, OllamaPromptExecutionSettings settings, string selectedModel)
    {
        List<Message> messages = [];
        messages.Add(new Message { Role = ChatRole.User, Content = "Describe this image:", Images = [content.DataUri!.Split(';')[1].Replace("base64,", "")] });

        var request = new ChatRequest
        {
            Options = new()
            {
                Temperature = settings.Temperature,
                TopP = settings.TopP,
                TopK = settings.TopK,
                Stop = settings.Stop?.ToArray()
            },
            Messages = messages,
            Model = selectedModel,
            Stream = true
        };

        return request;
    }
}
