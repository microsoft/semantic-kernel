// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Process.Internal;

internal static class MapExtensions
{
    public static KernelProcessMap CloneMap(this KernelProcessMap map, ILogger logger)
    {
        KernelProcessMapState newState = new(map.State.StepId, map.State.Version, map.State.RunId!);

        KernelProcessMap copy =
            new(
                newState,
                map.Operation.Clone(logger),
                map.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList()));

        return copy;
    }
}
