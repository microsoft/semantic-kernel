// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel.Process;
internal class ProcessEventListenerBuilder : ProcessStepBuilder
{
    public ProcessEventListenerBuilder(List<MessageSource> messageSources, string destinationId, string? id = null)
        : base("EventListener", id)
    {
        Verify.NotNullOrEmpty(messageSources, nameof(messageSources));
        Verify.NotNullOrWhiteSpace(destinationId, nameof(destinationId));

        this.MessageSources = messageSources;
        this.DestinationId = destinationId;
    }

    public List<MessageSource> MessageSources { get; } = [];

    public string DestinationId { get; } = "";

    internal override KernelProcessStepInfo BuildStep(KernelProcessStepStateMetadata? stateMetadata = null)
    {
        throw new NotImplementedException();
    }

    internal override Dictionary<string, KernelFunctionMetadata> GetFunctionMetadataMap()
    {
        throw new NotImplementedException();
    }
}
