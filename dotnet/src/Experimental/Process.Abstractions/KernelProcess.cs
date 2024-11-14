// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Process.
/// </summary>
public sealed record KernelProcess : KernelProcessStepInfo // TODO: Should be renamed to KernelProcessInfo to keep consistent names
{
    /// <summary>
    /// The collection of Steps in the Process.
    /// </summary>
    public IList<KernelProcessStepInfo> Steps { get; }

    public KernelProcessEventsSubscriberInfo? EventsSubscriber { get; set; } = null;

    /// <summary>
    /// Captures Kernel Process State into <see cref="KernelProcessStateMetadata"/> after process has run
    /// </summary>
    /// <returns><see cref="KernelProcessStateMetadata"/></returns>
    public KernelProcessStateMetadata ToProcessStateMetadata()
    {
        return ProcessStateMetadataFactory.KernelProcessToProcessStateMetadata(this);
    }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcess"/> class.
    /// </summary>
    /// <param name="state">The process state.</param>
    /// <param name="steps">The steps of the process.</param>
    /// <param name="edges">The edges of the process.</param>
    /// TODO: may need to reorder params
    public KernelProcess(KernelProcessState state, IList<KernelProcessStepInfo> steps, Dictionary<string, List<KernelProcessEdge>>? edges = null, KernelProcessEventsSubscriberInfo? eventsSubscriber = null)
        : base(typeof(KernelProcess), state, edges ?? [])
    {
        Verify.NotNull(steps);
        Verify.NotNullOrWhiteSpace(state.Name);

        this.Steps = [.. steps];
        this.EventsSubscriber = eventsSubscriber;
    }
}
