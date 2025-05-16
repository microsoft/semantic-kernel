// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.Magentic;

/// <summary>
/// Represents the context for the MagenticManager, encapsulating the team, task, and chat history.
/// </summary>
public sealed class MagenticManagerContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MagenticManagerContext"/> class.
    /// </summary>
    /// <param name="team">The team associated with the context.</param>
    /// <param name="task">The current task or objective for the team.</param>
    /// <param name="history">The chat message history relevant to the current context (not agent conversation history).</param>
    /// <param name="responseCount">The number of responses generated in the current context.</param>
    /// <param name="stallCount">The number of times the context has stalled or not progressed.</param>
    /// <param name="resetCount">The number of times the context has been reset.</param>
    internal MagenticManagerContext(
        MagenticTeam team,
        IEnumerable<ChatMessageContent> task,
        IEnumerable<ChatMessageContent> history,
        int responseCount,
        int stallCount,
        int resetCount)
    {
        this.Team = team;
        this.Task = [.. task];
        this.History = [.. history];
        this.ResponseCount = responseCount;
        this.StallCount = stallCount;
        this.ResetCount = resetCount;
    }

    /// <summary>
    /// Gets the chat message history for the current context.
    /// </summary>
    /// <remarks>
    /// This history refers to the overall context history, not the conversation history of a specific agent.
    /// </remarks>
    public IReadOnlyList<ChatMessageContent> History { get; }

    /// <summary>
    /// The number of responses generated in the current context.
    /// </summary>
    public int ResponseCount { get; }

    /// <summary>
    /// The number of times the context has stalled or not progressed.
    /// </summary>
    public int StallCount { get; }

    /// <summary>
    /// The number of times the context has been reset.
    /// </summary>
    public int ResetCount { get; }

    /// <summary>
    /// Gets the team associated with this context.
    /// </summary>
    public MagenticTeam Team { get; }

    /// <summary>
    /// Gets the current task or objective for the team, as provided as orchestration input.
    /// </summary>
    public IReadOnlyList<ChatMessageContent> Task { get; }
}
