// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Linq;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Process.Runtime;

internal static class MapExtensions
{
    public static IEnumerable GetMapInput(this ProcessMessage message, ILogger logger)
    {
        if (message.TargetEventData == null)
        {
            string errorMessage = $"Internal Map Error: Input data not present - {message.SourceId}/{message.DestinationId}.";
            logger.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException(errorMessage);
        }

        Type valueType = message.TargetEventData.GetType();
        if (!typeof(IEnumerable).IsAssignableFrom(valueType) || !valueType.HasElementType)
        {
            string errorMessage = $"Internal Map Error: Input parameter is not enumerable - {message.SourceId}/{message.DestinationId} [{valueType.FullName}].";
            logger.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException(errorMessage);
        }

        return (IEnumerable)message.TargetEventData;
    }

    public static KernelProcessMap CloneMap(this KernelProcessMap map, ILogger logger)
    {
        KernelProcessMapState newState = new(map.State.Name, map.State.Id!);

        KernelProcessMap copy =
            new(
                newState,
                map.Operation.CloneProcess(logger),
                map.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList()));

        return copy;
    }
}
