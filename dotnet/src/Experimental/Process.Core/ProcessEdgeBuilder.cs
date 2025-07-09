// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality for incrementally defining a process edge.
/// </summary>
public sealed class ProcessEdgeBuilder : ProcessStepEdgeBuilder
{
    /// <summary>
    /// The source step of the edge.
    /// </summary>
    internal new ProcessBuilder Source { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessEdgeBuilder"/> class.
    /// </summary>
    /// <param name="source">The source step.</param>
    /// <param name="eventId">The Id of the event.</param>
    internal ProcessEdgeBuilder(ProcessBuilder source, string eventId) : base(source, eventId, eventId)
    {
        this.Source = source;
    }

    /// <summary>
    /// Sends the output of the source step to the specified target when the associated event fires.
    /// </summary>
    public ProcessEdgeBuilder SendEventTo(ProcessFunctionTargetBuilder target)
    {
        if (!target.Step.InputParametersTypeData.TryGetValue(target.FunctionName, out var targetFunctionParameters))
        {
            throw new InvalidOperationException($"Target function {target.FunctionName} not found");
        }

        KernelEventTypeData targetParameterData = new();
        if (target.ParameterName != null)
        {
            if (!targetFunctionParameters.TryGetValue(target.ParameterName, out var parameterData))
            {
                throw new InvalidOperationException($"Target function {target.FunctionName} has no parameter named {target.ParameterName}");
            }

            targetParameterData = parameterData;
        }
        this.Source.AddInputEventToProcess(this.EventData.EventId, targetParameterData);

        return this.SendEventTo_Int(target as ProcessTargetBuilder);
    }

    public ProcessStepEdgeBuilder SendEventTo<TParameterDataType>(ProcessFunctionTargetBuilder target) where TParameterDataType : class, new()
    {
        if (!target.Step.InputParametersTypeData.TryGetValue(target.FunctionName, out var targetFunctionInput))
        {
            throw new InvalidOperationException($"Step {target.Step.StepId} does not have input parameter schemas for function {target.FunctionName}");
        }

        var matchingParameterTypeValues = targetFunctionInput.Where(p => p.Value.DataType == typeof(TParameterDataType)).ToList();
        if (matchingParameterTypeValues.Count == 0)
        {
            throw new InvalidOperationException($"No matching parameters of type {typeof(TParameterDataType).Name} found for function {target.FunctionName} in step {target.Step.StepId}.");
        }

        KernelEventTypeData targetParameterData = matchingParameterTypeValues.FirstOrDefault().Value;

        if (targetParameterData == null)
        {
            throw new InvalidOperationException("No matching parameters found.");
        }

        this.Source.AddInputEventToProcess(this.EventData.EventId, targetParameterData);

        return this.SendEventTo(target);
    }

    /// <summary>
    /// Sends the output of the source step to the specified target when the associated event fires.
    /// </summary>
    public new ProcessEdgeBuilder SendEventTo(ProcessTargetBuilder target)
    {
        return this.SendEventTo_Int(target as ProcessTargetBuilder);
    }

    /// <summary>
    /// Sends the output of the source step to the specified target when the associated event fires.
    /// </summary>
    internal ProcessEdgeBuilder SendEventTo_Int(ProcessTargetBuilder target)
    {
        if (this.Target is not null)
        {
            throw new InvalidOperationException("An output target has already been set.");
        }

        this.Target = target;
        ProcessStepEdgeBuilder edgeBuilder = new(this.Source, this.EventData.EventId, this.EventData.EventId) { Target = this.Target };
        this.Source.LinkTo(this.EventData.EventId, edgeBuilder);

        return new ProcessEdgeBuilder(this.Source, this.EventData.EventId);
    }
}
