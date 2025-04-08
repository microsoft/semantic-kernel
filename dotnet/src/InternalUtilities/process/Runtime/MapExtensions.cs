// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel.Process.Runtime;

internal static class MapExtensions
{
    public static (IEnumerable, KernelProcess, string) Initialize(this KernelProcessMap map, ProcessMessage message, ILogger? logger)
    {
        IEnumerable inputValues = message.GetMapInput(logger);
        KernelProcess mapOperation;
        string startEventId;

        if (map.Operation is KernelProcess kernelProcess)
        {
            startEventId = DefineOperationEventId(kernelProcess, message);
            mapOperation = kernelProcess;
        }
        else
        {
            startEventId = ProcessConstants.MapEventId;
            foreach (var kvp in message.Values)
            {
                if (kvp.Value is KernelProcessEventData eventData)
                {
                    message.Values[kvp.Key] = eventData.RepackAsKernelProcessEventDataList().ToArray();
                }
            }

            string? parameterName = message.Values.SingleOrDefault(kvp => IsEqual(inputValues, kvp.Value)).Key;
            string proxyId = Guid.NewGuid().ToString("N");
            mapOperation =
                new KernelProcess(
                    new KernelProcessState($"Map{map.Operation.State.Name}", map.Operation.State.Version, proxyId),
                    [map.Operation],
                    new() { { ProcessConstants.MapEventId, [new KernelProcessEdge(proxyId, new KernelProcessFunctionTarget(map.Operation.State.Id!, message.FunctionName, parameterName))] } });
        }

        return (inputValues, mapOperation, startEventId);
    }

    public static IEnumerable<KernelProcessEventData> RepackAsKernelProcessEventDataList(this KernelProcessEventData eventData)
    {
        var valueData = eventData.ToObject();
        var valueType = valueData!.GetType();

        if (typeof(IEnumerable).IsAssignableFrom(valueType))
        {
            var elementType = valueType.IsArray ? valueType.GetElementType() : valueType.GetGenericArguments().FirstOrDefault();
            if (elementType != null)
            {
                var kernelProcessEventDataList = new List<KernelProcessEventData>();
                foreach (var item in (IEnumerable)valueData)
                {
                    var kernelProcessEventData = KernelProcessEventData.FromObject(item);
                    if (kernelProcessEventData != null)
                    {
                        kernelProcessEventDataList.Add(kernelProcessEventData);
                    }
                    else
                    {
                        throw new KernelException($"Internal Map Error: Collection contains an element that cannot be serialized - {eventData.ObjectType}/{item.GetType().FullName}.");
                    }
                }
                return kernelProcessEventDataList;
            }

            throw new KernelException($"Internal Map Error: Input parameter is not a collection of serializable elements - {eventData.ObjectType}.");
        }

        throw new KernelException($"Internal Map Error: Input parameter is not enumerable - {eventData.ObjectType}.");
    }

    private static IEnumerable GetMapInput(this ProcessMessage message, ILogger? logger)
    {
        if (message.TargetEventData == null)
        {
            throw new KernelException($"Internal Map Error: Input data not present - {message.SourceId}/{message.DestinationId}.").Log(logger);
        }

        Type valueType = message.TargetEventData.GetType();
        object? valueData = message.TargetEventData;
        // Unpacking object to be an array compatible with map step initialization
        if (message.TargetEventData is KernelProcessEventData eventData)
        {
            valueData = eventData.ToObject();
            valueType = valueData!.GetType();

            if (typeof(IEnumerable).IsAssignableFrom(valueType) && valueType.HasElementType)
            {
                var repackedList = eventData.RepackAsKernelProcessEventDataList();
                valueData = repackedList.ToArray();
                valueType = valueData!.GetType();
            }
        }

        return typeof(IEnumerable).IsAssignableFrom(valueType) && valueType.HasElementType ?
            (IEnumerable)valueData! :
            throw new KernelException($"Internal Map Error: Input parameter is not enumerable - {message.SourceId}/{message.DestinationId} [{valueType.FullName}].").Log(logger);
    }

    private static string DefineOperationEventId(KernelProcess mapOperation, ProcessMessage message)
    {
        // Fails when zero or multiple candidate edges exist.  No reason a map-operation should be irrational.
        return
            mapOperation.Edges.SingleOrDefault(kvp => kvp.Value.Any(e => e.OutputTarget.FunctionName == message.FunctionName)).Key ??
            throw new InvalidOperationException($"The map operation does not have an input edge that matches the message destination: {mapOperation.State.Name}/{mapOperation.State.Id}.");
    }

    private static bool IsEqual(IEnumerable targetData, object? possibleValue)
    {
        // Short circuit for null candidate
        if (possibleValue == null)
        {
            return false;
        }

        // Object equality is valid for LocalRuntime
        if (targetData == possibleValue)
        {
            return true;
        }

        // DAPR runtime requires a deeper comparison
        Type candidateType = possibleValue.GetType();

        // Candidate must be enumerable with element type
        if (!typeof(IEnumerable).IsAssignableFrom(candidateType) ||
            !candidateType.HasElementType)
        {
            return false;
        }

        // Types much match
        Type targetType = targetData.GetType();
        if (candidateType != targetData.GetType())
        {
            return false;
        }

        if (targetType.GetElementType() == candidateType.GetElementType())
        {
            // Data has already been serialized to make get this far.
            // Let's use serialization for equality check.
            // Note: We aren't looking for equivalency.  We are testing
            // for a clone of the exact same data instances.
            string targetDataJson = JsonSerializer.Serialize(targetData);
            string possibleValueJson = JsonSerializer.Serialize(possibleValue);
            return string.Equals(targetDataJson, possibleValueJson, StringComparison.Ordinal);
        }

        return false;
    }
}
