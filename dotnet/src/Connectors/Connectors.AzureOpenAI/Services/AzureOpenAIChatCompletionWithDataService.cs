// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

#pragma warning disable CS8424 // The body of an async-iterator method must contain a 'yield' statement.
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
#pragma warning disable CA1065 // Do not raise exceptions in unexpected locations

/// <summary>
/// Azure OpenAI Chat Completion with data service.
/// More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
/// </summary>
[Experimental("SKEXP0010")]
[Obsolete("This class is deprecated in favor of OpenAIPromptExecutionSettings.AzureChatExtensionsOptions")]
public sealed class AzureOpenAIChatCompletionWithDataService : IChatCompletionService, ITextGenerationService
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIChatCompletionWithDataService"/> class.
    /// </summary>
    /// <param name="config">Instance of <see cref="AzureOpenAIChatCompletionWithDataConfig"/> class with completion configuration.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">Instance of <see cref="ILoggerFactory"/> to use for logging.</param>
    public AzureOpenAIChatCompletionWithDataService(
        AzureOpenAIChatCompletionWithDataConfig config,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => throw new NotImplementedException();

    /// <inheritdoc/>
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => throw new NotImplementedException();

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => throw new NotImplementedException();

    /// <inheritdoc/>
    public async Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }
}
