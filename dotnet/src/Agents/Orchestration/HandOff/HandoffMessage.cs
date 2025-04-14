// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

/// <summary>
/// A message that describes the input task and captures results for a <see cref="HandoffOrchestration{TInput,TOutput}"/>.
/// </summary>
public sealed class HandoffMessage
{
    /// <summary>
    /// The input task.
    /// </summary>
    public ChatMessageContent Content { get; init; } = new();

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="HandoffMessage"/>.
    /// </summary>
    public static HandoffMessage FromChat(ChatMessageContent content) => new() { Content = content };
}
