// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality for incrementally defining a process.
/// </summary>
public sealed class ProcessBuilder : ProcessStepBuilder
{
    private readonly List<ProcessStepBuilder> _steps;
    private readonly List<ProcessStepBuilder> _entrySteps;
    private readonly Dictionary<string, ProcessStepBuilder> _stepsMap;

    /// <summary>
    /// Used to resolve the target function and parameter for a given optional function name and parameter name.
    /// This is used to simplify the process of creating a <see cref="KernelProcessFunctionTarget"/> by making it possible
    /// to infer the function and/or parameter names from the function metadata if only one option exists.
    /// </summary>
    /// <param name="functionName">The name of the function. May be null if only one function exists on the step.</param>
    /// <param name="parameterName">The name of the parameter. May be null if only one parameter exists on the function.</param>
    /// <returns>A valid instance of <see cref="KernelProcessFunctionTarget"/> for this step.</returns>
    /// <exception cref="InvalidOperationException"></exception>
    internal override KernelProcessFunctionTarget ResolveFunctionTarget(string? functionName, string? parameterName)
    {
        // Try to resolve the function target on each of the registered entry points.
        var targets = new List<KernelProcessFunctionTarget>();
        foreach (var step in this._entrySteps)
        {
            try
            {
                targets.Add(step.ResolveFunctionTarget(functionName, parameterName));
            }
            catch (KernelException)
            {
                // If the function is not found on the source step, then we can ignore it.
            }
        }

        // If no targets were found or if multiple targets were found, throw an exception.
        if (targets.Count == 0)
        {
            throw new InvalidOperationException($"No targets found for the specified function and parameter '{functionName}.{parameterName}'.");
        }
        else if (targets.Count > 1)
        {
            throw new InvalidOperationException($"Multiple targets found for the specified function and parameter '{functionName}.{parameterName}'.");
        }

        return targets[0];
    }

    /// <inheritdoc/>
    internal override void LinkTo(string eventId, ProcessStepEdgeBuilder edgeBuilder)
    {
        // Keep track of the entry point steps
        this._entrySteps.Add(edgeBuilder.Source);
        base.LinkTo(eventId, edgeBuilder);
    }

    /// <inheritdoc/>
    internal override string GetScopedEventId(string eventId)
    {
        // The event id is scoped to the process name
        return $"{this.Name}.{eventId}";
    }

    /// <inheritdoc/>
    internal override Dictionary<string, KernelFunctionMetadata> GetFunctionMetadataMap()
    {
        // The process has no kernel functions of its own, but it does expose the functions from its entry steps.
        // Merge the function metadata map from each of the entry steps.
        return this._entrySteps.SelectMany(step => step.GetFunctionMetadataMap())
                               .ToDictionary(pair => pair.Key, pair => pair.Value);
    }

    /// <summary>
    /// Builds the step.
    /// </summary>
    /// <returns></returns>
    internal override KernelProcessStepInfo BuildStep()
    {
        // The process is a step so we can return the step info directly.
        return this.Build();
    }

    #region Public Interface

    /// <summary>
    /// A read-only collection of steps in the process.
    /// </summary>
    public IReadOnlyList<ProcessStepBuilder> Steps => this._steps.AsReadOnly();

    /// <summary>
    /// Adds a step to the process.
    /// </summary>
    /// <typeparam name="TStep">The step Type.</typeparam>
    /// <param name="name">The name of the step. This parameter is optional.</param>
    /// <returns>An instance of <see cref="ProcessStepBuilder"/></returns>
    public ProcessStepBuilder AddStepFromType<TStep>(string? name = null) where TStep : KernelProcessStep
    {
        var stepBuilder = new ProcessStepBuilder<TStep>(name);
        this._steps.Add(stepBuilder);
        this._stepsMap[stepBuilder.Name] = stepBuilder;

        return stepBuilder;
    }

    /// <summary>
    /// Adds a sub process to the process.
    /// </summary>
    /// <param name="kernelProcess">The process to add as a step.</param>
    /// <returns>An instance of <see cref="ProcessStepBuilder"/></returns>
    public ProcessStepBuilder AddStepFromProcess(ProcessBuilder kernelProcess)
    {
        // TODO: Could this method be converted to an "AddStepFromObject" method takes an
        // instance of ProcessStepBase and adds it to the process?
        // This would work for processes.
        // This would benefit steps because the initial value of state could be captured?

        this._steps.Add(kernelProcess);
        this._stepsMap[kernelProcess.Name] = kernelProcess;
        return kernelProcess;
    }

    /// <summary>
    /// Provides an instance of <see cref="ProcessStepEdgeBuilder"/> for defining an edge to a
    /// step inside the process for a given external event.
    /// </summary>
    /// <param name="eventId">The Id of the external event.</param>
    /// <returns>An instance of <see cref="ProcessStepEdgeBuilder"/></returns>
    public ProcessEdgeBuilder OnExternalEvent(string eventId)
    {
        return new ProcessEdgeBuilder(this, eventId);
    }

    /// <summary>
    /// Builds the process.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    /// <exception cref="NotImplementedException"></exception>
    public KernelProcess Build()
    {
        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());

        // Build the steps
        var builtSteps = this._steps.Select(step => step.BuildStep()).ToList();

        // Create the process
        var state = new KernelProcessState(this.Name);
        var process = new KernelProcess(state, builtSteps, builtEdges);
        return process;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessBuilder"/> class.
    /// </summary>
    /// <param name="name">The name of the process. This is required.</param>
    public ProcessBuilder(string name)
        : base(name)
    {
        this._steps = [];
        this._entrySteps = [];
        this._stepsMap = [];
    }

    #endregion
}
