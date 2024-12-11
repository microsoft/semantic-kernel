// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Dapr.Actors.Runtime;
using Dapr.Client;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Interfaces;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Contains information about a Step in a Dapr Process including it's state and edges.
/// </summary>
[KnownType(typeof(KernelProcessEdge))]
[KnownType(typeof(KernelProcessStepState))]
[KnownType(typeof(DaprProcessInfo))]
[KnownType(typeof(DaprMapInfo))]
[JsonDerivedType(typeof(DaprProcessInfo))]
[JsonDerivedType(typeof(DaprMapInfo))]
public class PubsubMessageActor : Actor, IPubsubMessage
{
    private readonly DaprClient _daprClient;

    public PubsubMessageActor(ActorHost host, DaprClient daprClient) : base(host)
    {
        this._daprClient = daprClient;
    }

    public async Task EmitPubsubMessageAsync(ProcessEvent processEvent, DaprPubsubEventData daprDetails)
    {
        Verify.NotNullOrWhiteSpace(daprDetails.PubsubName);
        Verify.NotNullOrWhiteSpace(daprDetails.TopicName);

        await this._daprClient.PublishEventAsync(daprDetails.PubsubName, daprDetails.TopicName, processEvent).ConfigureAwait(true);
    }
}
