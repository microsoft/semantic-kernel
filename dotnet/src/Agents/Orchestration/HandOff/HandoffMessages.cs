// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

/// <summary>
/// Common messages used by the <see cref="HandoffOrchestration"/>.
/// </summary>
internal static class HandoffMessages
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public sealed class Input // %%% NAME
    {
        /// <summary>
        /// %%% COMMENT
        /// </summary>
        public ChatMessageContent Task { get; init; } = new();

        /// <summary>
        /// %%% COMMENT
        /// </summary>
        public List<ChatMessageContent> Results { get; init; } = [];
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="task"></param>
    /// <returns></returns>
    public static Input ToInput(this ChatMessageContent task) => new() { Task = task };

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="source"></param>
    /// <param name="result"></param>
    /// <returns></returns>
    public static Input Forward(this Input source, ChatMessageContent result) => new() { Task = source.Task, Results = [.. source.Results, result] };
}
