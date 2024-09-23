// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Base implementation of a Step in a Process.
/// </summary>
public class KernelProcessStepBase
{
    /// <summary>
    /// A mapping of output edges from the Step using the .
    /// </summary>
    private readonly Dictionary<string, List<KernelProcessEdge>> _outputEdges;

    /// <summary>
    /// The state object of type TState.
    /// </summary>
    internal KernelProcessStepState State { get; init; }

    /// <summary>
    /// A read-only collection of event Ids that this Step can emit.
    /// </summary>
    protected IReadOnlyCollection<string> EventIds => this._outputEdges.Keys.ToList().AsReadOnly();

    /// <summary>
    /// Retrieves the output edges for a given event Id. Returns an empty list if the event Id is not found.
    /// </summary>
    /// <param name="eventId">The Id of an event.</param>
    /// <returns>An <see cref="IReadOnlyCollection{T}"/> where T is <see cref="KernelProcessEdge"/></returns>
    protected IReadOnlyCollection<KernelProcessEdge> GetOutputEdges(string eventId)
    {
        if (this._outputEdges.TryGetValue(eventId, out List<KernelProcessEdge>? edges))
        {
            return edges.AsReadOnly();
        }

        return new List<KernelProcessEdge>().AsReadOnly();
    }

    /// <summary>
    /// Called when the Step is activated.
    /// </summary>
    /// <param name="state">An instance of the state that holds state data for the step.</param>
    /// <returns>An instance of <see cref="ValueTask"/></returns>
    internal virtual ValueTask _ActivateAsync(KernelProcessStepState state)
    {
        return default;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepBase"/> class.
    /// </summary>
    public KernelProcessStepBase(KernelProcessStepState state, Dictionary<string, List<KernelProcessEdge>> edges)
    {
        Verify.NotNull(state);
        Verify.NotNull(edges);

        this.State = state;
        this._outputEdges = edges;
    }
}

/// <summary>
/// Process Step. Derive from this class to create a new Step for a Process.
/// </summary>
public class KernelProcessStep : KernelProcessStepBase
{
    /// <inheritdoc/>
    internal override ValueTask _ActivateAsync(KernelProcessStepState state)
    {
        Verify.NotNull(state);
        return this.ActivateAsync(state);
    }

    /// <inheritdoc/>
    public virtual ValueTask ActivateAsync(KernelProcessStepState state)
    {
        return default;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStep"/> class.
    /// </summary>
    /// <param name="state">An instance that derives from <see cref="KernelProcessStepState"/></param>
    /// <param name="edges">The output edges.</param>
    protected KernelProcessStep(KernelProcessStepState? state = null, Dictionary<string, List<KernelProcessEdge>>? edges = null)
        : base(state ?? new(), edges ?? [])
    {
    }
}

/// <summary>
/// Process Step. Derive from this class to create a new Step with user-defined state of type TState for a Process.
/// </summary>
/// <typeparam name="TState">An instance of TState used for user-defined state.</typeparam>
public class KernelProcessStep<TState> : KernelProcessStepBase where TState : class, new()
{
    internal new ProcessStepState<TState> State => base.State as ProcessStepState<TState> ?? new();

    /// <inheritdoc/>
    internal override ValueTask _ActivateAsync(KernelProcessStepState state)
    {
        var genericState = state as ProcessStepState<TState>;
        Verify.NotNull(genericState);

        // initialize the state if it is null
        if (genericState.State is null)
        {
            genericState.State = new TState();
        }

        return this.ActivateAsync(genericState);
    }

    /// <inheritdoc/>
    public virtual ValueTask ActivateAsync(ProcessStepState<TState> state)
    {
        return this._ActivateAsync(state);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStep"/> class.
    /// </summary>
    /// <param name="state">The state associated with this step.</param>
    /// <param name="edges">The output edges.</param>
    public KernelProcessStep(ProcessStepState<TState>? state = null, Dictionary<string, List<KernelProcessEdge>>? edges = null)
        : base(state ?? new(), edges ?? [])
    {
    }
}
