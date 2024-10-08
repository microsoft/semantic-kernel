// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;
public interface IExternalEventQueue : IActor
{
    Task EnqueueAsync(KernelProcessEvent externalEvent);

    Task<List<KernelProcessEvent>> DequeueAllAsync();
}
