// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Represents an event listener step in a kernel process that listens for messages from specified sources and routes them to a destination step.
/// </summary>
public record KernelProcessEventListener : KernelProcessStepInfo
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessEventListener"/> class.
    /// </summary>
    /// <param name="messageSources">A <see cref="List{KernelProcessMessageSource}"/></param>
    /// <param name="destinationStepId">The unique Id of the destination step</param>
    /// <param name="state">The initial state of the Step</param>
    /// <param name="edges">The edges of the step.</param>
    public KernelProcessEventListener(List<KernelProcessMessageSource> messageSources, string destinationStepId, KernelProcessStepState state, Dictionary<string, List<KernelProcessEdge>> edges) : base(typeof(KernelProcessEventListenerStep), state, edges)
    {
        Verify.NotNullOrEmpty(messageSources, nameof(messageSources));
        Verify.NotNullOrWhiteSpace(destinationStepId, nameof(destinationStepId));

        this.MessageSources = messageSources;
        this.DestinationStepId = destinationStepId;
    }

    /// <summary>
    /// Gets the list of message sources that this event listener is listening to.
    /// </summary>
    public List<KernelProcessMessageSource> MessageSources { get; }

    /// <summary>
    /// Gets the unique identifier of the destination step that this event listener routes messages to.
    /// </summary>
    public string DestinationStepId { get; }
}
