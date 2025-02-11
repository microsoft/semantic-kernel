// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality to allow emitting external messages from withing the SK
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
    internal Dictionary<string, string> EventTopicMap { get; } = [];
    internal Dictionary<string, string> EventDataMap { get; } = [];

    internal ProcessFunctionTargetBuilder GetExternalFunctionTargetBuilder()
    {
        // TODO: change to use this -> assuming this = KernelStep<ProxyStep>
        return new ProcessFunctionTargetBuilder(this, functionName: KernelProxyStep.Functions.EmitExternalEvent);
    }

    internal ProcessFunctionTargetBuilder GetInternalFunctionTargetBuilder()
    {
        // TODO: change to use this -> assuming this = KernelStep<ProxyStep>
        return new ProcessFunctionTargetBuilder(this, functionName: KernelProxyStep.Functions.EmitInternalEvent);
    }

    internal void LinkTopicToStepEdgeInfo(string topicName, ProcessStepBuilder sourceStep, ProcessEventData eventData)
    {
        // TODO-estenori: these 2 could potentially be merged into 1 dict later
        // maybe sourceStep is not needed? need to check
        this.EventTopicMap[eventData.EventName] = topicName;
        this.EventDataMap[eventData.EventName] = eventData.EventId;

        this.ExternalTopicUsage[topicName] = true;
    }

    /// <inheritdoc/>
    internal override KernelProcessStepInfo BuildStep(KernelProcessStepStateMetadata? stateMetadata = null)
    {
        KernelProcessProxyStateMetadata? proxyMetada = new()
        {
            Name = this.Name,
            Id = this.Id,
            EventPublishTopicMap = this.EventTopicMap,
            EventDataMap = this.EventDataMap,
            PublishTopics = this.ExternalTopicUsage.ToList().Select(topic => topic.Key).ToList()
        };

        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());

        KernelProcessStepState state = new(this.Name, this.Version, this.Id);

        return new KernelProcessProxy(state, builtEdges)
        {
            ProxyMetadata = proxyMetada
        };
    }
}
