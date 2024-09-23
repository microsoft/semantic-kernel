// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the state of an individual step in a process.
/// </summary>
public class KernelProcessStepState

{
    /// <summary>
    /// The identifier of the Step which is required to be unique within an instance of a Process.
    /// This may not be null until a process containing this step has been invoked.
    /// </summary>
    public string? Id { get; set; }

    /// <summary>
    /// The name of the Step. This is itended to be human readable and is not required to be unique. If not set
    /// when the Step is added to a Process, the name will be derived from the steps .NET type.
    /// </summary>
    public string? Name { get; set; }
}

/// <summary>
/// Represents the state of an individual step in a process that includes a user-defined state object.
/// </summary>
/// <typeparam name="TState">The type of the user-defined state.</typeparam>
public sealed class ProcessStepState<TState> : KernelProcessStepState where TState : class, new()
{
    /// <summary>
    /// The user-defined state object associated with the Step.
    /// </summary>
    public TState? State { get; set; }
}
