// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

public static class ChatCompletionExtensions
{
    /// <summary>
    /// Generate a new chat message
    /// </summary>
    /// <param name="chatCompletion">Target interface to extend</param>
    /// <param name="chat">Chat history</param>
    /// <param name="requestSettings">AI request settings</param>
    /// <param name="cancellationToken">Async cancellation token</param>
    /// <remarks>This extension does not support multiple prompt results (Only the first will be returned)</remarks>
    /// <returns>Stream the generated chat message in string format</returns>
    public static async IAsyncEnumerable<string> GenerateMessageStreamAsync(
        this IChatCompletion chatCompletion,
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var chatCompletionResult in chatCompletion.GetStreamingChatCompletionsAsync(chat, requestSettings, cancellationToken).ConfigureAwait(false))
        {
            await foreach (var chatMessageStream in chatCompletionResult.GetStreamingChatMessageAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return chatMessageStream.Content;
            }

            yield break;
        }
    }

    /// <summary>
    /// Generate a new chat message
    /// </summary>
    /// <param name="chatCompletion">Target interface to extend</param>
    /// <param name="chat">Chat history</param>
    /// <param name="requestSettings">AI request settings</param>
    /// <param name="cancellationToken">Async cancellation token</param>
    /// <returns>Stream the generated chat message in string format</returns>
    public static async IAsyncEnumerable<string> GenerateMessagesStreamAsync(
        this IChatCompletion chatCompletion,
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var chatCompletionResult in chatCompletion.GetStreamingChatCompletionsAsync(chat, requestSettings, cancellationToken).ConfigureAwait(false))
        {
            await foreach (var chatMessageStream in chatCompletionResult.GetStreamingChatMessageAsync(cancellationToken).ConfigureAwait(false))
            {
                if (!string.IsNullOrWhiteSpace(chatMessageStream.Content))
                {
                    yield return chatMessageStream.Content;
                }
            }
        }
    }

    /// <summary>
    /// Generate a new chat message
    /// </summary>
    /// <param name="chatCompletion">Target interface to extend</param>
    /// <param name="chat">Chat history</param>
    /// <param name="requestSettings">AI request settings</param>
    /// <param name="cancellationToken">Async cancellation token</param>
    /// <remarks>This extension does not support multiple prompt results (Only the first will be returned)</remarks>
    /// <returns>Generated chat message in string format</returns>
    public static async Task<string> GenerateMessageAsync(
        this IChatCompletion chatCompletion,
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        var chatResults = await chatCompletion.GetChatCompletionsAsync(chat, requestSettings, cancellationToken).ConfigureAwait(false);
        var firstChatMessage = await chatResults[0].GetChatMessageAsync(cancellationToken).ConfigureAwait(false);

        return firstChatMessage.Content;
    }
}
