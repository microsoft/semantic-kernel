// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Process;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Builder class for defining targets to listen for in a process.
/// </summary>
public class ListenForTargetBuilder : ProcessStepEdgeBuilder
{
    private readonly ProcessBuilder _processBuilder;
    private readonly List<MessageSourceBuilder> _messageSources = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="ListenForTargetBuilder"/> class.
    /// </summary>
    /// <param name="messageSources">The list of message sources.</param>
    /// <param name="processBuilder">The process builder.</param>
    public ListenForTargetBuilder(List<MessageSourceBuilder> messageSources, ProcessBuilder processBuilder) : base(processBuilder, "Aggregate", "Aggregate")
    {
        Verify.NotNullOrEmpty(messageSources, nameof(messageSources));
        this._messageSources = messageSources;
        this._processBuilder = processBuilder;
    }

    /// <summary>
    /// Sends the event to the specified target.
    /// </summary>
    /// <param name="target">The target to send the event to.</param>
    /// <returns>A new instance of <see cref="ListenForTargetBuilder"/>.</returns>
    internal override ProcessStepEdgeBuilder SendEventTo_Internal(ProcessFunctionTargetBuilder target)
    {
        Verify.NotNull(target, nameof(target));

        // Create a new event listener for the source messages and the destination step
        var eventListener = new ProcessEventListenerBuilder(this._messageSources, target.Step.Id, id: Guid.NewGuid().ToString("n"));

        // Add the listener to the process builder
        this._processBuilder.AddListenerStep(eventListener);

        // Link the listener to the destination step
        string eventId = "events_received";
        eventListener.LinkTo(eventId, new ProcessStepEdgeBuilder(eventListener, eventId, eventListener.Name)
        {
            Target = target
        });

        foreach (var messageSource in this._messageSources)
        {
            if (messageSource.Source == null)
            {
                throw new InvalidOperationException("Source step cannot be null.");
            }

            // Link all the source steps to the event listener
            messageSource.Source.OnEvent(messageSource.MessageType)
                .SendEventTo(new ProcessFunctionTargetBuilder(eventListener));
        }

        return new ListenForTargetBuilder(this._messageSources, this._processBuilder);
    }
}
