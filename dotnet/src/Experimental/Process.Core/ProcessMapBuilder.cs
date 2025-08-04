// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality to define a step that maps an enumerable input for parallel processing
/// targeting the provided operation and provides the resulting value as an enumerable parameter
/// with equivalent dimension as the input.
/// </summary>
public sealed class ProcessMapBuilder : ProcessStepBuilder
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessMapBuilder"/> class.
    /// </summary>
    /// <param name="mapOperation">The target of the map operation.  May target a step or process</param>
    internal ProcessMapBuilder(ProcessStepBuilder mapOperation)
        : base($"Map{mapOperation.StepId}", mapOperation.ProcessBuilder)
    {
        this.MapOperation = mapOperation;
    }

    /// <summary>
    /// Version of the map-step, used when saving the state of the step.
    /// </summary>
    public string Version { get; init; } = "v1";

    /// <summary>
    /// Retrieves the target for a given external event. The step associated with the target is the process itself (this).
    /// </summary>
    /// <param name="eventId">The Id of the event</param>
    /// <returns>An instance of <see cref="ProcessFunctionTargetBuilder"/></returns>
    /// <exception cref="KernelException"></exception>
    public ProcessFunctionTargetBuilder WhereInputEventIs(string eventId)
    {
        Verify.NotNullOrWhiteSpace(eventId, nameof(eventId));

        if (this.MapOperation is not ProcessBuilder process)
        {
            throw new KernelException("Map operation is not a process.");
        }

        ProcessFunctionTargetBuilder operationTarget = process.WhereInputEventIs(eventId);

        return operationTarget with { Step = this, TargetEventId = eventId };
    }

    /// <summary>
    /// The map operation that will be executed for each element in the input.
    /// </summary>
    internal ProcessStepBuilder MapOperation { get; }

    /// <inheritdoc/>
    /// <remarks>
    /// Never called as the map is a proxy for the map operation and does not have a function target.
    /// </remarks>
    internal override Dictionary<string, KernelFunctionMetadata> GetFunctionMetadataMap()
    {
        throw new NotImplementedException($"{nameof(ProcessMapBuilder)}.{nameof(GetFunctionMetadataMap)} should never be invoked");
    }

    /// <inheritdoc/>
    internal override KernelProcessFunctionTarget ResolveFunctionTarget(string? functionName, string? parameterName)
    {
        if (this.MapOperation is ProcessBuilder processOperation)
        {
            throw new KernelException($"Map operation is a process.  Use {nameof(ProcessMapBuilder)}.{nameof(WhereInputEventIs)} to resolve target.");
        }

        return this.MapOperation.ResolveFunctionTarget(functionName, parameterName);
    }

    /// <inheritdoc/>
    internal override KernelProcessStepInfo BuildStep(ProcessBuilder processBuilder)
    {
        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());

        // Define the map state
        KernelProcessMapState state = new(this.StepId, this.Version, this.StepId);

        return new KernelProcessMap(state, this.MapOperation.BuildStep(processBuilder), builtEdges);
    }
}
