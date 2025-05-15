// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;
internal class LocalEdgeGroupProcessor
{
    private readonly KernelProcessEdgeGroup _edgeGroup;
    private HashSet<string> _requiredMessages = new();
    private HashSet<string> _absentMessages = new();

    public Dictionary<string, object?> MessageData { get; private set; } = [];

    public LocalEdgeGroupProcessor(KernelProcessEdgeGroup edgeGroup)
    {
        Verify.NotNull(edgeGroup, nameof(edgeGroup));
        this._edgeGroup = edgeGroup;

        this.InitializeEventTracking();
    }

    public void ClearMessageData()
    {
        this.MessageData.Clear();
        this.InitializeEventTracking();
    }

    public bool RehydrateMessageData(Dictionary<string, object?> cachedMessageData)
    {
        if (cachedMessageData == null || cachedMessageData.Count == 0)
        {
            return false;
        }

        // Add check to ensure message data values have supported types

        foreach (var message in cachedMessageData)
        {
            this.MessageData[message.Key] = message.Value;
        }
        this._absentMessages.RemoveWhere(message => cachedMessageData.ContainsKey(message));

        return true;
    }

    public bool TryGetResult(ProcessMessage message, out Dictionary<string, object?>? result)
    {
        string messageKey = this.GetKeyForMessageSource(message);
        if (!this._requiredMessages.Contains(messageKey))
        {
            throw new KernelException($"Message {messageKey} is not expected for edge group {this._edgeGroup.GroupId}.");
        }

        if (message.TargetEventData is KernelProcessEventData processEventData)
        {
            // used by events from steps
            this.MessageData[messageKey] = processEventData.ToObject();
        }
        else
        {
            // used by events that are process input events
            this.MessageData[messageKey] = message.TargetEventData;
        }

        this._absentMessages.Remove(messageKey);
        if (this._absentMessages.Count == 0)
        {
            // We have received all required events so forward them to the target
            result = (Dictionary<string, object?>?)this._edgeGroup.InputMapping(this.MessageData);

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
