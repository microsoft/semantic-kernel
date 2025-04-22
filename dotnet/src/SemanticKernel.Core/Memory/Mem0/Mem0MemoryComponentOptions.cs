// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Options for the <see cref="Mem0MemoryComponent"/>.
/// </summary>
[Experimental("SKEXP0130")]
public class Mem0MemoryComponentOptions
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
    /// This value will be overridden by any thread id provided to the methods of the <see cref="Mem0MemoryComponent"/>.
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
    /// Gets or sets a value indicating whether the scope of the memories is limited to the current thread.
    /// </summary>
    /// <remarks>
    /// If false, <see cref="ThreadId"/> will be ignored, and any thread ids passed into the methods of the <see cref="Mem0MemoryComponent"/> will also be ignored.
    /// </remarks>
    public bool ScopeToThread { get; init; } = false;
}
