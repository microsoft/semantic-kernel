// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel;

/// <summary>
/// %%% COMMENT
/// </summary>
public abstract class ProcessMapBuilder : ProcessStepBuilder
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    protected readonly ProcessStepBuilder _transformStep;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessMapBuilder{TValue}"/> class.
    /// </summary>
    /// <param name="transformStep">// %%% COMMENT</param>
    /// <param name="startEventId">// %%% COMMENT</param>
    /// <param name="completeEventId">// %%% COMMENT</param>
    internal ProcessMapBuilder(ProcessStepBuilder transformStep, string startEventId, string completeEventId)
        : base(transformStep.Name)
    {
        this._transformStep = transformStep;
        this.StartEventId = startEventId;
        this.CompleteEventId = completeEventId;
        this.TargetFunction = new ProcessFunctionTargetBuilder(this) { TargetEventId = startEventId };
    }

    /// <inheritdoc/>
    internal override Dictionary<string, KernelFunctionMetadata> GetFunctionMetadataMap()
    {
        IReadOnlyList<ProcessStepBuilder> innerSteps = this._transformStep is ProcessBuilder process ? process.Steps : [this._transformStep];

        return
            innerSteps
                .SelectMany(step => step.GetFunctionMetadataMap())
                //.Union(KernelPluginFactory.CreateFromType<KernelProcessMap>().ToDictionary(f => f.Name, f => f.Metadata))  // %%% NEEDED ???
                .ToDictionary(pair => pair.Key, pair => pair.Value);
    }

    #region Public Interface

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public string StartEventId { get; }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public string CompleteEventId { get; }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public ProcessFunctionTargetBuilder TargetFunction { get; }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public abstract ProcessMapBuilder WithResultType<TResult>();

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public abstract ProcessMapBuilder WithResultType(Type resultType);

    #endregion
}

/// <summary>
/// %%% COMMENT
/// </summary>
public sealed class ProcessMapBuilder<TValue> : ProcessMapBuilder
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessMapBuilder{TValue}"/> class.
    /// </summary>
    /// <param name="transformStep">// %%% COMMENT</param>
    /// <param name="startEventId">// %%% COMMENT</param>
    /// <param name="completeEventId">// %%% COMMENT</param>
    internal ProcessMapBuilder(ProcessStepBuilder transformStep, string startEventId, string completeEventId)
        : base(transformStep, startEventId, completeEventId)
    {
        this.ResultType = typeof(TValue);
    }

    /// <summary>
    /// Builds the step.
    /// </summary>
    /// <returns></returns>
    internal override KernelProcessStepInfo BuildStep()
    {
        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());

        // Build the steps
        ProcessBuilder mapBuilder = new(this.Name);

        var captureStep = mapBuilder.AddStepFromType<MapResultStep<TValue>>();

        ProcessStepBuilder externalStep;
        if (this._transformStep is ProcessBuilder builder)
        {
            // If external step is process, initialize appropriately
            var externalProcess = mapBuilder.AddStepFromProcess(builder);
            mapBuilder
                .OnInputEvent(this.StartEventId)
                .SendEventTo(externalProcess);
            externalStep = externalProcess;
        }
        else
        {
            // Otherwise treat as step
            externalStep = this._transformStep;
            mapBuilder
                .OnInputEvent(this.StartEventId)
                .SendEventTo(new ProcessFunctionTargetBuilder(externalStep));
        }

        externalStep
            .OnEvent(this.CompleteEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(captureStep));

        // Create the map
        KernelProcessMap map = new(new KernelProcessStepState(this.Name, this.Id), mapBuilder.Build(), builtEdges);

        return map;
    }

    #region Public Interface

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public Type ResultType { get; private set; }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public override ProcessMapBuilder WithResultType<TResult>()
    {
        this.ResultType = typeof(TResult);
        return this;
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public override ProcessMapBuilder WithResultType(Type resultType)
    {
        this.ResultType = resultType;
        return this;
    }

    #endregion
}
