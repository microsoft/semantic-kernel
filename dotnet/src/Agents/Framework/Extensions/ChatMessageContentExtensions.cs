// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents.Extensions;

/// <summary>
/// Extension methods for <see cref="ChatMessageContent"/>
/// </summary>
public static class ChatMessageContentExtensions
{
    /// <summary>
    /// Determines if <see cref="ChatMessageContent"/> has content.
    /// </summary>
    public static bool HasContent(this ChatMessageContent? message)
        => !string.IsNullOrWhiteSpace(message?.Content);

    /// <summary>
    /// Retrieves <see cref="ChatMessageContent.Content"/>, if defined.
    /// </summary>
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
