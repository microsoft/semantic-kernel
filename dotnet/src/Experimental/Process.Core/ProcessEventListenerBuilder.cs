// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel.Process;
internal class ProcessEventListenerBuilder : ProcessStepBuilder
{
    public ProcessEventListenerBuilder(List<MessageSourceBuilder> messageSources, string destinationId, string? id = null)
        : base("EventListener", id)
    {
        Verify.NotNullOrEmpty(messageSources, nameof(messageSources));
        Verify.NotNullOrWhiteSpace(destinationId, nameof(destinationId));

        this.MessageSources = messageSources;
        this.DestinationId = destinationId;
    }

    public List<MessageSourceBuilder> MessageSources { get; } = [];

    public string DestinationId { get; } = "";

    internal override KernelProcessStepInfo BuildStep(KernelProcessStepStateMetadata? stateMetadata = null)
    {
        var state = new KernelProcessStepState("EventListener", "V1", id: this.Id);
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());
        var builtSources = this.MessageSources
            .Select(sourceBuilder => new KernelProcessMessageSource(sourceBuilder.MessageType, sourceBuilder.Source.Id))
            .ToList();

        return new KernelProcessEventListener(builtSources, this.DestinationId, state, builtEdges);
    }

    internal override Dictionary<string, KernelFunctionMetadata> GetFunctionMetadataMap()
    {
        throw new NotImplementedException();
    }

    internal override KernelProcessFunctionTarget ResolveFunctionTarget(string? functionName, string? parameterName)
    {
        return new KernelProcessFunctionTarget(this.Id, "HandleMessage");
    }
}
