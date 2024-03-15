// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Experimental.Agents.Extensions;

/// <summary>
/// $$$
/// </summary>
public static class ChatMessageContentExtensions
{
    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="message"></param>
    /// <returns></returns>
    public static bool HasContent(this ChatMessageContent? message)
        => !string.IsNullOrWhiteSpace(message?.Content);

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="message"></param>
    /// <param name="content"></param>
    /// <returns></returns>
    public static bool TryGetContent(this ChatMessageContent? message, out string content)
    {
        if (message.HasContent())
        {
            content = message!.Content!;
            return true;
        }

        content = string.Empty;
        return false;
    }
}
