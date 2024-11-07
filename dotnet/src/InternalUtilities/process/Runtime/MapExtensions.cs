// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel.Process.Runtime;

internal static class MapExtensions
{
    public static IEnumerable GetMapInput(this ProcessMessage message, ILogger? logger)
    {
        if (message.TargetEventData == null)
        {
            throw new KernelException($"Internal Map Error: Input data not present - {message.SourceId}/{message.DestinationId}.").Log(logger);
        }

        Type valueType = message.TargetEventData.GetType();
        if (!typeof(IEnumerable).IsAssignableFrom(valueType) || !valueType.HasElementType)
        {
            throw new KernelException($"Internal Map Error: Input parameter is not enumerable - {message.SourceId}/{message.DestinationId} [{valueType.FullName}].").Log(logger);
        }

        return (IEnumerable)message.TargetEventData;
    }
}
