// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
//using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using ChatTokenUsage = OpenAI.Chat.ChatTokenUsage;

namespace Magentic.Extensions;

/// <summary>
/// Extension methods for <see cref="ChatMessageContent"/>.
/// </summary>
public static class ChatMessageContentExtensions
{
    /// <summary>
    /// Get the usage metadata from a message.
    /// </summary>
    public static ChatTokenUsage? GetUsage(this ChatMessageContent message)
    {
        if (message.Metadata?.TryGetValue("Usage", out object? usage) ?? false)
        {
            if (usage is ChatTokenUsage chatUsage)
            {
                return chatUsage;
            }
        }
        return null;
    }

    ///// <summary>
    ///// Transform chat message to a progress message.
    ///// </summary>
    //internal static ChatMessages.Progress ToProgress(this ChatMessageContent message, string label)
    //{
    //    ChatTokenUsage? usage = message.GetUsage();
    //    return
    //        new ChatMessages.Progress
    //        {
    //            Label = label,
    //            TotalTokens = usage?.TotalTokenCount,
    //            InputTokens = usage?.InputTokenCount,
    //            OutputTokens = usage?.OutputTokenCount,
    //        };
    //}
}
