// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Linq;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Process.Runtime;

internal static class MapExtensions
{
    public static IEnumerable GetMapInput(this ProcessMessage message, string parameterName, ILogger logger)
    {
        //if (string.IsNullOrWhiteSpace(message.TargetEventId))
        //{
        //    string errorMessage = "Internal Map Error: The target event id must be specified when sending a message to a step.";
        //    logger.LogError("{ErrorMessage}", errorMessage);
        //    throw new KernelException(errorMessage);
        //}

        if (!message.Values.TryGetValue(parameterName, out object? values))
        {
            string errorMessage = $"Internal Map Error: Input parameter not present - {parameterName}";
            logger.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException($"Internal Map Error: Input parameter not present - {parameterName}");
        }

        Type valueType = values!.GetType();
        if (!typeof(IEnumerable).IsAssignableFrom(valueType) || !valueType.HasElementType)
        {
            string errorMessage = $"Internal Map Error: Input parameter is not enumerable - {parameterName} [{valueType.FullName}]";
            logger.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException($"Internal Map Error: Input parameter is not enumerable - {parameterName} [{valueType.FullName}]");
        }

        return (IEnumerable)values;
    }

    public static KernelProcess CloneProcess(this KernelProcess process, ILogger logger)
    {
        KernelProcess copy =
            new(
                new KernelProcessState(process.State.Name, process.State.Id),
                process.Steps.Select(s => s.Clone(logger)).ToArray(),
                process.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList()));

        return copy;
    }
}
