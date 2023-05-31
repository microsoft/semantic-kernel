// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text;
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
    /// <returns>Stream the generated chat message in string format</returns>
    public static async IAsyncEnumerable<string> GenerateMessageStreamAsync(
        this IChatCompletion chatCompletion,
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var chatCompletionResults = chatCompletion.GetStreamingChatCompletionsAsync(chat, requestSettings, cancellationToken).ConfigureAwait(false);

        await foreach (var chatCompletionResult in chatCompletionResults)
        {
            await foreach (var chatMessageStream in chatCompletionResult.GetStreamingChatMessageAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return chatMessageStream.Content;
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
    /// <returns>Generated chat message in string format</returns>
    public static async Task<string> GenerateMessageAsync(
        this IChatCompletion chatCompletion,
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        var chatResults = await chatCompletion.GetChatCompletionsAsync(chat, requestSettings, cancellationToken).ConfigureAwait(false);

        StringBuilder messageContent = new();
        foreach (var chatResult in chatResults)
        {
            var chatMessage = await chatResult.GetChatMessageAsync(cancellationToken).ConfigureAwait(false);
            messageContent.Append(chatMessage.Content);
        }

        return messageContent.ToString();
    }
}
