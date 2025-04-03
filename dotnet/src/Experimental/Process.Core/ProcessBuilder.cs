// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality for incrementally defining a process.
/// </summary>
public sealed class ProcessBuilder : ProcessStepBuilder
{
    /// <summary>The collection of steps within this process.</summary>
    private readonly List<ProcessStepBuilder> _steps = [];

    /// <summary>The collection of entry steps within this process.</summary>
    private readonly List<ProcessStepBuilder> _entrySteps = [];

    /// <summary>Maps external input event Ids to the target entry step for the event.</summary>
    private readonly Dictionary<string, ProcessFunctionTargetBuilder> _externalEventTargetMap = [];

    private readonly List<EventListener> _eventListeners = [];

    /// <summary>
    /// A boolean indicating if the current process is a step within another process.
    /// </summary>
    internal bool HasParentProcess { get; set; }

    /// <summary>
    /// Version of the process, used when saving the state of the process
    /// </summary>
    public string Version { get; init; } = "v1";

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
        Verify.NotNull(edgeBuilder?.Source, nameof(edgeBuilder.Source));
        Verify.NotNull(edgeBuilder?.Target, nameof(edgeBuilder.Target));

        // Keep track of the entry point steps
        this._entrySteps.Add(edgeBuilder.Source);
        this._externalEventTargetMap[eventId] = edgeBuilder.Target;
        base.LinkTo(eventId, edgeBuilder);
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
    /// <param name="stateMetadata">State to apply to the step on the build process</param>
    /// <returns></returns>
    internal override KernelProcessStepInfo BuildStep(KernelProcessStepStateMetadata? stateMetadata = null)
    {
        // The step is a, process so we can return the step info directly.
        return this.Build(stateMetadata as KernelProcessStateMetadata);
    }

    /// <summary>
    /// Add the provided step builder to the process.
    /// </summary>
    /// <remarks>
    /// Utilized by <see cref="ProcessMapBuilder"/> only.
    /// </remarks>
    internal void AddStepFromBuilder(ProcessStepBuilder stepBuilder)
    {
        this._steps.Add(stepBuilder);
    }

    /// <summary>
    /// Check to ensure stepName is not used yet in another step
    /// </summary>
    private bool StepNameAlreadyExists(string stepName)
    {
        return this._steps.Select(step => step.Name).Contains(stepName);
    }

    /// <summary>
    /// Verify step is unique and add to the process.
    /// </summary>
    private TBuilder AddStep<TBuilder>(TBuilder builder, IReadOnlyList<string>? aliases) where TBuilder : ProcessStepBuilder
    {
        if (this.StepNameAlreadyExists(builder.Name))
        {
            throw new InvalidOperationException($"Step name {builder.Name} is already used, assign a different name for step");
        }

        if (aliases != null && aliases.Count > 0)
        {
            builder.Aliases = aliases;
        }

        this._steps.Add(builder);

        return builder;
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
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessStepBuilder"/></returns>
    public ProcessStepBuilder AddStepFromType<TStep>(string? name = null, IReadOnlyList<string>? aliases = null, string? id = null) where TStep : KernelProcessStep
    {
        ProcessStepBuilder<TStep> stepBuilder = new(name, id: id);

        return this.AddStep(stepBuilder, aliases);
    }

    /// <summary>
    /// Adds a step to the process.
    /// </summary>
    /// <param name="stepType">The step Type.<param>
    /// <param name="name">The name of the step. This parameter is optional.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessStepBuilder"/></returns>
    public ProcessStepBuilder AddStepFromType(Type stepType, string? name = null, IReadOnlyList<string>? aliases = null, string? id = null)
    {
        ProcessStepBuilderTyped stepBuilder = new(stepType, name, id);

        return this.AddStep(stepBuilder, aliases);
    }

    /// <summary>
    /// Adds a step to the process and define it's initial user-defined state.
    /// </summary>
    /// <typeparam name="TStep">The step Type.</typeparam>
    /// <typeparam name="TState">The state Type.</typeparam>
    /// <param name="initialState">The initial state of the step.</param>
    /// <param name="name">The name of the step. This parameter is optional.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessStepBuilder"/></returns>
    public ProcessStepBuilder AddStepFromType<TStep, TState>(TState initialState, string? name = null, IReadOnlyList<string>? aliases = null) where TStep : KernelProcessStep<TState> where TState : class, new()
    {
        ProcessStepBuilder<TStep> stepBuilder = new(name, initialState: initialState);

        return this.AddStep(stepBuilder, aliases);
    }

    /// <summary>
    /// Adds a sub process to the process.
    /// </summary>
    /// <param name="kernelProcess">The process to add as a step.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessStepBuilder"/></returns>
    public ProcessBuilder AddStepFromProcess(ProcessBuilder kernelProcess, IReadOnlyList<string>? aliases = null)
    {
        kernelProcess.HasParentProcess = true;

        return this.AddStep(kernelProcess, aliases);
    }

    /// <summary>
    /// Adds a step to the process.
    /// </summary>
    /// <typeparam name="TStep">The step Type.</typeparam>
    /// <param name="name">The name of the step. This parameter is optional.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessMapBuilder"/></returns>
    public ProcessMapBuilder AddMapStepFromType<TStep>(string? name = null, IReadOnlyList<string>? aliases = null) where TStep : KernelProcessStep
    {
        ProcessStepBuilder<TStep> stepBuilder = new(name);

        ProcessMapBuilder mapBuilder = new(stepBuilder);

        return this.AddStep(mapBuilder, aliases);
    }

    /// <summary>
    /// Adds a step to the process and define it's initial user-defined state.
    /// </summary>
    /// <typeparam name="TStep">The step Type.</typeparam>
    /// <typeparam name="TState">The state Type.</typeparam>
    /// <param name="initialState">The initial state of the step.</param>
    /// <param name="name">The name of the step. This parameter is optional.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessMapBuilder"/></returns>
    public ProcessMapBuilder AddMapStepFromType<TStep, TState>(TState initialState, string? name = null, IReadOnlyList<string>? aliases = null) where TStep : KernelProcessStep<TState> where TState : class, new()
    {
        ProcessStepBuilder<TStep> stepBuilder = new(name, initialState: initialState);

        ProcessMapBuilder mapBuilder = new(stepBuilder);

        return this.AddStep(mapBuilder, aliases);
    }

    /// <summary>
    /// Adds a map operation to the process that accepts an enumerable input parameter and
    /// processes each individual parameter value by the specified map operation (TStep).
    /// Results are coalesced into a result set of the same dimension as the input set.
    /// </summary>
    /// <param name="process">The target for the map operation</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessMapBuilder"/></returns>
    public ProcessMapBuilder AddMapStepFromProcess(ProcessBuilder process, IReadOnlyList<string>? aliases = null)
    {
        process.HasParentProcess = true;

        ProcessMapBuilder mapBuilder = new(process);

        return this.AddStep(mapBuilder, aliases);
    }

    /// <summary>
    /// Adds proxy step to the process that allows emitting events externally. For making use of it, there should be an implementation
    /// of <see cref="IExternalKernelProcessMessageChannel"/> passed.
    /// For now, the current implementation only allows for 1 implementation of <see cref="IExternalKernelProcessMessageChannel"/> at the time.
    /// </summary>
    /// <param name="externalTopics">topic names to be used externally</param>
    /// <param name="name">name of the proxy step</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessProxyBuilder"/></returns>
    public ProcessProxyBuilder AddProxyStep(IReadOnlyList<string> externalTopics, string? name = null, IReadOnlyList<string>? aliases = null)
    {
        ProcessProxyBuilder proxyBuilder = new(externalTopics, name ?? nameof(KernelProxyStep));

        return this.AddStep(proxyBuilder, aliases);
    }

    /// <summary>
    /// Provides an instance of <see cref="ProcessEdgeBuilder"/> for defining an input edge to a process.
    /// </summary>
    /// <param name="eventId">The Id of the external event.</param>
    /// <returns>An instance of <see cref="ProcessEdgeBuilder"/></returns>
    public ProcessEdgeBuilder OnInputEvent(string eventId)
    {
        return new ProcessEdgeBuilder(this, eventId);
    }

    /// <summary>
    /// Provides an instance of <see cref="ProcessEdgeBuilder"/> for defining an edge to a
    /// step that responds to an unhandled process error.
    /// </summary>
    /// <returns>An instance of <see cref="ProcessEdgeBuilder"/></returns>
    /// <remarks>
    /// To target a specific error source, use the <see cref="ProcessStepBuilder.OnFunctionError"/> on the step.
    /// </remarks>
    public ProcessEdgeBuilder OnError()
    {
        return new ProcessEdgeBuilder(this, ProcessConstants.GlobalErrorEventId);
    }

    /// <summary>
    /// Retrieves the target for a given external event. The step associated with the target is the process itself (this).
    /// </summary>
    /// <param name="eventId">The Id of the event</param>
    /// <returns>An instance of <see cref="ProcessFunctionTargetBuilder"/></returns>
    /// <exception cref="KernelException"></exception>
    public ProcessFunctionTargetBuilder WhereInputEventIs(string eventId)
    {
        Verify.NotNullOrWhiteSpace(eventId, nameof(eventId));

        if (!this._externalEventTargetMap.TryGetValue(eventId, out var target))
        {
            throw new KernelException($"The process named '{this.Name}' does not expose an event with Id '{eventId}'.");
        }

        // Targets for external events on a process should be scoped to the process itself rather than the step inside the process.
        var processTarget = target with { Step = this, TargetEventId = eventId };
        return processTarget;
    }

    /// <summary>
    /// Builds the process.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    /// <exception cref="NotImplementedException"></exception>
    public KernelProcess Build(KernelProcessStateMetadata? stateMetadata = null)
    {
        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());

        // Build the steps and injecting initial state if any is provided
        var builtSteps = this.BuildWithStateMetadata(stateMetadata);

        // Create the process
        KernelProcessState state = new(this.Name, version: this.Version, id: this.HasParentProcess ? this.Id : null);
        KernelProcess process = new(state, builtSteps, builtEdges);

        return process;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessBuilder"/> class.
    /// </summary>
    /// <param name="name">The name of the process. This is required.</param>
    public ProcessBuilder(string name)
        : base(name)
    {
    }

    public static async Task<KernelProcess?> ReadFromStringAsync(string processString)
    {
        Verify.NotNullOrWhiteSpace(processString);

        try
        {
            var workflow = WorkflowSerializer.DeserializeFromYaml(processString);
            var builder = new WorkflowBuilder();
            var process = await builder.BuildProcessAsync(workflow).ConfigureAwait(false);

            return process;
        }
        catch (Exception ex)
        {
            throw new ArgumentException("Failed to deserialize the process string.", ex);
        }
    }

    public ListenForBuilder ListenFor()
    {
        return new ListenForBuilder();
    }
    #endregion
}

public class ListenForBuilder
{
    public ListenForTargetBuilder Message(string type, ProcessStepBuilder from)
    {
        Verify.NotNullOrWhiteSpace(type, nameof(type));
        Verify.NotNull(from, nameof(from));

        return new ListenForTargetBuilder([new() { MessageType = type, Source = from }]);
    }

    public ListenForTargetBuilder AllOf(List<MessageSource> messageSources)
    {
        Verify.NotNullOrEmpty(messageSources, nameof(messageSources));
        return new ListenForTargetBuilder(messageSources);
    }
}

public class ListenForTargetBuilder
{
    private readonly List<MessageSource> _messageSources = new();

    public ListenForTargetBuilder(List<MessageSource> messageSources)
    {
        Verify.NotNullOrEmpty(messageSources, nameof(messageSources));
        this._messageSources = messageSources;
    }

    public ListenForTargetBuilder SendTo(ProcessStepBuilder destination)
    {
        Verify.NotNull(destination, nameof(destination));

        foreach (var messageSource in this._messageSources)
        {
            if (messageSource.Source == null)
            {
                throw new InvalidOperationException("Source step cannot be null.");
            }

            // Create a new event listener for the source messages and the destination step
            var eventListener = new ProcessEventListenerBuilder(this._messageSources, destination.Id);

            // Link all the source steps to the event listener
            messageSource.Source.OnEvent(messageSource.MessageType)
                .SendEventTo(new ProcessFunctionTargetBuilder(eventListener));
        }

        return new ListenForTargetBuilder(this._messageSources);
    }
}

public class MessageSource
{
    public string MessageType { get; set; }

    public ProcessStepBuilder Source { get; set; }
}

// TODO: Move to Core
public class EventListener
{
    public EventListener(string? id = null)
    {
        this.Id = id ?? Guid.NewGuid().ToString();
    }

    public string Id { get; }

    public List<MessageSource> MessageSources = [];

    public string DestinationId = "";
}
