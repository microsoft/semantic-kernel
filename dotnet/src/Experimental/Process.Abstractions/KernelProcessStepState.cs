// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the state of an individual step in a process.
/// </summary>
public class KernelProcessStepState
public record KernelProcessStepState
{
    /// <summary>
    /// The identifier of the Step which is required to be unique within an instance of a Process.
    /// This may be null until a process containing this step has been invoked.
    /// </summary>
    public string? Id { get; init; }

    /// <summary>
    /// The name of the Step. This is itended to be human readable and is not required to be unique. If
    /// not provided, the name will be derived from the steps .NET type.
    /// </summary>
    public string Name { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepState"/> class.
    /// </summary>
    /// <param name="name">The name of the associated <see cref="KernelProcessStep"/></param>
    /// <param name="id">The Id of the associated <see cref="KernelProcessStep"/></param>
    public KernelProcessStepState(string name, string? id = null)
    {
        Verify.NotNullOrWhiteSpace(name);

        this.Id = id;
        this.Name = name;
    }
}

/// <summary>
/// Represents the state of an individual step in a process that includes a user-defined state object.
/// </summary>
/// <typeparam name="TState">The type of the user-defined state.</typeparam>
public sealed class KernelProcessStepState<TState> : KernelProcessStepState where TState : class, new()
public sealed record KernelProcessStepState<TState> : KernelProcessStepState where TState : class, new()
{
    /// <summary>
    /// The user-defined state object associated with the Step.
    /// </summary>
    public TState? State { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepState"/> class.
    /// </summary>
    /// <param name="name">The name of the associated <see cref="KernelProcessStep"/></param>
    /// <param name="id">The Id of the associated <see cref="KernelProcessStep"/></param>
    public KernelProcessStepState(string name, string? id = null)
        : base(name, id)
    {
        Verify.NotNullOrWhiteSpace(name);

        this.Id = id;
        this.Name = name;
    }
}
