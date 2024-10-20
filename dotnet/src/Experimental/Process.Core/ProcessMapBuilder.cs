// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel; // %%% BEN: NEGATIVE VALUE IN SEPARATION FROM ABSTRACTIONS _also_ NAMESPACE

/// <summary>
/// Provides functionality to define a step that maps an enumerable input for parallel processing
/// targeting the provided operation and provides the resulting value as an enumerable parameter
/// with equivalent dimension as the input.
/// </summary>
public sealed class ProcessMapBuilder : ProcessStepBuilder
{
    private readonly ProcessStepBuilder _transformStep;

    private string? _targetFunction;
    private string? _targetParameter;
    private ProcessBuilder? _mapProcess;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessMapBuilder"/> class.
    /// </summary>
    /// <param name="transformStep">The step or process that defines the map operation.</param>
    /// <param name="startEventId">The event that singles the map operation.</param>
    /// <param name="completeEventId">The event that signals the completion of "transformStep".</param>
    internal ProcessMapBuilder(ProcessStepBuilder transformStep, string startEventId, string completeEventId)
        : base($"Map{transformStep.Name}")
    {
        this._transformStep = transformStep;
        this.StartEventId = startEventId;
        this.CompleteEventId = completeEventId;
    }

    #region Public Interface

    /// <summary>
    /// The event that singles the map operation.
    /// </summary>
    public string StartEventId { get; }

    /// <summary>
    /// The event that signals the completion of map operation.
    /// </summary>
    public string CompleteEventId { get; }

    /// <summary>
    /// Define the target function for the transform step when more than a single function exists.
    /// </summary>
    /// <param name="functionName">The function to target.</param>
    /// <param name="parameterName">The parameter to target (optional).</param>
    /// <remarks>
    /// No impact when transform step is sub-process.
    /// </remarks>
    public ProcessMapBuilder ForTarget(string functionName, string? parameterName = null) // %%% BEN: REVIEW NAME
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
    internal override void LinkTo(string eventId, ProcessStepEdgeBuilder edgeBuilder)
    {
        // Proxy edge to the map operation.
        this.MapProcess.LinkTo(eventId, edgeBuilder);
    }

    /// <inheritdoc/>
    /// <remarks>
    /// Never called as the map is a proxy for the map operation and does not have a function target.
    /// </remarks>
    internal override KernelProcessFunctionTarget ResolveFunctionTarget(string? functionName, string? parameterName)
    {
        throw new NotImplementedException($"{nameof(ProcessMapBuilder)}.{nameof(ResolveFunctionTarget)} should never be invoked");
    }

    /// <inheritdoc/>
    internal override KernelProcessStepInfo BuildStep()
    {
        if (string.IsNullOrEmpty(this.TargetFunction.ParameterName))
        {
            throw new KernelException("The target function must have a parameter name.");
        }
        KernelProcess map = this.BuildMapProcess();
        KernelProcessMapState state = new(this.Name, this.MapProcess.Id);
        return new KernelProcessMap(state, map, this.CompleteEventId, this.TargetFunction.ParameterName!);
    }

    /// <summary>
    /// Provides the entry-point to the map operation.
    /// </summary>
    internal ProcessFunctionTargetBuilder TargetFunction => this.MapProcess.WhereInputEventIs(this.StartEventId);

    /// <summary>
    /// Safe accessor for the map operation (ensures not-null).
    /// </summary>
    private ProcessBuilder MapProcess => this._mapProcess ??= this.CreateMapProcess();

    private KernelProcess BuildMapProcess()
    {
        // Build the edges first
        var builtEdges = this.MapProcess.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());

        // Build the steps
        var builtSteps = this.MapProcess.Steps.Select(step => step.BuildStep()).ToList();

        // Create the process
        var state = new KernelProcessState(this.Name, this.MapProcess.Id);
        return new KernelProcess(state, builtSteps, builtEdges);
    }

    private ProcessBuilder CreateMapProcess()
    {
        // Build the steps
        ProcessBuilder transformBuilder = new($"One{this._transformStep.Name}");

        var captureStep = transformBuilder.AddStepFromType<MapResultStep>();

        ProcessStepBuilder transformStep;
        if (this._transformStep is ProcessBuilder builder)
        {
            // If external step is process, initialize appropriately
            var transformProcess = transformBuilder.AddStepFromProcess(builder);
            transformBuilder
                .OnInputEvent(this.StartEventId)
                .SendEventTo(transformProcess.WhereInputEventIs(this.StartEventId));
            transformStep = transformProcess;
        }
        else
        {
            // Otherwise initialize as single step
            transformStep = this._transformStep;
            transformBuilder.AddStepFromBuilder(transformStep);
            transformBuilder
                .OnInputEvent(this.StartEventId)
                .SendEventTo(new ProcessFunctionTargetBuilder(transformStep, this._targetFunction, this._targetParameter));
        }

        transformStep
            .OnEvent(this.CompleteEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(captureStep));

        return transformBuilder;
    }
}
