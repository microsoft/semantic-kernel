﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.ML.OnnxRuntimeGenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Onnx;

/// <summary>
/// Represents a chat completion service using OnnxRuntimeGenAI.
/// </summary>
public sealed class OnnxRuntimeGenAIChatCompletionService : IChatCompletionService, IDisposable
{
    private readonly string _modelPath;
    private OnnxRuntimeGenAIChatClient? _chatClient;
    private IChatCompletionService? _chatClientWrapper;
    private readonly Dictionary<string, object?> _attributesInternal = [];

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;

    /// <summary>
    /// Initializes a new instance of the OnnxRuntimeGenAIChatCompletionService class.
    /// </summary>
    /// <param name="modelId">The name of the model.</param>
    /// <param name="modelPath">The generative AI ONNX model path for the chat completion service.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for various aspects of serialization and deserialization required by the service.</param>
    public OnnxRuntimeGenAIChatCompletionService(
        string modelId,
        string modelPath,
        ILoggerFactory? loggerFactory = null,
        JsonSerializerOptions? jsonSerializerOptions = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(modelPath);

        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
        this._modelPath = modelPath;
    }

    private IChatCompletionService GetChatCompletionService()
    {
        this._chatClient ??= new OnnxRuntimeGenAIChatClient(this._modelPath, new OnnxRuntimeGenAIChatClientOptions()
        {
            PromptFormatter = (messages, options) =>
            {
                StringBuilder promptBuilder = new();
                foreach (var message in messages)
                {
                    promptBuilder.Append($"<|{message.Role}|>\n{message.Text}");
                }
                promptBuilder.Append("<|end|>\n<|assistant|>");

                return promptBuilder.ToString();
            }
        });

        return this._chatClientWrapper ??= this._chatClient.AsChatCompletionService();
    }

    /// <inheritdoc/>
    public void Dispose() => this._chatClient?.Dispose();

    /// <inheritdoc/>
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default) =>
        this.GetChatCompletionService().GetChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default) =>
        this.GetChatCompletionService().GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);
}
