// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the type of target for a process.
/// </summary>
public enum ProcessTargetType
{
    /// <summary>
    /// The target is a step.
    /// </summary>
    Invocation,

    /// <summary>
    /// The target is a function.
    /// </summary>
    KernelFunction,

    /// <summary>
    /// The target is a parameter.
    /// </summary>
    StateUpdate
}
