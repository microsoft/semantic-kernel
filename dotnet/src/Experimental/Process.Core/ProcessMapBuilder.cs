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
    private readonly Func<ProcessBuilder> _mapProcessFactory;

    private string? _targetFunction;
    private string? _targetParameter;
    private ProcessBuilder? _mapProcess;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessMapBuilder"/> class.
    /// </summary>
    /// <param name="mapStep">The step or process that defines the map operation.</param>
    internal ProcessMapBuilder(ProcessStepBuilder mapStep)
        : base($"Map{mapStep.Name}")
    {
        this._mapProcessFactory = () => this.CreateMapProcess(mapStep);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessBuilder"/> class.
    /// </summary>
    /// <param name="mapProcess">The step or process that defines the map operation.</param>
    /// <param name="eventId">// %%% COMMENT</param>
    internal ProcessMapBuilder(ProcessBuilder mapProcess, string eventId)
        : base($"Map{mapProcess.Name}")
    {
        this._mapProcessFactory = () => this.CreateMapProcess(mapProcess, eventId);
    }

    #region Public Interface

    /// <summary>
    /// Define the target function for the transform step when more than a single function exists.
    /// </summary>
    /// <param name="functionName">The function to target.</param>
    /// <param name="parameterName">The parameter to target (optional).</param>
    /// <remarks>
    /// No impact when transform step is sub-process.
    /// </remarks>
    public ProcessMapBuilder ForTarget(string functionName, string? parameterName = null)
    {
        this._targetFunction = functionName;
        this._targetParameter = parameterName;

        return this;
    }

    #endregion

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
        return new KernelProcessFunctionTarget(this.Id!, this.TargetFunction.FunctionName, this.TargetFunction.ParameterName);
    }

    /// <inheritdoc/>
    internal override KernelProcessStepInfo BuildStep()
    {
        if (string.IsNullOrEmpty(this.TargetFunction.ParameterName))
        {
            throw new KernelException("The target function must have a parameter name.");
        }

        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());
        ProcessBuilder mapProcess = this.MapProcess;

        KernelProcessMapState state = new(this.Name, this.Id);
        return new KernelProcessMap(state, mapProcess.Build(), this.TargetFunction.ParameterName!, builtEdges);
    }

    /// <summary>
    /// Provides the entry-point to the map operation.
    /// </summary>
    internal ProcessFunctionTargetBuilder TargetFunction => this.MapProcess.WhereInputEventIs(KernelProcessMap.MapEventId);

    /// <summary>
    /// Safe accessor for the map operation (ensures not-null).
    /// </summary>
    private ProcessBuilder MapProcess => this._mapProcess ??= this._mapProcessFactory();

    private ProcessBuilder CreateMapProcess(ProcessBuilder mapProcess, string eventId)
    {
        ProcessBuilder transformBuilder = new($"One{mapProcess.Name}");

        var transformProcess = transformBuilder.AddStepFromProcess(mapProcess);
        transformBuilder
            .OnInputEvent(KernelProcessMap.MapEventId)
            .SendEventTo(transformProcess.WhereInputEventIs(eventId));

        return transformBuilder;
    }

    private ProcessBuilder CreateMapProcess(ProcessStepBuilder mapStep)
    {
        ProcessBuilder transformBuilder = new($"One{mapStep.Name}");

        transformBuilder.AddStepFromBuilder(mapStep);
        transformBuilder
            .OnInputEvent(KernelProcessMap.MapEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(mapStep, this._targetFunction, this._targetParameter));

        return transformBuilder;
    }
}
