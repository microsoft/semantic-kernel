// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

public interface IChatCompletion
{
    /// <summary>
    /// Create a new empty chat instance
    /// </summary>
    /// <param name="instructions">Optional chat instructions for the AI service</param>
    /// <returns>Chat object</returns>
    ChatHistory CreateNewChat(string instructions = "");

    /// <summary>
    /// Generate a new chat message
    /// </summary>
    /// <param name="chat">Chat history</param>
    /// <param name="requestSettings">AI request settings</param>
    /// <param name="cancellationToken">Async cancellation token</param>
    /// <returns>Generated chat message in string format</returns>
    Task<string> GenerateMessageAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Generate a new chat message
    /// </summary>
    /// <param name="chat">Chat history</param>
    /// <param name="requestSettings">AI request settings</param>
    /// <param name="cancellationToken">Async cancellation token</param>
    /// <returns>Stream the generated chat message in string format</returns>
    IAsyncEnumerable<string> GenerateMessageStreamAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default);

    Task<IReadOnlyList<IChatCompletionResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default);

    IAsyncEnumerable<IChatCompletionStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default);
}

public interface IChatCompletionResult
{
    Task<IChatMessage> GetChatMessageAsync(CancellationToken cancellationToken = default);
}

public interface IChatCompletionStreamingResult : IChatCompletionResult
{
    IAsyncEnumerable<IChatMessage> GetChatMessageStreamingAsync(CancellationToken cancellationToken = default);
}

public static class ChatCompletionExtensions
{
    public static IAsyncEnumerable<string> GenerateMessageStreamAsync(this IChatCompletion chatCompletion,
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        return Array.Empty<string>().ToAsyncEnumerable();
    }
}
