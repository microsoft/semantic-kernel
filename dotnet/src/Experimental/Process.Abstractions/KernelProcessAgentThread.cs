// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a thread in the process.
/// </summary>
public record KernelProcessAgentThread
{
    /// <summary>
    /// The policy describing how the thread is created and managed in the process.
    /// </summary>
    public KernelProcessThreadLifetime ThreadPolicy { get; init; } = KernelProcessThreadLifetime.Scoped;

    /// <summary>
    /// The type of the thread. This is used to identify the underlying thread type.
    /// </summary>
    public KernelProcessThreadType ThreadType { get; init; } = KernelProcessThreadType.ChatCompletion;

    /// <summary>
    /// The id of the thread. This may be null if the thread is not existing when the Process is created.
    /// </summary>
    public string? ThreadId { get; init; }

    /// <summary>
    /// The name of the thread. This is used to identify the thread in the process.
    /// </summary>
    public string ThreadName { get; init; } = string.Empty;
}
