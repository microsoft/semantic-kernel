// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Tools;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality for incrementally defining a process.
/// </summary>
public sealed partial class ProcessBuilder : ProcessStepBuilder
{
    /// <summary>The collection of steps within this process.</summary>
    private readonly List<ProcessStepBuilder> _steps = [];

    /// <summary>The collection of entry steps within this process.</summary>
    private readonly List<ProcessStepBuilder> _entrySteps = [];

    /// <summary>Maps external input event Ids to the target entry step for the event.</summary>
    private readonly Dictionary<string, ProcessTargetBuilder> _externalEventTargetMap = [];

    /// <summary>
    /// The collection of threads within this process.
    /// </summary>
    private readonly Dictionary<string, KernelProcessAgentThread> _threads = [];

    /// <summary>
    /// A boolean indicating if the current process is a step within another process.
    /// </summary>
    internal bool HasParentProcess { get; set; }

    /// <summary>
    /// Version of the process, used when saving the state of the process
    /// </summary>
    public string Version { get; init; } = "v1";

    /// <summary>
    /// The type of the state. This is optional.
    /// </summary>
    public Type? StateType { get; init; } = null;

    /// <summary>
    /// The description of the process.
    /// </summary>
    public string Description { get; init; } = string.Empty;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessBuilder"/> class.
    /// </summary>
    /// <param name="id">The name of the process. This is required.</param>
    /// <param name="description">The semantic description of the Process being built.</param>
    /// <param name="processBuilder">ProcessBuilder to copy from</param>
    /// <param name="stateType">The type of the state. This is optional.</param>
    public ProcessBuilder(string id, string? description = null, ProcessBuilder? processBuilder = null, Type? stateType = null)
        : base(id, processBuilder)
    {
        Verify.NotNullOrWhiteSpace(id, nameof(id));
        this.StateType = stateType;
        this.Description = description ?? string.Empty;
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

    internal void AddOutputEventToProcess(ProcessStepEventData outputEvent)
    {
        this.OutputStepEvents.Add(outputEvent.EventId, outputEvent);
    }

    /// <summary>
    /// Builds the step.
    /// </summary>
    /// <param name="processBuilder">ProcessBuilder to build the step for</param>
    /// <returns></returns>
    internal override KernelProcessStepInfo BuildStep(ProcessBuilder processBuilder)
    {
        // The step is a, process so we can return the step info directly.
        return this.Build();
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
        return this._steps.Select(step => step.StepId).Contains(stepName);
    }

    /// <summary>
    /// Verify step is unique and add to the process.
    /// </summary>
    private TBuilder AddStep<TBuilder>(TBuilder builder, IReadOnlyList<string>? aliases) where TBuilder : ProcessStepBuilder
    {
        if (this.StepNameAlreadyExists(builder.StepId))
        {
            throw new InvalidOperationException($"Step name {builder.StepId} is already used, assign a different name for step");
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
    /// <param name="id">The unique Id of the step. If not provided, the name of the step Type will be used.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessStepBuilder"/></returns>
    public ProcessStepBuilder AddStepFromType<TStep>(string? id = null, IReadOnlyList<string>? aliases = null) where TStep : KernelProcessStep
    {
        ProcessStepBuilder<TStep> stepBuilder = new(id: id ?? typeof(TStep).Name, this);

        return this.AddStep(stepBuilder, aliases);
    }

    /// <summary>
    /// Adds a step to the process.
    /// </summary>
    /// <param name="stepType">The step Type.</param>
    /// <param name="id">The unique Id of the step. If not provided, the name of the step Type will be used.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessStepBuilder"/></returns>
    public ProcessStepBuilder AddStepFromType(Type stepType, string? id = null, IReadOnlyList<string>? aliases = null)
    {
        ProcessStepBuilderTyped stepBuilder = new(stepType: stepType, id: id ?? stepType.Name, this);

        return this.AddStep(stepBuilder, aliases);
    }

    /// <summary>
    /// Adds a step to the process and define it's initial user-defined state.
    /// </summary>
    /// <typeparam name="TStep">The step Type.</typeparam>
    /// <typeparam name="TState">The state Type.</typeparam>
    /// <param name="initialState">The initial state of the step.</param>
    /// <param name="id">The unique Id of the step. If not provided, the name of the step Type will be used.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessStepBuilder"/></returns>
    public ProcessStepBuilder AddStepFromType<TStep, TState>(TState initialState, string? id = null, IReadOnlyList<string>? aliases = null) where TStep : KernelProcessStep<TState> where TState : class, new()
    {
        ProcessStepBuilder<TStep> stepBuilder = new(id ?? typeof(TStep).Name, this, initialState: initialState);

        return this.AddStep(stepBuilder, aliases);
    }

    /// <summary>
    /// Adds a step to the process from a declarative agent.
    /// </summary>
    /// <param name="agentDefinition">The <see cref="AgentDefinition"/></param>
    /// <param name="id">The unique Id of the step. If not provided, the name of the step Type will be used.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <param name="threadName">Specifies the thread reference to be used by the agent. If not provided, the agent will create a new thread for each invocation.</param>
    /// <param name="humanInLoopMode">Specifies the human-in-the-loop mode for the agent. If not provided, the default is <see cref="HITLMode.Never"/>.</param>
    public ProcessAgentBuilder<TProcessState> AddStepFromAgent<TProcessState>(AgentDefinition agentDefinition, string? id = null, IReadOnlyList<string>? aliases = null, string? threadName = null, HITLMode humanInLoopMode = HITLMode.Never) where TProcessState : class, new()
    {
        Verify.NotNull(agentDefinition, nameof(agentDefinition));

        if (string.IsNullOrWhiteSpace(agentDefinition.Name))
        {
            throw new ArgumentException("AgentDefinition.Name cannot be null or empty.", nameof(agentDefinition));
        }

        if (string.IsNullOrWhiteSpace(threadName))
        {
            // No thread name was specified so add a new thread for the agent.
            this.AddThread(agentDefinition.Name, KernelProcessThreadLifetime.Scoped);
            threadName = agentDefinition.Name;
        }

        var stepBuilder = new ProcessAgentBuilder<TProcessState>(agentDefinition, threadName: threadName, [], this, id) { HumanInLoopMode = humanInLoopMode }; // TODO: Add inputs to the agent
        return this.AddStep(stepBuilder, aliases);
    }

    /// <summary>
    /// Adds a step to the process from a declarative agent.
    /// </summary>
    /// <param name="agentDefinition">The <see cref="AgentDefinition"/></param>
    /// <param name="id">The unique Id of the step. If not provided, the name of the step Type will be used.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <param name="threadName">Specifies the thread reference to be used by the agent. If not provided, the agent will create a new thread for each invocation.</param>
    /// <param name="humanInLoopMode">Specifies the human-in-the-loop mode for the agent. If not provided, the default is <see cref="HITLMode.Never"/>.</param>
    public ProcessAgentBuilder AddStepFromAgent(AgentDefinition agentDefinition, string? id = null, IReadOnlyList<string>? aliases = null, string? threadName = null, HITLMode humanInLoopMode = HITLMode.Never)
    {
        Verify.NotNull(agentDefinition, nameof(agentDefinition));

        if (string.IsNullOrWhiteSpace(agentDefinition.Name))
        {
            throw new ArgumentException("AgentDefinition.Name cannot be null or empty.", nameof(agentDefinition));
        }

        if (string.IsNullOrWhiteSpace(threadName))
        {
            // No thread name was specified so add a new thread for the agent.
            this.AddThread(agentDefinition.Name, KernelProcessThreadLifetime.Scoped);
            threadName = agentDefinition.Name;
        }

        var stepBuilder = new ProcessAgentBuilder(agentDefinition, threadName: threadName, [], this, id) { HumanInLoopMode = humanInLoopMode };
        return this.AddStep(stepBuilder, aliases);
    }

    /// <summary>
    /// Adds a step to the process from a declarative agent.
    /// </summary>
    /// <param name="agentDefinition">The <see cref="AgentDefinition"/></param>
    /// <param name="threadName">Specifies the thread reference to be used by the agent. If not provided, the agent will create a new thread for each invocation.</param>
    /// <param name="stepId">Id of the step. If not provided, the Id will come from the agent Id.</param>
    /// <param name="humanInLoopMode">Specifies the human-in-the-loop mode for the agent. If not provided, the default is <see cref="HITLMode.Never"/>.</param>
    /// <param name="aliases"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    public ProcessAgentBuilder<TProcessState> AddStepFromAgentProxy<TProcessState>(AgentDefinition agentDefinition, string? threadName = null, string? stepId = null, HITLMode humanInLoopMode = HITLMode.Never, IReadOnlyList<string>? aliases = null) where TProcessState : class, new()
    {
        Verify.NotNull(agentDefinition, nameof(agentDefinition));

        if (string.IsNullOrWhiteSpace(agentDefinition.Id))
        {
            throw new ArgumentException("AgentDefinition.Id cannot be null or empty.", nameof(agentDefinition));
        }

        if (string.IsNullOrWhiteSpace(agentDefinition.Name))
        {
            throw new ArgumentException("AgentDefinition.Name cannot be null or empty.", nameof(agentDefinition));
        }

        if (string.IsNullOrWhiteSpace(threadName))
        {
            // No thread name was specified so add a new thread for the agent.
            this.AddThread(agentDefinition.Name, KernelProcessThreadLifetime.Scoped);
            threadName = agentDefinition.Name;
        }

        KernelProcessStateResolver<string?> agentIdResolver = new((s) =>
        {
            StateResolverContentWrapper wrapper = new() { State = s };
            var result = JMESPathConditionEvaluator.EvaluateToString(wrapper, agentDefinition.Id);
            return Task.FromResult(result);
        });

        var stepBuilder = new ProcessAgentBuilder<TProcessState>(agentDefinition, threadName: threadName, [], this, stepId) { AgentIdResolver = agentIdResolver, HumanInLoopMode = humanInLoopMode }; // TODO: Add inputs to the agent
        return this.AddStep(stepBuilder, aliases);
    }

    /// <summary>
    /// Adds a step to the process that represents the end of the process.
    /// </summary>
    /// <returns></returns>
    public ProcessStepBuilder AddEndStep()
    {
        var stepBuilder = EndStep.Instance;
        return this.AddStep(stepBuilder, null);
    }

    /// <summary>
    /// Adds a sub process to the process.
    /// </summary>
    /// <param name="kernelProcess">The process to add as a step.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessStepBuilder"/></returns>
    public ProcessBuilder AddStepFromProcess(ProcessBuilder kernelProcess, IReadOnlyList<string>? aliases = null)
    {
        kernelProcess.ProcessBuilder = this;
        kernelProcess.HasParentProcess = true;

        return this.AddStep(kernelProcess, aliases);
    }

    /// <summary>
    /// Adds a step to the process.
    /// </summary>
    /// <typeparam name="TStep">The step Type.</typeparam>
    /// <param name="id">The unique Id of the step. If not provided, the name of the step Type will be used.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessMapBuilder"/></returns>
    public ProcessMapBuilder AddMapStepFromType<TStep>(string? id = null, IReadOnlyList<string>? aliases = null) where TStep : KernelProcessStep
    {
        ProcessStepBuilder<TStep> stepBuilder = new(id ?? typeof(TStep).Name, this.ProcessBuilder);

        ProcessMapBuilder mapBuilder = new(stepBuilder);

        return this.AddStep(mapBuilder, aliases);
    }

    /// <summary>
    /// Adds a step to the process and define it's initial user-defined state.
    /// </summary>
    /// <typeparam name="TStep">The step Type.</typeparam>
    /// <typeparam name="TState">The state Type.</typeparam>
    /// <param name="initialState">The initial state of the step.</param>
    /// <param name="id">The unique Id of the step.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessMapBuilder"/></returns>
    public ProcessMapBuilder AddMapStepFromType<TStep, TState>(TState initialState, string id, IReadOnlyList<string>? aliases = null) where TStep : KernelProcessStep<TState> where TState : class, new()
    {
        ProcessStepBuilder<TStep> stepBuilder = new(id, this.ProcessBuilder, initialState: initialState);

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
    /// <param name="id">The unique Id of the proxy step.</param>
    /// <param name="externalTopics">topic names to be used externally.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <returns>An instance of <see cref="ProcessProxyBuilder"/></returns>
    public ProcessProxyBuilder AddProxyStep(string id, IReadOnlyList<string> externalTopics, IReadOnlyList<string>? aliases = null)
    {
        ProcessProxyBuilder proxyBuilder = new(externalTopics, id ?? nameof(KernelProxyStep), this);

        return this.AddStep(proxyBuilder, aliases);
    }

    /// <summary>
    /// Adds a thread to the process.
    /// </summary>
    /// <typeparam name="T">The concrete type of the <see cref="AgentThread"/></typeparam>
    /// <param name="threadName">The name of the thread.</param>
    /// <param name="threadPolicy">The policy that determines the lifetime of the <see cref="AgentThread"/></param>
    /// <param name="threadId">The Id of an existing thread that should be used.</param>
    public ProcessBuilder AddThread<T>(string threadName, KernelProcessThreadLifetime threadPolicy, string? threadId = null) where T : AgentThread
    {
        Verify.NotNullOrWhiteSpace(threadName, nameof(threadName));

        var threadType = typeof(T) switch
        {
            Type t when t == typeof(AzureAIAgentThread) => KernelProcessThreadType.AzureAI,
            _ => throw new ArgumentException($"Unsupported thread type: {typeof(T).Name}")
        };

        var processThread = new KernelProcessAgentThread() { ThreadName = threadName, ThreadId = threadId, ThreadType = threadType };
        this._threads[threadName] = processThread;
        return this;
    }

    /// <summary>
    /// Adds a thread to the process.
    /// </summary>
    /// <param name="threadName">The name of the thread.</param>
    /// <param name="threadPolicy">The policy that determines the lifetime of the <see cref="AgentThread"/></param>
    public ProcessBuilder AddThread(string threadName, KernelProcessThreadLifetime threadPolicy)
    {
        Verify.NotNullOrWhiteSpace(threadName, nameof(threadName));
        Verify.NotNull(threadPolicy, nameof(threadPolicy));

        var processThread = new KernelProcessAgentThread() { ThreadName = threadName, ThreadPolicy = threadPolicy };
        this._threads[threadName] = processThread;
        return this;
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

    /// <inheritdoc/>
    public override ProcessStepEdgeBuilder OnEvent(string eventId, bool isPublic = false)
    {
        if (!this.OutputStepEvents.ContainsKey(eventId))
        {
            throw new InvalidOperationException($"Output Event {eventId} is not emitted publicly by {this.StepId}");
        }

        return base.OnEvent(eventId, isPublic);
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
    /// Creates a <see cref="ListenForBuilder"/> instance to define a listener for incoming messages.
    /// </summary>
    /// <returns></returns>
    public ListenForBuilder ListenFor()
    {
        return new ListenForBuilder(this);
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
            throw new KernelException($"The process named '{this.StepId}' does not expose an event with Id '{eventId}'.");
        }

        if (target is not ProcessFunctionTargetBuilder functionTargetBuilder)
        {
            throw new KernelException($"The process named '{this.StepId}' does not expose an event with Id '{eventId}'.");
        }

        // Targets for external events on a process should be scoped to the process itself rather than the step inside the process.
        var processTarget = functionTargetBuilder with { Step = this, TargetEventId = eventId };
        return processTarget;
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
        var builtSteps = this.BuildWithStateMetadata();

        // Create the process
        KernelProcessState state = new(this.StepId, version: this.Version);
        KernelProcess process = new(state, builtSteps, builtEdges) { Threads = this._threads, UserStateType = this.StateType, Description = this.Description };

        return process;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessBuilder"/> class.
    /// </summary>
    /// <param name="yaml">Workflow definition in YAML format.</param>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    public static Task<KernelProcess?> LoadFromYamlAsync(string yaml)
        => LoadFromYamlInternalAsync(yaml);

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessBuilder"/> class.
    /// </summary>
    /// <param name="yaml">Workflow definition in YAML format.</param>
    /// <param name="stepTypes">Collection of preloaded step types.</param>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    public static Task<KernelProcess?> LoadFromYamlAsync(string yaml, Dictionary<string, Type> stepTypes)
        => LoadFromYamlInternalAsync(yaml, stepTypes: stepTypes);

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessBuilder"/> class.
    /// </summary>
    /// <param name="yaml">Workflow definition in YAML format.</param>
    /// <param name="assemblyPaths">Collection of names or paths of the files that contain the manifest of the assembly.</param>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    public static Task<KernelProcess?> LoadFromYamlAsync(string yaml, List<string> assemblyPaths)
        => LoadFromYamlInternalAsync(yaml, assemblyPaths: assemblyPaths);

    #endregion

    #region private

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessBuilder"/> class.
    /// </summary>
    /// <param name="yaml">Workflow definition in YAML format.</param>
    /// <param name="assemblyPaths">Collection of names or paths of the files that contain the manifest of the assembly.</param>
    /// <param name="stepTypes">Collection of preloaded step types.</param>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    private static async Task<KernelProcess?> LoadFromYamlInternalAsync(
        string yaml,
        List<string>? assemblyPaths = null,
        Dictionary<string, Type>? stepTypes = null)
    {
        Verify.NotNullOrWhiteSpace(yaml);

        try
        {
            var workflow = WorkflowSerializer.DeserializeFromYaml(yaml);
            var builder = new WorkflowBuilder();

            if (stepTypes is not null)
            {
                return await builder.BuildProcessAsync(workflow, yaml, stepTypes).ConfigureAwait(false);
            }
            else if (assemblyPaths is { Count: > 0 })
            {
                var loadedStepTypes = ProcessStepLoader.LoadStepTypesFromAssemblies(assemblyPaths);
                return await builder.BuildProcessAsync(workflow, yaml, loadedStepTypes).ConfigureAwait(false);
            }

            return await builder.BuildProcessAsync(workflow, yaml).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            throw new ArgumentException("Failed to deserialize the process string.", ex);
        }
    }
    #endregion
}
