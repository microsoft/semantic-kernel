// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Settings that affect behavior of <see cref="AgentGroupChat"/>.
/// </summary>
/// <remarks>
/// Default behavior result in no agent selection.
/// </remarks>
public class AgentGroupChatSettings
{
    /// <summary>
    /// Optional strategy for evaluating whether to terminate multiturn chat.
    /// </summary>
    /// <remarks>
    /// See <see cref="TerminationStrategy"/>.
    /// </remarks>
    public TerminationStrategy TerminationStrategy { get; init; } = new DefaultTerminationStrategy();

    /// <summary>
    /// An optional strategy for selecting the next agent.
    /// </summary>
    /// <remarks>
    /// See <see cref="SelectionStrategy"/>.
    /// </remarks>
    public SelectionStrategy SelectionStrategy { get; init; } = new SequentialSelectionStrategy();
}
