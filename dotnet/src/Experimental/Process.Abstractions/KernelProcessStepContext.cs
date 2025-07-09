// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides step related functionality for Kernel Functions running in a step.
/// </summary>
public sealed class KernelProcessStepContext
{
    private readonly IKernelProcessMessageChannel _stepMessageChannel;
    private readonly IReadOnlyDictionary<string, ProcessStepEventData> _outputEventsData;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepContext"/> class.
    /// </summary>
    /// <param name="channel">An instance of <see cref="IKernelProcessMessageChannel"/>.</param>
    /// <param name="outputEventsData">event data of output events emitted by step</param>
    public KernelProcessStepContext(IKernelProcessMessageChannel channel, IReadOnlyDictionary<string, ProcessStepEventData>? outputEventsData)
    {
        this._stepMessageChannel = channel;
        this._outputEventsData = outputEventsData ?? new ReadOnlyDictionary<string, ProcessStepEventData>(new Dictionary<string, ProcessStepEventData>());
    }

    /// <summary>
    /// Emit an SK process event from the current step.
    /// </summary>
    /// <param name="processEvent">An instance of <see cref="KernelProcessEvent"/> to be emitted from the <see cref="KernelProcessStep"/></param>
    /// <returns>A <see cref="ValueTask"/></returns>
    public ValueTask EmitEventAsync(KernelProcessEvent processEvent)
    {
        return this._stepMessageChannel.EmitEventAsync(processEvent);
    }

    /// <summary>
    /// Emit an SK process event from the current step with a simplified method signature.
    /// </summary>
    /// <param name="eventId"></param>
    /// <param name="data"></param>
    /// <param name="visibility"></param>
    /// <returns></returns>
    public ValueTask EmitEventAsync(
        string eventId,
        object? data = null,
        KernelProcessEventVisibility visibility = KernelProcessEventVisibility.Internal)
    {
        Verify.NotNullOrWhiteSpace(eventId, nameof(eventId));

        var eventVisibility = KernelProcessEventVisibility.Internal;
        if (this._outputEventsData.TryGetValue(eventId, out var eventData))
        {
            if (eventData.IsPublic)
            {
                eventVisibility = KernelProcessEventVisibility.Public;
            }
        }
        else
        {
            // TODO: Log a warning that the event is not registered in the step metadata -> event mismatch between step implementation and step builder event usage
            var t = "Event with ID '" + eventId + "' is not registered in the step metadata.";
        }

        return this._stepMessageChannel.EmitEventAsync(
            new KernelProcessEvent
            {
                Id = eventId,
                Data = data,
                Visibility = eventVisibility,
            });
    }

    public ValueTask EmitEventAsync<T>(KernelProcessEventDescriptor<T> eventIdData, object? data = null)
    {
        Verify.NotNull(eventIdData, nameof(eventIdData));
        var eventVisibility = KernelProcessEventVisibility.Internal;
        if (this._outputEventsData.TryGetValue(eventIdData.EventName, out var eventData))
        {
            if (eventData.IsPublic)
            {
                eventVisibility = KernelProcessEventVisibility.Public;
            }
        }

        // TODO: Runtime check/warning can be added were to validate that the data type matches the expected type of the event.

        return this._stepMessageChannel.EmitEventAsync(new KernelProcessEvent { Id = eventIdData.EventName, Data = data, Visibility = eventVisibility });
    }
}
