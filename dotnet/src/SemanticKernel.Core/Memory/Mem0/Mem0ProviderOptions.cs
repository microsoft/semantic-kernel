// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Options for the <see cref="Mem0Provider"/>.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class Mem0ProviderOptions
{
    /// <summary>
    /// Gets or sets an optional ID for the application to scope memories to.
    /// </summary>
    /// <remarks>
    /// If not set, the scope of the memories will span all applications.
    /// </remarks>
    public string? ApplicationId { get; init; }

    /// <summary>
    /// Gets or sets an optional ID for the agent to scope memories to.
    /// </summary>
    /// <remarks>
    /// If not set, the scope of the memories will span all agents.
    /// </remarks>
    public string? AgentId { get; init; }

    /// <summary>
    /// Gets or sets an optional ID for the thread to scope memories to.
    /// </summary>
    /// <remarks>
    /// This value will be overridden by any thread id provided to the methods of the <see cref="Mem0Provider"/>.
    /// </remarks>
    public string? ThreadId { get; init; }

    /// <summary>
    /// Gets or sets an optional ID for the user to scope memories to.
    /// </summary>
    /// <remarks>
    /// If not set, the scope of the memories will span all users.
    /// </remarks>
    public string? UserId { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether memories should be scoped to the thread id provided on a per operation basis.
    /// </summary>
    /// <remarks>
    /// This setting is useful if the thread id is not known when the <see cref="Mem0Provider"/> is instantiated, but
    /// per thread scoping is desired.
    /// If <see langword="false"/>, and <see cref="ThreadId"/> is not set, there will be no per thread scoping.
    /// if <see langword="false"/>, and <see cref="ThreadId"/> is set, <see cref="ThreadId"/> will be used for scoping.
    /// If <see langword="true"/>, the thread id will be set to the thread id of the current operation, regardless of the value of <see cref="ThreadId"/>.
    /// </remarks>
    public bool ScopeToPerOperationThreadId { get; init; } = false;

    /// <summary>
    /// When providing the memories found in Mem0 to the AI model on invocation, this string is prefixed
    /// to those memories, in order to provide some context to the model.
    /// </summary>
    /// <value>
    /// Defaults to &quot;## Memories\nConsider the following memories when answering user questions:&quot;
    /// </value>
    public string? ContextPrompt { get; init; }
}
