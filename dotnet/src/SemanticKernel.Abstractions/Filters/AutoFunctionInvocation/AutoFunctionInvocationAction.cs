// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Contains set of actions to perform during function calling.
/// </summary>
[Flags]
public enum AutoFunctionInvocationAction
{
    /// <summary>
    /// Default value, no actions will be performed.
    /// </summary>
    None = 0,

    /// <summary>
    /// This action will stop function call iteration, but proceed with request iteration.
    /// Request iteration will send function results achieved so far, so LLM can decide what to do next.
    /// </summary>
    StopFunctionCallIteration = 1,

    /// <summary>
    /// This action will stop request iteration.
    /// No more requests will be performed to LLM after last function call.
    /// </summary>
    StopRequestIteration = 1 << 1
}
