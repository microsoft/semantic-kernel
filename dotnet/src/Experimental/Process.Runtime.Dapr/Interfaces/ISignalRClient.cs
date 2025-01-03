// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel.Process.Interfaces;
public interface ISignalRClient: IActor
{
    Task PublishMessageExternallyAsync(string topic, object? data);
}
