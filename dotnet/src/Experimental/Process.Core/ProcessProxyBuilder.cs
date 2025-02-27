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
        this.ExternalTopicUsage = externalTopics.ToDictionary(topic => topic, topic => false);
    }

    /// <summary>
    /// Version of the map-step, used when saving the state of the step.
    /// </summary>
    public string Version { get; init; } = "v1";

    internal Dictionary<string, bool> ExternalTopicUsage { get; }
    internal Dictionary<string, KernelProcessProxyEventMetadata> EventMetadata { get; } = [];

    internal ProcessFunctionTargetBuilder GetExternalFunctionTargetBuilder()
    {
        return new ProcessFunctionTargetBuilder(this, functionName: KernelProxyStep.Functions.EmitExternalEvent, parameterName: "proxyEvent");
    }

    internal ProcessFunctionTargetBuilder GetInternalFunctionTargetBuilder()
    {
        return new ProcessFunctionTargetBuilder(this, functionName: KernelProxyStep.Functions.EmitInternalEvent, parameterName: "proxyEvent");
    }

    internal void LinkTopicToStepEdgeInfo(string topicName, ProcessStepBuilder sourceStep, ProcessEventData eventData)
    {
        if (!this.ExternalTopicUsage.TryGetValue(topicName, out bool usedTopic))
        {
            throw new InvalidOperationException($"Topic name {topicName} is not registered as proxy publish event, register first before using");
        }

        // todo-estenori: need to test how it works when multiple steps emit the same topic externally
        if (usedTopic)
        {
            throw new InvalidOperationException($"Topic name {topicName} is is already linked to another step edge");
        }

        this.EventMetadata[eventData.EventName] = new() { EventId = eventData.EventId, TopicName = topicName };
        this.ExternalTopicUsage[topicName] = true;
    }

    /// <inheritdoc/>
    internal override KernelProcessStepInfo BuildStep(KernelProcessStepStateMetadata? stateMetadata = null)
    {
        KernelProcessProxyStateMetadata proxyMetadata = new()
        {
            Name = this.Name,
            Id = this.Id,
            EventMetadata = this.EventMetadata,
            PublishTopics = this.ExternalTopicUsage.ToList().Select(topic => topic.Key).ToList(),
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
