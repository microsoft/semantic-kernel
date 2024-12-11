// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel.Process;

[KnownType(typeof(DaprPubsubEventData))]
public record DaprPubsubEventData
{
    public required string PubsubName { get; init; }

    public required string ProcessEventName { get; init; }

    public required string TopicName { get; init; }
}
