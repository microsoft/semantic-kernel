// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Dapr.Actors;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process.Interfaces;
public interface IPubsubMessage: IActor
{
    Task EmitPubsubMessageAsync(ProcessEvent processEvent, DaprPubsubEventData daprDetails);
}
