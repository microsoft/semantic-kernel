// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Process.Models;

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
        : base($"Map{mapOperation.Name}")
    {
        this.MapOperation = mapOperation;
    }

    /// <summary>
    /// Version of the map-step, used when saving the state of the step.
    /// </summary>
    public string Version { get; init; } = "v1";

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
            KernelProcessFunctionTarget? inputTarget = null;
            foreach (var step in processOperation.Steps)
            {
                try
                {
                    inputTarget = step.ResolveFunctionTarget(functionName, parameterName);
                }
                catch (KernelException)
                {
                    // Function not found, try the next step
                }
            }

            if (inputTarget == null)
            {
                throw new KernelException($"Failed to resolve function target for map-step - {this.Name}: Function - {functionName ?? "any"} / Parameter - {parameterName ?? "any"}");
            }

            //return processOperation.WhereInputEventIs(ProcessConstants.MapEventId); // %%% DON'T KNOW EVENTID
            return inputTarget;
        }

        return this.MapOperation.ResolveFunctionTarget(functionName, parameterName);
    }

    /// <inheritdoc/>
    internal override KernelProcessStepInfo BuildStep(KernelProcessStepStateMetadata? stateMetadata = null)
    {
        KernelProcessMapStateMetadata? mapMetadata = stateMetadata as KernelProcessMapStateMetadata;

        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());

        // Define the map state
        KernelProcessMapState state = new(this.Name, this.Version, this.Id);

        return new KernelProcessMap(state, this.MapOperation.BuildStep(mapMetadata?.OperationState), builtEdges);
    }
}
