// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.History;

/// <summary>
/// Defines a contract for a reducing chat history to be used by agents.
/// </summary>
/// <remarks>
/// The additional interface methods are used to evaluate the equality of different reducers, which is necessary for the agent channel key.
/// </remarks>
public interface IAgentChatHistoryReducer : IChatHistoryReducer
{
    /// <summary>
    /// Each reducer shall override equality evaluation so that different reducers
    /// of the same configuration can be evaluated for equivalency.
    /// </summary>
    bool Equals(object? obj);

    /// <summary>
    /// Each reducer shall implement custom hash-code generation so that different reducers
    /// of the same configuration can be evaluated for equivalency.
    /// </summary>
    int GetHashCode();
}
