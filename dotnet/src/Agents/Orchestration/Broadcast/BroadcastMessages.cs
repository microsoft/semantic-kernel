// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;

/// <summary>
/// Common messages used by the <see cref="BroadcastOrchestration"/>.
/// </summary>
public static class BroadcastMessages
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public sealed class Task
    {
        /// <summary>
        /// %%% COMMENT
        /// </summary>
        public ChatMessageContent Message { get; init; } = new();
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public sealed class Result
    {
        /// <summary>
        /// %%% COMMENT
        /// </summary>
        public ChatMessageContent Message { get; init; } = new();
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="message"></param>
    /// <returns></returns>
    public static Result ToResult(this ChatMessageContent message) => new() { Message = message };

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="message"></param>
    /// <returns></returns>
    public static Task ToTask(this ChatMessageContent message) => new() { Message = message };
}
