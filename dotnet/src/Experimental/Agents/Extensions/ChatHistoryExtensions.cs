// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents.Extensions;
internal static class ChatHistoryExtensions
{
    public static IAsyncEnumerable<ChatMessageContent> ToDescending(this ChatHistory history)
    {
        return Reverse().ToAsyncEnumerable();

        IEnumerable<ChatMessageContent> Reverse()
        {
            for (int index = history.Count - 1; index >= 0; --index)
            {
                yield return history[index];
            }
        }
    }
}
