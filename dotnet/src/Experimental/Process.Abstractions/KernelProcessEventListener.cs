// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Process;
public record KernelProcessEventListener : KernelProcessStepInfo
{
    public KernelProcessEventListener(List<KernelProcessMessageSource> messageSources, string destinationStepId, Type innerStepType, KernelProcessStepState state, Dictionary<string, List<KernelProcessEdge>> edges) : base(typeof(KernelProcessEventListener), state, edges)
    {
        Verify.NotNullOrEmpty(messageSources, nameof(messageSources));
        Verify.NotNullOrWhiteSpace(destinationStepId, nameof(destinationStepId));

        this.MessageSources = messageSources;
        this.DestinationStepId = destinationStepId;
    }

    public List<KernelProcessMessageSource> MessageSources { get; }

    public string DestinationStepId { get; }
}
