// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// Common messages used in the Magentic framework.
/// </summary>
public static class GroupChatMessages
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public sealed class Group
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
    /// Reset/clear the conversation history.
    /// </summary>
    public sealed class Reset { }

    /// <summary>
    /// Signal the agent to respond.
    /// </summary>
    public sealed class Speak { }

    /// <summary>
    /// Defines the task to be performed.
    /// </summary>
    public sealed class Task
    {
        /// <summary>
        /// A task that does not require any action.
        /// </summary>
        public static readonly Task None = new();

        /// <summary>
        /// The input that defines the task goal.
        /// </summary>
        public string Input { get; init; } = string.Empty;
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="message"></param>
    /// <returns></returns>
    public static Group ToGroup(this ChatMessageContent message) => new() { Message = message };

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="message"></param>
    /// <returns></returns>
    public static Result ToResult(this ChatMessageContent message) => new() { Message = message };
}
