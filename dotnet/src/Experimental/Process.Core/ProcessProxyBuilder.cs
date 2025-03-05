// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality to allow emitting external messages from within the SK
/// process.
/// </summary>
public sealed class ProcessProxyBuilder : ProcessStepBuilder<KernelProxyStep>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessProxyBuilder"/> class.
    /// </summary>
    internal ProcessProxyBuilder(IReadOnlyList<string> externalTopics, string name)
        : base(name)
    {
        if (externalTopics.Count == 0)
        {
            throw new ArgumentException("No topic names registered");
        }

        this._externalTopicUsage = externalTopics.ToDictionary(topic => topic, topic => false);
        if (this._externalTopicUsage.Count < externalTopics.Count)
        {
            throw new ArgumentException("Topic names registered must be different");
        }
    }

    /// <summary>
    /// Version of the proxy step, used when saving the state of the step.
    /// </summary>
    public string Version { get; init; } = "v1";

    internal readonly Dictionary<string, bool> _externalTopicUsage;

    // For supporting multiple step edges getting linked to the same external topic, current implementation needs to be updated
    // to instead have a list of potential edges in case event names in different steps have same name
    internal readonly Dictionary<string, KernelProcessProxyEventMetadata> _eventMetadata = [];

    internal ProcessFunctionTargetBuilder GetExternalFunctionTargetBuilder()
    {
        return new ProcessFunctionTargetBuilder(this, functionName: KernelProxyStep.Functions.EmitExternalEvent, parameterName: "proxyEvent");
    }

    internal void LinkTopicToStepEdgeInfo(string topicName, ProcessStepBuilder sourceStep, ProcessEventData eventData)
    {
        if (!this._externalTopicUsage.TryGetValue(topicName, out bool usedTopic))
        {
            throw new InvalidOperationException($"Topic name {topicName} is not registered as proxy publish event, register first before using");
        }

        if (usedTopic)
        {
            throw new InvalidOperationException($"Topic name {topicName} is is already linked to another step edge");
        }

        this._eventMetadata[eventData.EventName] = new() { EventId = eventData.EventId, TopicName = topicName };
        this._externalTopicUsage[topicName] = true;
    }

    /// <inheritdoc/>
    internal override KernelProcessStepInfo BuildStep(KernelProcessStepStateMetadata? stateMetadata = null)
    {
        if (this._externalTopicUsage.All(topic => !topic.Value))
        {
            throw new InvalidOperationException("Proxy step does not have linked steps to it, link step edges to proxy or remove proxy step");
        }

        KernelProcessProxyStateMetadata proxyMetadata = new()
        {
            Name = this.Name,
            Id = this.Id,
            EventMetadata = this._eventMetadata,
            PublishTopics = this._externalTopicUsage.ToList().Select(topic => topic.Key).ToList(),
        };

        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());

        KernelProcessStepState state = new(this.Name, this.Version, this.Id);

        return new KernelProcessProxy(state, builtEdges)
        {
            ProxyMetadata = proxyMetadata
        };
    }
}
