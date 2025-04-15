// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process;
internal class LocalListener : LocalStep
{
    private readonly KernelProcessEventListener _eventListener;
    private readonly HashSet<string> _requiredMessages = new();
    private readonly HashSet<string> _absentMessages = new();
    private readonly Dictionary<string, object?> _messageData = [];
    private readonly LocalStep _targetStep;

    public LocalListener(KernelProcessEventListener eventListener, Kernel kernel, LocalStep _targetStep, string? parentProcessId = null) : base(eventListener, kernel, parentProcessId)
    {
        Verify.NotNull(eventListener, nameof(eventListener));
        Verify.NotNull(_targetStep, nameof(_targetStep));

        this._targetStep = _targetStep;
        this._eventListener = eventListener;
        this._requiredMessages = this.BuildRequiredEvents(eventListener.MessageSources);
        this._absentMessages = [.. this._requiredMessages];
    }

    /// <inheritdoc/>
    protected override ValueTask InitializeStepAsync()
    {
        return default;
    }

    internal override async Task HandleMessageAsync(ProcessMessage message)
    {
        string messageKey = this.GetKeyForMessageSource(message);
        if (!this._requiredMessages.Contains(messageKey))
        {
            // TODO: Should throw? Event is not excepted.
            return;
        }

        this._messageData[messageKey] = message.TargetEventData;

        this._absentMessages.Remove(messageKey);
        if (this._absentMessages.Count == 0)
        {
            // We have recieved all required events so forward them to the target
            KernelProcessEvent kernelProcessEvent = new()
            {
                Data = this._messageData,
                Id = this._eventListener.State.Id!
            };

            await this.EmitEventAsync(new KernelProcessEvent
            {
                Id = "events_received",
                Data = this._messageData
            }).ConfigureAwait(false);

            //await this._targetStep.EmitEventAsync(kernelProcessEvent).ConfigureAwait(false);
        }

        return;
    }

    private HashSet<string> BuildRequiredEvents(List<KernelProcessMessageSource> messageSources)
    {
        var requiredEvents = new HashSet<string>();
        foreach (var source in messageSources)
        {
            requiredEvents.Add(this.GetKeyForMessageSource(source));
        }

        return requiredEvents;
    }

    private string GetKeyForMessageSource(KernelProcessMessageSource messageSource)
    {
        return $"{messageSource.SourceStepId}.{messageSource.MessageType}";
    }

    private string GetKeyForMessageSource(ProcessMessage message)
    {
        return $"{message.SourceId}.{message.SourceEventId}";
    }
}
