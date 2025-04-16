// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors.Runtime;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

internal class MessageListenerActor : StepActor
{
    private DaprMessageListenerInfo? _eventListener;
    private HashSet<string> _requiredMessages = [];
    private HashSet<string> _absentMessages = [];
    private readonly Dictionary<string, object?> _messageData = [];

    /// <summary>
    /// Initializes a new instance of the <see cref="MessageListenerActor"/> class.
    /// </summary>
    /// <param name="host"></param>
    /// <param name="kernel"></param>
    public MessageListenerActor(ActorHost host, Kernel kernel) : base(host, kernel)
    {
    }

    protected override void InitializeStep(DaprStepInfo stepInfo, string? parentProcessId, string? eventProxyStepId = null)
    {
        if (stepInfo is not DaprMessageListenerInfo daprMessageListener)
        {
            throw new KernelException($"Invalid step info type: {stepInfo.GetType()}");
        }

        this._eventListener = daprMessageListener;
        this._requiredMessages = this.BuildRequiredEvents(this._eventListener.MessageSources);
        this._absentMessages = [.. this._requiredMessages];

        base.InitializeStep(stepInfo, parentProcessId, eventProxyStepId);
    }

    internal override async Task HandleMessageAsync(ProcessMessage message)
    {
        Verify.NotNull(message, nameof(message));

        // Lazy one-time initialization of the step before processing a message
        await this._activateTask.Value.ConfigureAwait(false);

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
                Id = this._eventListener!.State.Id!
            };

            await this.EmitEventAsync(new KernelProcessEvent
            {
                Id = "events_received",
                Data = this._messageData
            }).ConfigureAwait(false);
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
