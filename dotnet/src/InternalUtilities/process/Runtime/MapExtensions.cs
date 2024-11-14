// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections;
using System.Linq;
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

    public static KernelProcess CreateProxyOperation(this KernelProcessMap map, ProcessMessage message)
    {
        if (map.Operation is KernelProcess kernelProcess)
        {
            return kernelProcess;
        }

        string? parameterName = message.Values.SingleOrDefault(kvp => kvp.Value == message.TargetEventData).Key;
        string proxyId = Guid.NewGuid().ToString("N");
        return
            new KernelProcess(
                new KernelProcessState($"Map{map.Operation.State.Name}", map.Operation.State.Version, proxyId),
                [map.Operation],
                new() { { ProcessConstants.MapEventId, [new KernelProcessEdge(proxyId, new KernelProcessFunctionTarget(map.Operation.State.Id!, message.FunctionName, parameterName))] } });
    }

    public static string DefineOperationEventId(this KernelProcessMap map, ProcessMessage message)
    {
        if (map.Operation is KernelProcess kernelProcess)
        {
            foreach (var edge in kernelProcess.Edges)
            {
                if (edge.Value.Any(e => e.OutputTarget.FunctionName == message.FunctionName)) // %%% SUFFICIENT ???
                {
                    return edge.Key;
                }
            }

            throw new InvalidOperationException($"The map operation does not have an input edge that matches the message destination: {map.State.Name}/{map.State.Id}.");
        }

        return ProcessConstants.MapEventId;
    }
}
