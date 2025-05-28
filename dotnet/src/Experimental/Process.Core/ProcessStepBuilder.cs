// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An abstract class that provides functionality for incrementally defining a process step and linking it to other steps within a Process.
/// </summary>
public abstract class ProcessStepBuilder
{
    #region Public Interface

    /// <summary>
    /// The unique identifier for the step within a process. A process cannot have two steps with the same stepId.
    /// This can be human-readable but is required to be unique within the process.
    /// </summary>
    public string StepId { get; }

    /// <summary>
    /// Alternative names that have been used to previous versions of the step
    /// </summary>
    public IReadOnlyList<string> Aliases { get; internal set; } = [];

    /// <summary>
    /// A mapping of group Ids to functions that will be used to map the input of the step to the input of the group.
    /// </summary>
    public Dictionary<string, KernelProcessEdgeGroup> IncomingEdgeGroups { get; internal set; } = [];

    /// <summary>
    /// Define the behavior of the step when the event with the specified Id is fired.
    /// </summary>
    /// <param name="eventId">The Id of the event of interest.</param>
    /// <returns>An instance of <see cref="ProcessStepEdgeBuilder"/>.</returns>
    public ProcessStepEdgeBuilder OnEvent(string eventId)
    {
        // scope the event to this instance of this step
        var scopedEventId = this.GetScopedEventId(eventId);
        return new ProcessStepEdgeBuilder(this, scopedEventId, eventId);
    }

    /// <summary>
    /// Returns the event Id that is used to identify the result of a function.
    /// </summary>
    /// <param name="functionName">Optional: name of the step function the result is expected from</param>
    /// <returns></returns>
    public string GetFunctionResultEventId(string? functionName = null)
    {
        // TODO: Add a check to see if the function name is valid if provided
        if (string.IsNullOrWhiteSpace(functionName))
        {
            functionName = this.ResolveFunctionName();
        }
        return $"{functionName}.OnResult";
    }

    /// <summary>
    /// Returns the event Id that is used to identify the step specific event.
    /// </summary>
    /// <param name="eventName">used for custom events emitted by step</param>
    /// <param name="functionName">used for return objects from specific function, if step has only 1 function no need to provide functionName</param>
    /// <returns></returns>
    public string GetFullEventId(string? eventName = null, string? functionName = null)
    {
        if (eventName == null)
        {
            // default function result are used
            eventName = this.GetFunctionResultEventId(functionName);
        }

        return $"{this.StepId}.{eventName}";
    }

    /// <summary>
    /// Define the behavior of the step when the specified function has been successfully invoked.
    /// </summary>
    /// <param name="functionName">Optional: The name of the function of interest.</param>
    /// If the function name is not provided, it will be inferred if there's exactly one function in the step.
    /// <returns>An instance of <see cref="ProcessStepEdgeBuilder"/>.</returns>
    public ProcessStepEdgeBuilder OnFunctionResult(string? functionName = null)
    {
        var eventId = this.GetFunctionResultEventId(functionName);
        return this.OnEvent(eventId);
    }

    /// <summary>
    /// Define the behavior of the step when the specified function has thrown an exception.
    /// If the function name is not provided, it will be inferred if there's exactly one function in the step.
    /// </summary>
    /// <param name="functionName">Optional: The name of the function of interest.</param>
    /// <returns>An instance of <see cref="ProcessStepEdgeBuilder"/>.</returns>
    public ProcessStepEdgeBuilder OnFunctionError(string? functionName = null)
    {
        if (string.IsNullOrWhiteSpace(functionName))
        {
            functionName = this.ResolveFunctionName();
        }
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
    /// The process builder that this step is a part of. This may be null if the step is itself a process.
    /// </summary>
    internal ProcessBuilder? ProcessBuilder { get; }

    /// <summary>
    /// Builds the step with step state
    /// </summary>
    /// <returns>an instance of <see cref="KernelProcessStepInfo"/>.</returns>
    internal abstract KernelProcessStepInfo BuildStep(ProcessBuilder processBuilder);

    /// <summary>
    /// Registers a group input mapping for the step.
    /// </summary>
    /// <param name="edgeGroup"></param>
    internal void RegisterGroupInputMapping(KernelProcessEdgeGroup edgeGroup)
    {
        // If the group is alrwady registered, then we don't need to register it again.
        if (this.IncomingEdgeGroups.ContainsKey(edgeGroup.GroupId))
        {
            return;
        }

        // Register the group by GroupId.
        this.IncomingEdgeGroups[edgeGroup.GroupId] = edgeGroup;
    }

    /// <summary>
    /// Resolves the function name for the step.
    /// </summary>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    private string ResolveFunctionName()
    {
        if (this.FunctionsDict.Count == 0)
        {
            throw new KernelException($"The step {this.StepId} has no functions.");
        }
        else if (this.FunctionsDict.Count > 1)
        {
            throw new KernelException($"The step {this.StepId} has more than one function, so a function name must be provided.");
        }

        return this.FunctionsDict.Keys.First();
    }

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
            throw new KernelException($"The target step {this.StepId} has no functions.");
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
            throw new KernelException($"The function {functionName} does not exist on step {this.StepId}");
        }

        // If the parameter name is null or whitespace, then the function must have 0 or 1 parameters
        if (string.IsNullOrWhiteSpace(verifiedParameterName))
        {
            var undeterminedParameters = kernelFunctionMetadata.Parameters.Where(p => p.ParameterType != typeof(KernelProcessStepContext)).ToList();

            if (undeterminedParameters.Count > 1)
            {
                // TODO: Uncomment the following line if we want to enforce parameter specification.
                //throw new KernelException($"The function {functionName} on step {this.Name} has more than one parameter, so a parameter name must be provided.");
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
            stepId: this.StepId!,
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
    /// <param name="id">The unique Id of the step.</param>
    /// <param name="processBuilder">The process builder that this step is a part of.</param>
    protected ProcessStepBuilder(string id, ProcessBuilder? processBuilder)
    {
        Verify.NotNullOrWhiteSpace(id, nameof(id));

        this.StepId ??= id;
        this.StepId = id;
        this.FunctionsDict = [];
        this._eventNamespace = this.StepId;
        this.Edges = new Dictionary<string, List<ProcessStepEdgeBuilder>>(StringComparer.OrdinalIgnoreCase);
        this.ProcessBuilder = processBuilder;
    }
}

/// <summary>
/// Provides functionality for incrementally defining a process step.
/// </summary>
public class ProcessStepBuilderTyped : ProcessStepBuilder
{
    /// <summary>
    /// The initial state of the step. This may be null if the step does not have any state.
    /// </summary>
    private readonly object? _initialState;

    private readonly Type _stepType;

    /// <summary>
    /// Creates a new instance of the <see cref="ProcessStepBuilder"/> class. If a name is not provided, the name will be derived from the type of the step.
    /// </summary>
    /// <param name="stepType">The <see cref="Type"/> of the step.</param>
    /// <param name="id">The unique id of the step.</param>
    /// <param name="processBuilder">The process builder that this step is a part of.</param>
    /// <param name="initialState">Initial state of the step to be used on the step building stage</param>
    internal ProcessStepBuilderTyped(Type stepType, string id, ProcessBuilder? processBuilder, object? initialState = default)
        : base(id, processBuilder)
    {
        Verify.NotNull(stepType);

        this._stepType = stepType;
        this.FunctionsDict = this.GetFunctionMetadataMap();
        this._initialState = initialState;
    }

    /// <summary>
    /// Builds the step with a state if provided
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcessStepInfo"/></returns>
    internal override KernelProcessStepInfo BuildStep(ProcessBuilder processBuilder)
    {
        KernelProcessStepState? stateObject = null;
        KernelProcessStepMetadataAttribute stepMetadataAttributes = KernelProcessStepMetadataFactory.ExtractProcessStepMetadataFromType(this._stepType);

        if (this._stepType.TryGetSubtypeOfStatefulStep(out Type? genericStepType) && genericStepType is not null)
        {
            // The step is a subclass of KernelProcessStep<>, so we need to extract the generic type argument
            // and create an instance of the corresponding KernelProcessStepState<>.
            var userStateType = genericStepType.GetGenericArguments()[0];
            Verify.NotNull(userStateType);

            var stateType = typeof(KernelProcessStepState<>).MakeGenericType(userStateType);
            Verify.NotNull(stateType);

            // If the step has a user-defined state then we need to validate that the initial state is of the correct type.
            if (this._initialState is not null && this._initialState.GetType() != userStateType)
            {
                throw new KernelException($"The initial state provided for step {this.StepId} is not of the correct type. The expected type is {userStateType.Name}.");
            }

            var initialState = this._initialState ?? Activator.CreateInstance(userStateType);
            stateObject = (KernelProcessStepState?)Activator.CreateInstance(stateType, this.StepId, stepMetadataAttributes.Version, null);
            stateType.GetProperty(nameof(KernelProcessStepState<object>.State))?.SetValue(stateObject, initialState);
        }
        else
        {
            // The step is a KernelProcessStep with no user-defined state, so we can use the base KernelProcessStepState.
            stateObject = new KernelProcessStepState(this.StepId, stepMetadataAttributes.Version);
        }

        Verify.NotNull(stateObject);

        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());

        // Then build the step with the edges and state.
        var builtStep = new KernelProcessStepInfo(this._stepType, stateObject, builtEdges, this.IncomingEdgeGroups);
        return builtStep;
    }

    /// <inheritdoc/>
    internal override Dictionary<string, KernelFunctionMetadata> GetFunctionMetadataMap()
    {
        var metadata = KernelFunctionMetadataFactory.CreateFromType(this._stepType);
        return metadata.ToDictionary(m => m.Name, m => m);
    }
}

/// <summary>
/// Provides functionality for incrementally defining a process step.
/// </summary>
public class ProcessStepBuilder<TStep> : ProcessStepBuilderTyped where TStep : KernelProcessStep
{
    /// <summary>
    /// Creates a new instance of the <see cref="ProcessStepBuilder"/> class. If a name is not provided, the name will be derived from the type of the step.
    /// </summary>
    /// <param name="id">The unique Id of the step.</param>
    /// <param name="processBuilder">The process builder that this step is a part of.</param>
    /// <param name="initialState">Initial state of the step to be used on the step building stage</param>
    internal ProcessStepBuilder(string id, ProcessBuilder? processBuilder = null, object? initialState = default)
        : base(typeof(TStep), id, processBuilder, initialState)
    {
    }
}
