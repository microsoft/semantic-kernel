// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.Orchestration.Sequential;

/// <summary>
/// A message that describes the input task and captures results for a <see cref="SequentialOrchestration{TInput,TOutput}"/>.
/// </summary>
public sealed class SequentialMessage
{
    /// <summary>
    /// The input task.
    /// </summary>
    public ChatMessageContent Message { get; init; } = new();

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="SequentialMessage"/>.
    /// </summary>
    public static SequentialMessage FromChat(ChatMessageContent content) => new() { Message = content };
}
