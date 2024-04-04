// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Extensions;

/// <summary>
/// Extension methods for <see cref="KernelAgent"/>
/// </summary>
public static class AgentNexusExtensions
{
    /// <summary>
    /// Add user message to nexus history
    /// </summary>
    /// <param name="nexus">The target nexus.</param>
    /// <param name="input">Optional user input.</param>
    public static ChatMessageContent? AppendUserMessageToHistory(this AgentNexus nexus, string? input)
    {
        var message = string.IsNullOrWhiteSpace(input) ? null : new ChatMessageContent(AuthorRole.User, input);

        if (message != null)
        {
            nexus.AppendHistory(message);
        }

        return message;
    }
}
