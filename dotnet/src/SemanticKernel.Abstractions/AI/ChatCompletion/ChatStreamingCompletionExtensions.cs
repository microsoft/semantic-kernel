// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Provides extension methods for the IChatCompletion interface.
/// </summary>
public static class ChatStreamingCompletionExtensions
{
    /// <summary>
    /// Generates a new chat message as an asynchronous stream.
    /// </summary>
    /// <param name="chatCompletion">The target IChatCompletion interface to extend.</param>
    /// <param name="chat">The chat history.</param>
    /// <param name="requestSettings">The AI request settings (optional).</param>
    /// <param name="cancellationToken">The asynchronous cancellation token (optional).</param>
    /// <remarks>This extension does not support multiple prompt results (only the first will be returned).</remarks>
    /// <returns>An asynchronous stream of the generated chat message in string format.</returns>
    public static async IAsyncEnumerable<string> GenerateMessageStreamAsync(
        this IChatStreamingCompletion chatCompletion,
        ChatHistory chat,
        AIRequestSettings? requestSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // Using var below results in Microsoft.CSharp.RuntimeBinder.RuntimeBinderException : Cannot apply indexing with [] to an expression of type 'object'
        IAsyncEnumerable<IChatStreamingResult> chatCompletionResults = chatCompletion.GetChatStreamingResultsAsync(chat, requestSettings, cancellationToken);
        await foreach (var chatCompletionResult in chatCompletionResults)
        {
            await foreach (var chatMessageStream in chatCompletionResult.GetChatMessageStreamingAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return chatMessageStream.Content;
            }

            yield break;
        }
    }
}
