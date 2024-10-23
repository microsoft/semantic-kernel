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
    private readonly ProcessStepBuilder _transformStep;

    private ProcessStepBuilder? _mapOperation;

    private string? _targetFunction;
    private string? _targetParameter;
    private ProcessBuilder? _mapProcess;
    private readonly List<string> _proxyEvents = [];

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessMapBuilder"/> class.
    /// </summary>
    /// <param name="transformStep">The step or process that defines the map operation.</param>
    /// <param name="completeEventId">The event that signals the completion of "transformStep".</param>
    internal ProcessMapBuilder(ProcessStepBuilder transformStep, string completeEventId)
        : base($"Map{transformStep.Name}")
    {
        this._transformStep = transformStep;
        this.CompleteEventId = completeEventId;
    }

    #region Public Interface

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
    internal override void LinkTo(string eventId, ProcessStepEdgeBuilder edgeBuilder)
    {
        // Proxy edge to the map operation.
        //this.MapProcess.LinkTo(eventId, edgeBuilder);
        string rawEventId = eventId.Split('.').Last(); // %%% RAW
        this._proxyEvents.Add(rawEventId);
        base.LinkTo(eventId, edgeBuilder);
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

        // Build the edges first
        //var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());
        //Console.WriteLine($"\tMAP BUILDER: {this.Id}");
        //Console.WriteLine($"\tMAP PROCESS: {this.MapProcess.Id}");
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());
        //Console.WriteLine($"\tMAP EDGE KEY: {builtEdges.First().Key} {builtEdges.First().Value.First().OutputTarget.TargetEventId}");
        //Console.WriteLine($"\tMAP SOURCE STEP: {builtEdges.First().Value.First().SourceStepId}");
        //Console.WriteLine($"\tMAP STEP ID: {builtEdges.First().Value.First().OutputTarget.StepId}");
        //Console.WriteLine($"\tMAP TARGET ID: {builtEdges.First().Value.First().OutputTarget.TargetEventId}");
        //Console.WriteLine($"\tMAP TARGET ID: {builtEdges.First().Value.First().OutputTarget.TargetEventId}");
        var mapEdges = builtEdges.ToDictionary(kvp => kvp.Key.Replace(this.Id!, this.MapProcess.Id), kvp => kvp.Value.Select(e => new KernelProcessEdge(this.MapProcess.Id!, e.OutputTarget)).ToList());

        ProcessBuilder mapProcess = this.MapProcess;
        var captureStep = mapProcess.AddStepFromType<MapResultStep>();
        string completeEvent = this._proxyEvents.Single();// %%% HACK
        this._mapOperation! // %%% NULLABLE
            .OnEvent(completeEvent) // %%% HACK
            .SendEventTo(new ProcessFunctionTargetBuilder(captureStep));

        KernelProcessMapState state = new(this.Name, mapProcess.Id);
        return new KernelProcessMap(state, mapProcess.Build(), completeEvent, this.TargetFunction.ParameterName!, mapEdges);
    }

    /// <summary>
    /// Provides the entry-point to the map operation.
    /// </summary>
    internal ProcessFunctionTargetBuilder TargetFunction => this.MapProcess.WhereInputEventIs(KernelProcessMap.MapEventId);

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

        ProcessStepBuilder transformStep;
        if (this._transformStep is ProcessBuilder builder)
        {
            // If external step is process, initialize appropriately
            var transformProcess = transformBuilder.AddStepFromProcess(builder);
            transformBuilder
                .OnInputEvent(KernelProcessMap.MapEventId)
                .SendEventTo(transformProcess.WhereInputEventIs("BROKE")); // %%% VALIDATE WITH SUBPROCESS - FUNCTION TARGET
            transformStep = transformProcess;
        }
        else
        {
            // Otherwise initialize as single step
            transformStep = this._transformStep;
            transformBuilder.AddStepFromBuilder(transformStep);
            transformBuilder
                .OnInputEvent(KernelProcessMap.MapEventId)
                .SendEventTo(new ProcessFunctionTargetBuilder(transformStep, this._targetFunction, this._targetParameter));
        }

        this._mapOperation = transformStep;
        //var captureStep = transformBuilder.AddStepFromType<MapResultStep>();
        //transformStep // %%% DEFER TO FINAL BUILD
        //    .OnEvent(this.CompleteEventId)
        //    .SendEventTo(new ProcessFunctionTargetBuilder(captureStep));

        return transformBuilder;
    }
}
