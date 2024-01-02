// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Extension methods for <see cref="ChatHistory"/> class.
/// </summary>
internal static class ChatHistoryExtensions
{
    /// <summary>
    /// Returns the number of tokens in the chat history.
    /// </summary>
    /// <param name="chatHistory">The chat history.</param>
    /// <param name="additionalMessage">An additional message to include in the token count.</param>
    /// <param name="skipStart">The index to start skipping messages.</param>
    /// <param name="skipCount">The number of messages to skip.</param>
    /// <param name="tokenCounter">The token counter to use.</param>
    internal static int GetTokenCount(this ChatHistory chatHistory, string? additionalMessage = null, int skipStart = 0, int skipCount = 0, TextChunker.TokenCounter? tokenCounter = null)
    {
        return tokenCounter is null ?
            Default(chatHistory, additionalMessage, skipStart, skipCount) :
            Custom(chatHistory, additionalMessage, skipStart, skipCount, tokenCounter);

        static int Default(ChatHistory chatHistory, string? additionalMessage, int skipStart, int skipCount)
        {
            int chars = 0;
            bool prevMsg = false;
            for (int i = 0; i < chatHistory.Count; i++)
            {
                if (i >= skipStart && i < skipStart + skipCount)
                {
                    continue;
                }

                chars += chatHistory[i].Content?.Length ?? 0;

                // +1 for "\n" if there was a previous message
                if (prevMsg)
                {
                    chars++;
                }
                prevMsg = true;
            }

            if (additionalMessage is not null)
            {
                chars += 1 + additionalMessage.Length; // +1 for "\n"
            }

            return chars / 4; // same as TextChunker's default token counter
        }

        static int Custom(ChatHistory chatHistory, string? additionalMessage, int skipStart, int skipCount, TextChunker.TokenCounter tokenCounter)
        {
            var messages = string.Join("\n", chatHistory.Where((m, i) => i < skipStart || i >= skipStart + skipCount).Select(m => m.Content));

            if (!string.IsNullOrEmpty(additionalMessage))
            {
                messages = $"{messages}\n{additionalMessage}";
            }

            var tokenCount = tokenCounter(messages);
            return tokenCount;
        }
    }
}
