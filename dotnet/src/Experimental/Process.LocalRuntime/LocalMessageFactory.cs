// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// A factory class for creating <see cref="LocalMessage"/> instances.
/// </summary>
internal static class LocalMessageFactory
{
    /// <summary>
    /// Creates a new <see cref="LocalMessage"/> instance from a <see cref="KernelProcessEdge"/> and a data object.
    /// </summary>
    /// <param name="edge">An instance of <see cref="KernelProcessEdge"/></param>
    /// <param name="data">A data object.</param>
    /// <returns>An instance of <see cref="LocalMessage"/></returns>
    internal static LocalMessage CreateFromEdge(KernelProcessEdge edge, object? data)
    {
        var target = edge.OutputTarget;
        Dictionary<string, object?> parameterValue = [];
        if (!string.IsNullOrWhiteSpace(target.ParameterName))
        {
            parameterValue.Add(target.ParameterName!, data);
        }

        LocalMessage newMessage = new(edge.SourceStepId, target.StepId, target.FunctionName, parameterValue)
        {
            TargetEventId = target.TargetEventId,
            TargetEventData = data
        };

        return newMessage;
    }
}
