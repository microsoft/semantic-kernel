// Copyright (c) Microsoft. All rights reserved.

using static Microsoft.SemanticKernel.Text.TextChunker;

namespace Microsoft.SemanticKernel.Planning.Structured.Extensions;

using System.Linq;
using AI.ChatCompletion;


/// <summary>
/// Extension methods for <see cref="ChatHistory"/> class.
/// </summary>
public static class ChatHistoryExtensions
{
    /// <summary>
    /// Returns the number of tokens in the chat history.
    /// </summary>
    // <param name="chatHistory">The chat history.</param>
    // <param name="additionalMessage">An additional message to include in the token count.</param>
    // <param name="skipStart">The index to start skipping messages.</param>
    // <param name="skipCount">The number of messages to skip.</param>
    // <param name="tokenCounter">The token counter to use.</param>
    internal static int GetTokenCount(this ChatHistory chatHistory, string? additionalMessage = null, int skipStart = 0, int skipCount = 0, TokenCounter? tokenCounter = null)
    {
        tokenCounter ??= DefaultTokenCounter;

        var messages = string.Join("\n", chatHistory.Where((m, i) => i < skipStart || i >= skipStart + skipCount).Select(m => m.Content));

        if (!string.IsNullOrEmpty(additionalMessage))
        {
            messages = $"{messages}\n{additionalMessage}";
        }

        var tokenCount = tokenCounter(messages);
        return tokenCount;
    }


    private static int DefaultTokenCounter(string input) => input.Length / 4;
}
