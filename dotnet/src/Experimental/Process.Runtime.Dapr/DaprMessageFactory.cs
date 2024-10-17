// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A factory class for creating <see cref="DaprMessage"/> instances.
/// </summary>
internal static class DaprMessageFactory
{
    /// <summary>
    /// Creates a new <see cref="DaprMessage"/> instance from a <see cref="KernelProcessEdge"/> and a data object.
    /// </summary>
    /// <param name="edge">An instance of <see cref="KernelProcessEdge"/></param>
    /// <param name="data">A data object.</param>
    /// <returns>An instance of <see cref="DaprMessage"/></returns>
    internal static DaprMessage CreateFromEdge(KernelProcessEdge edge, object? data)
    {
        var target = edge.OutputTarget;
        Dictionary<string, object?> parameterValue = [];
        if (!string.IsNullOrWhiteSpace(target.ParameterName))
        {
            parameterValue.Add(target.ParameterName!, data);
        }

        DaprMessage newMessage = new()
        {
            SourceId = edge.SourceStepId,
            DestinationId = target.StepId,
            FunctionName = target.FunctionName,
            Values = parameterValue,
            TargetEventId = target.TargetEventId,
            TargetEventData = data
        };

        return newMessage;
    }
}
