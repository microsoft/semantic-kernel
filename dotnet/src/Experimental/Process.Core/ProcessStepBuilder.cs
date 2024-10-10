﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Process;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An abstract class that provides functionality for incrementally defining a process step and linking it to other steps within a Process.
/// </summary>
public abstract class ProcessStepBuilder
{
    #region Public Interface

    /// <summary>
    /// The unique identifier for the step. This may be null until the step is run within a process.
    /// </summary>
    public string? Id { get; }

    /// <summary>
    /// The name of the step. This is intended to be a human-readable name and is not required to be unique.
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// Define the behavior of the step when the event with the specified Id is fired.
    /// </summary>
    /// <param name="eventId">The Id of the event of interest.</param>
    /// <returns>An instance of <see cref="ProcessStepEdgeBuilder"/>.</returns>
    public virtual ProcessStepEdgeBuilder OnEvent(string eventId)
    {
        // scope the event to this instance of this step
        var scopedEventId = this.GetScopedEventId(eventId);
        return new ProcessStepEdgeBuilder(this, scopedEventId);
    }

    /// <summary>
    /// Define the behavior of the step when the specified function has been successfully invoked.
    /// </summary>
    /// <param name="functionName">The name of the function of interest.</param>
    /// <returns>An instance of <see cref="ProcessStepEdgeBuilder"/>.</returns>
    public virtual ProcessStepEdgeBuilder OnFunctionResult(string functionName)
    {
        return this.OnEvent($"{functionName}.OnResult");
    }

    /// <summary>
    /// Define the behavior of the step when the specified function has thrown an exception.
    /// </summary>
    /// <param name="functionName">The name of the function of interest.</param>
    /// <returns>An instance of <see cref="ProcessStepEdgeBuilder"/>.</returns>
    public ProcessStepEdgeBuilder OnFunctionError(string functionName)
    {
        return this.OnEvent($"{functionName}.OnError");
    }

    #endregion

    /// <summary>The namespace for events that are scoped to this step.</summary>
    private readonly string _eventNamespace;

    /// <summary>
    /// A mapping of function names to the functions themselves.
    /// </summary>
    internal Dictionary<string, KernelFunctionMetadata> FunctionsDict { get; set; }

    /// <summary>
    /// A mapping of event Ids to the edges that are triggered by those events.
    /// </summary>
    internal Dictionary<string, List<ProcessStepEdgeBuilder>> Edges { get; }

    /// <summary>
    /// Builds the step.
    /// </summary>
    /// <returns>an instance of <see cref="KernelProcessStep"/>.</returns>
    internal abstract KernelProcessStepInfo BuildStep();

    /// <summary>
    /// Links the output of the current step to the an input of another step via the specified event type.
    /// </summary>
    /// <param name="eventId">The Id of the event.</param>
    /// <param name="edgeBuilder">The targeted function.</param>
    internal virtual void LinkTo(string eventId, ProcessStepEdgeBuilder edgeBuilder)
    {
        if (!this.Edges.TryGetValue(eventId, out List<ProcessStepEdgeBuilder>? edges) || edges == null)
        {
            edges = [];
            this.Edges[eventId] = edges;
        }

        edges.Add(edgeBuilder);
    }

    /// <summary>
    /// Used to resolve the target function and parameter for a given optional function name and parameter name.
    /// This is used to simplify the process of creating a <see cref="KernelProcessFunctionTarget"/> by making it possible
    /// to infer the function and/or parameter names from the function metadata if only one option exists.
    /// </summary>
    /// <param name="functionName">The name of the function. May be null if only one function exists on the step.</param>
    /// <param name="parameterName">The name of the parameter. May be null if only one parameter exists on the function.</param>
    /// <returns>A valid instance of <see cref="KernelProcessFunctionTarget"/> for this step.</returns>
    /// <exception cref="InvalidOperationException"></exception>
    internal virtual KernelProcessFunctionTarget ResolveFunctionTarget(string? functionName, string? parameterName)
    {
        string? verifiedFunctionName = functionName;
        string? verifiedParameterName = parameterName;

        if (this.FunctionsDict.Count == 0)
        {
            throw new KernelException($"The target step {this.Name} has no functions.");
        }

        // If the function name is null or whitespace, then there can only one function on the step
        if (string.IsNullOrWhiteSpace(verifiedFunctionName))
        {
            if (this.FunctionsDict.Count > 1)
            {
                throw new KernelException("The target step has more than one function, so a function name must be provided.");
            }

            verifiedFunctionName = this.FunctionsDict.Keys.First();
        }

        // Verify that the target function exists
        if (!this.FunctionsDict.TryGetValue(verifiedFunctionName!, out var kernelFunctionMetadata) || kernelFunctionMetadata is null)
        {
            throw new KernelException($"The function {functionName} does not exist on step {this.Name}");
        }

        // If the parameter name is null or whitespace, then the function must have 0 or 1 parameters
        if (string.IsNullOrWhiteSpace(verifiedParameterName))
        {
            var undeterminedParameters = kernelFunctionMetadata.Parameters.Where(p => p.ParameterType != typeof(KernelProcessStepContext)).ToList();

            if (undeterminedParameters.Count > 1)
            {
                throw new KernelException($"The function {functionName} on step {this.Name} has more than one parameter, so a parameter name must be provided.");
            }

            // We can infer the parameter name from the function metadata
            if (undeterminedParameters.Count == 1)
            {
                parameterName = undeterminedParameters[0].Name;
                verifiedParameterName = parameterName;
            }
        }

        Verify.NotNull(verifiedFunctionName);

        return new KernelProcessFunctionTarget(
            stepId: this.Id!,
            functionName: verifiedFunctionName,
            parameterName: verifiedParameterName
        );
    }

    /// <summary>
    /// Loads a mapping of function names to the associated functions metadata.
    /// </summary>
    /// <returns>A <see cref="Dictionary{TKey, TValue}"/> where TKey is <see cref="string"/> and TValue is <see cref="KernelFunctionMetadata"/></returns>
    internal abstract Dictionary<string, KernelFunctionMetadata> GetFunctionMetadataMap();

    /// <summary>
    /// Given an event Id, returns a scoped event Id that is unique to this instance of the step.
    /// </summary>
    /// <param name="eventId">The Id of the event.</param>
    /// <returns>An Id that represents the provided event Id scoped to this step instance.</returns>
    protected string GetScopedEventId(string eventId)
    {
        // Scope the event to this instance of this step by prefixing the event Id with the step's namespace.
        return $"{this._eventNamespace}.{eventId}";
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessStepBuilder"/> class.
    /// </summary>
    /// <param name="name">The name of the step.</param>
    protected ProcessStepBuilder(string name)
    {
        this.Name ??= name;
        Verify.NotNullOrWhiteSpace(name);

        this.FunctionsDict = [];
        this.Id = Guid.NewGuid().ToString("n");
        this._eventNamespace = $"{this.Name}_{this.Id}";
        this.Edges = new Dictionary<string, List<ProcessStepEdgeBuilder>>(StringComparer.OrdinalIgnoreCase);
    }
}

/// <summary>
/// Provides functionality for incrementally defining a process step.
/// </summary>
public sealed class ProcessStepBuilder<TStep> : ProcessStepBuilder where TStep : KernelProcessStep
{
    /// <summary>
    /// Creates a new instance of the <see cref="ProcessStepBuilder"/> class. If a name is not provided, the name will be derived from the type of the step.
    /// </summary>
    public ProcessStepBuilder(string? name = null)
        : base(name ?? typeof(TStep).Name)
    {
        this.FunctionsDict = this.GetFunctionMetadataMap();
    }

    /// <summary>
    /// Builds the step.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcessStepInfo"/></returns>
    internal override KernelProcessStepInfo BuildStep()
    {
        KernelProcessStepState? stateObject = null;

        if (typeof(TStep).TryGetSubtypeOfStatefulStep(out Type? genericStepType) && genericStepType is not null)
        {
            // The step is a subclass of KernelProcessStep<>, so we need to extract the generic type argument
            // and create an instance of the corresponding KernelProcessStepState<>.
            var userStateType = genericStepType.GetGenericArguments()[0];
            Verify.NotNull(userStateType);

            var stateType = typeof(KernelProcessStepState<>).MakeGenericType(userStateType);
            Verify.NotNull(stateType);

            stateObject = (KernelProcessStepState?)Activator.CreateInstance(stateType, this.Name, this.Id);
        }
        else
        {
            // The step is a KernelProcessStep with no user-defined state, so we can use the base KernelProcessStepState.
            stateObject = new KernelProcessStepState(this.Name, this.Id);
        }

        Verify.NotNull(stateObject);

        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());

        // Then build the step with the edges and state.
        var builtStep = new KernelProcessStepInfo(typeof(TStep), stateObject, builtEdges);
        return builtStep;
    }

    /// <inheritdoc/>
    internal override Dictionary<string, KernelFunctionMetadata> GetFunctionMetadataMap()
    {
        // TODO: Should not have to create a new instance of the step to get the functions metadata.
        var functions = KernelPluginFactory.CreateFromType<TStep>();
        return functions.ToDictionary(f => f.Name, f => f.Metadata);
    }
}
