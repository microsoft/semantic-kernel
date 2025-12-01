// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

internal class LocalEdgeGroupProcessor
{
    private readonly KernelProcessEdgeGroup _edgeGroup;
    private readonly Dictionary<string, object?> _messageData = [];
    private HashSet<string> _requiredMessages = new();
    private HashSet<string> _absentMessages = new();

    public LocalEdgeGroupProcessor(KernelProcessEdgeGroup edgeGroup)
    {
        Verify.NotNull(edgeGroup, nameof(edgeGroup));
        this._edgeGroup = edgeGroup;

        this.InitializeEventTracking();
    }

    public bool TryGetResult(ProcessMessage message, out Dictionary<string, object?>? result)
    {
        string messageKey = this.GetKeyForMessageSource(message);
        if (!this._requiredMessages.Contains(messageKey))
        {
            throw new KernelException($"Message {messageKey} is not expected for edge group {this._edgeGroup.GroupId}.");
        }

        this._messageData[messageKey] = (message.TargetEventData as KernelProcessEventData)!.ToObject();

        this._absentMessages.Remove(messageKey);
        if (this._absentMessages.Count == 0)
        {
            // We have received all required events so forward them to the target
            result = (Dictionary<string, object?>?)this._edgeGroup.InputMapping(this._messageData);

            // TODO: Reset state according to configured logic i.e. reset after first message or after all messages are received.
            this.InitializeEventTracking();

            return true;
        }

        result = null;
        return false;
    }

    private void InitializeEventTracking()
    {
        this._requiredMessages = this.BuildRequiredEvents(this._edgeGroup.MessageSources);
        this._absentMessages = [.. this._requiredMessages];
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
