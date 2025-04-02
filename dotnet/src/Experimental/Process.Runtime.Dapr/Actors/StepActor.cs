// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading.Tasks;
using Dapr.Actors;
using Dapr.Actors.Runtime;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Runtime;
using Microsoft.SemanticKernel.Process.Serialization;

namespace Microsoft.SemanticKernel;

internal class StepActor : Actor, IStep, IKernelProcessMessageChannel
{
    private readonly Lazy<ValueTask> _activateTask;

    private DaprStepInfo? _stepInfo;
    private ILogger? _logger;
    private Type? _innerStepType;

    private bool _isInitialized;

    protected readonly Kernel _kernel;
    protected string? _eventNamespace;

    internal Queue<ProcessMessage> _incomingMessages = new();
    internal KernelProcessStepState? _stepState;
    internal Type? _stepStateType;
    internal Dictionary<string, List<KernelProcessEdge>>? _outputEdges;
    internal readonly Dictionary<string, KernelFunction> _functions = [];
    internal Dictionary<string, Dictionary<string, object?>?>? _inputs = [];
    internal Dictionary<string, Dictionary<string, object?>?>? _initialInputs = [];

    internal string? ParentProcessId;
    internal ActorId? EventProxyStepId;

    /// <summary>
    /// Represents a step in a process that is running in-process.
    /// </summary>
    /// <param name="host">The host.</param>
    /// <param name="kernel">Required. An instance of <see cref="Kernel"/>.</param>
    public StepActor(ActorHost host, Kernel kernel)
        : base(host)
    {
        this._kernel = kernel;
        this._activateTask = new Lazy<ValueTask>(this.ActivateStepAsync);
    }

    #region Public Actor Methods

    /// <summary>
    /// Initializes the step with the provided step information.
    /// </summary>
    /// <param name="stepInfo">The <see cref="KernelProcessStepInfo"/> instance describing the step.</param>
    /// <param name="parentProcessId">The Id of the parent process if one exists.</param>
    /// <param name="eventProxyStepId">An optional identifier of an actor requesting to proxy events.</param>
    /// <returns>A <see cref="ValueTask"/></returns>
    public async Task InitializeStepAsync(DaprStepInfo stepInfo, string? parentProcessId, string? eventProxyStepId = null)
    {
        Verify.NotNull(stepInfo, nameof(stepInfo));

        // Only initialize once. This check is required as the actor can be re-activated from persisted state and
        // this should not result in multiple initializations.
        if (this._isInitialized)
        {
            return;
        }

        this.InitializeStep(stepInfo, parentProcessId, eventProxyStepId);

        // Save initial state
        await this.StateManager.AddStateAsync(ActorStateKeys.StepInfoState, stepInfo).ConfigureAwait(false);
        await this.StateManager.AddStateAsync(ActorStateKeys.StepParentProcessId, parentProcessId).ConfigureAwait(false);
        if (!string.IsNullOrWhiteSpace(eventProxyStepId))
        {
            await this.StateManager.AddStateAsync(ActorStateKeys.EventProxyStepId, eventProxyStepId).ConfigureAwait(false);
        }
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Initializes the step with the provided step information.
    /// </summary>
    /// <param name="stepInfo">The <see cref="KernelProcessStepInfo"/> instance describing the step.</param>
    /// <param name="parentProcessId">The Id of the parent process if one exists.</param>
    /// <param name="eventProxyStepId">An optional identifier of an actor requesting to proxy events.</param>
    private void InitializeStep(DaprStepInfo stepInfo, string? parentProcessId, string? eventProxyStepId = null)
    {
        Verify.NotNull(stepInfo, nameof(stepInfo));

        // Attempt to load the inner step type
        this._innerStepType = Type.GetType(stepInfo.InnerStepDotnetType);
        if (this._innerStepType is null)
        {
            throw new KernelException($"Could not load the inner step type '{stepInfo.InnerStepDotnetType}'.").Log(this._logger);
        }

        this.ParentProcessId = parentProcessId;
        this._stepInfo = stepInfo;
        this._stepState = this._stepInfo.State;
        this._logger = this._kernel.LoggerFactory?.CreateLogger(this._innerStepType) ?? new NullLogger<StepActor>();
        this._outputEdges = this._stepInfo.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList());
        this._eventNamespace = $"{this._stepInfo.State.Name}_{this._stepInfo.State.Id}";

        if (!string.IsNullOrWhiteSpace(eventProxyStepId))
        {
            this.EventProxyStepId = new ActorId(eventProxyStepId);
        }

        this._isInitialized = true;
    }

    /// <summary>
    /// Triggers the step to dequeue all pending messages and prepare for processing.
    /// </summary>
    /// <returns>A <see cref="Task{Task}"/> where T is an <see cref="int"/> indicating the number of messages that are prepared for processing.</returns>
    public async Task<int> PrepareIncomingMessagesAsync()
    {
        IMessageBuffer messageQueue = this.ProxyFactory.CreateActorProxy<IMessageBuffer>(new ActorId(this.Id.GetId()), nameof(MessageBufferActor));
        IList<string> incoming = await messageQueue.DequeueAllAsync().ConfigureAwait(false);
        IList<ProcessMessage> messages = incoming.ToProcessMessages();

        foreach (ProcessMessage message in messages)
        {
            this._incomingMessages.Enqueue(message);
        }

        // Save the incoming messages to state
        await this.StateManager.SetStateAsync(ActorStateKeys.StepIncomingMessagesState, this._incomingMessages).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);

        return this._incomingMessages.Count;
    }

    /// <summary>
    /// Triggers the step to process all prepared messages.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    public async Task ProcessIncomingMessagesAsync()
    {
        // Handle all the incoming messages one at a time
        while (this._incomingMessages.Count > 0)
        {
            var message = this._incomingMessages.Dequeue();
            await this.HandleMessageAsync(message).ConfigureAwait(false);

            // Save the incoming messages to state
            await this.StateManager.SetStateAsync(ActorStateKeys.StepIncomingMessagesState, this._incomingMessages).ConfigureAwait(false);
            await this.StateManager.SaveStateAsync().ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Extracts the current state of the step and returns it as a <see cref="DaprStepInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="DaprStepInfo"/></returns>
    public virtual async Task<DaprStepInfo> ToDaprStepInfoAsync()
    {
        // Lazy one-time initialization of the step before extracting state information.
        // This allows state information to be extracted even if the step has not been activated.
        await this._activateTask.Value.ConfigureAwait(false);

        var stepInfo = new DaprStepInfo { InnerStepDotnetType = this._stepInfo!.InnerStepDotnetType!, State = this._stepInfo.State, Edges = this._stepInfo.Edges! };
        return stepInfo;
    }

    /// <summary>
    /// Overrides the base method to initialize the step from persisted state.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    protected override async Task OnActivateAsync()
    {
        var existingStepInfo = await this.StateManager.TryGetStateAsync<DaprStepInfo>(ActorStateKeys.StepInfoState).ConfigureAwait(false);
        if (existingStepInfo.HasValue)
        {
            // Initialize the step from persisted state
            string? parentProcessId = await this.StateManager.GetStateAsync<string>(ActorStateKeys.StepParentProcessId).ConfigureAwait(false);
            string? eventProxyStepId = null;
            if (await this.StateManager.ContainsStateAsync(ActorStateKeys.EventProxyStepId).ConfigureAwait(false))
            {
                eventProxyStepId = await this.StateManager.GetStateAsync<string>(ActorStateKeys.EventProxyStepId).ConfigureAwait(false);
            }
            this.InitializeStep(existingStepInfo.Value, parentProcessId, eventProxyStepId);

            // Load the persisted incoming messages
            var incomingMessages = await this.StateManager.TryGetStateAsync<Queue<ProcessMessage>>(ActorStateKeys.StepIncomingMessagesState).ConfigureAwait(false);
            if (incomingMessages.HasValue)
            {
                this._incomingMessages = incomingMessages.Value;
            }
        }
    }

    #endregion

    /// <summary>
    /// The name of the step.
    /// </summary>
    protected virtual string Name => this._stepInfo?.State.Name ?? throw new KernelException("The Step must be initialized before accessing the Name property.").Log(this._logger);

    /// <summary>
    /// Emits an event from the step.
    /// </summary>
    /// <param name="processEvent">The event to emit.</param>
    /// <returns>A <see cref="ValueTask"/></returns>
    public ValueTask EmitEventAsync(KernelProcessEvent processEvent) => this.EmitEventAsync(ProcessEvent.Create(processEvent, this._eventNamespace!));

    // TODO: this can be moved to shared runtime code, looks almost/same to localRuntime implementation
    internal virtual void AssignStepFunctionParameterValues(ProcessMessage message)
    {
        if (this._functions is null || this._inputs is null || this._initialInputs is null)
        {
            throw new KernelException("The step has not been initialized.").Log(this._logger);
        }

        // Add the message values to the inputs for the function
        foreach (var kvp in message.Values)
        {
            if (this._inputs.TryGetValue(message.FunctionName, out Dictionary<string, object?>? functionName) && functionName != null && functionName.TryGetValue(kvp.Key, out object? parameterName) && parameterName != null)
            {
                this._logger?.LogWarning("Step {StepName} already has input for {FunctionName}.{Key}, it is being overwritten with a message from Step named '{SourceId}'.", this.Name, message.FunctionName, kvp.Key, message.SourceId);
            }

            if (!this._inputs.TryGetValue(message.FunctionName, out Dictionary<string, object?>? functionParameters))
            {
                this._inputs[message.FunctionName] = [];
                functionParameters = this._inputs[message.FunctionName];
            }

            if (kvp.Value is KernelProcessEventData proxyData)
            {
                functionParameters![kvp.Key] = proxyData.ToObject();
            }
            else
            {
                functionParameters![kvp.Key] = kvp.Value;
            }
        }
    }

    /// <summary>
    /// Handles a <see cref="ProcessMessage"/> that has been sent to the step.
    /// </summary>
    /// <param name="message">The message to process.</param>
    /// <returns>A <see cref="Task"/></returns>
    /// <exception cref="KernelException"></exception>
    internal virtual async Task HandleMessageAsync(ProcessMessage message)
    {
        Verify.NotNull(message, nameof(message));

        // Lazy one-time initialization of the step before processing a message
        await this._activateTask.Value.ConfigureAwait(false);

        if (this._functions is null || this._inputs is null || this._initialInputs is null)
        {
            throw new KernelException("The step has not been initialized.").Log(this._logger);
        }

        string messageLogParameters = string.Join(", ", message.Values.Select(kvp => $"{kvp.Key}: {kvp.Value}"));
        this._logger?.LogDebug("Received message from '{SourceId}' targeting function '{FunctionName}' and parameters '{Parameters}'.", message.SourceId, message.FunctionName, messageLogParameters);

        // Add the message values to the inputs for the function
        this.AssignStepFunctionParameterValues(message);

        // If we're still waiting for inputs on all of our functions then don't do anything.
        List<string> invocableFunctions = this._inputs.Where(i => i.Value != null && i.Value.All(v => v.Value != null)).Select(i => i.Key).ToList();
        var missingKeys = this._inputs.Where(i => i.Value is null || i.Value.Any(v => v.Value is null));

        if (invocableFunctions.Count == 0)
        {
            string missingKeysLog() => string.Join(", ", missingKeys.Select(k => $"{k.Key}: {string.Join(", ", k.Value?.Where(v => v.Value == null).Select(v => v.Key) ?? [])}"));
            this._logger?.LogInformation("No invocable functions, missing keys: {MissingKeys}", missingKeysLog());
            return;
        }

        // A message can only target one function and should not result in a different function being invoked.
        var targetFunction = invocableFunctions.FirstOrDefault((name) => name == message.FunctionName) ??
            throw new InvalidOperationException($"A message targeting function '{message.FunctionName}' has resulted in a function named '{invocableFunctions.First()}' becoming invocable. Are the function names configured correctly?").Log(this._logger);

        this._logger?.LogInformation("Step with Id `{StepId}` received all required input for function [{TargetFunction}] and is executing.", this.Name, targetFunction);

        // Concat all the inputs and run the function
        KernelArguments arguments = new(this._inputs[targetFunction]!);
        if (!this._functions.TryGetValue(targetFunction, out KernelFunction? function) || function == null)
        {
            throw new InvalidOperationException($"Function {targetFunction} not found in plugin {this.Name}").Log(this._logger);
        }

        // Invoke the function, catching all exceptions that it may throw, and then post the appropriate event.
#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            this?._logger?.LogInformation("Invoking function {FunctionName} with arguments {Arguments}", targetFunction, arguments);
            FunctionResult invokeResult = await this.InvokeFunction(function, this._kernel, arguments).ConfigureAwait(false);

            this?.Logger?.LogInformation("Function {FunctionName} returned {Result}", targetFunction, invokeResult);

            // Persist the state after the function has been executed
            var stateJson = JsonSerializer.Serialize(this._stepState, this._stepStateType!);
            await this.StateManager.SetStateAsync(ActorStateKeys.StepStateJson, stateJson).ConfigureAwait(false);
            await this.StateManager.SaveStateAsync().ConfigureAwait(false);

            await this.EmitEventAsync(
                ProcessEvent.Create(
                    invokeResult.GetValue<object>(),
                    this._eventNamespace!,
                    sourceId: $"{targetFunction}.OnResult",
                    eventVisibility: KernelProcessEventVisibility.Public)).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            this._logger?.LogError(ex, "Error in Step {StepName}: {ErrorMessage}", this.Name, ex.Message);
            await this.EmitEventAsync(
                ProcessEvent.Create(
                    KernelProcessError.FromException(ex),
                    this._eventNamespace!,
                    sourceId: $"{targetFunction}.OnError",
                    eventVisibility: KernelProcessEventVisibility.Public,
                    isError: true)).ConfigureAwait(false);
        }
        finally
        {
            // Reset the inputs for the function that was just executed
            this._inputs[targetFunction] = new(this._initialInputs[targetFunction] ?? []);
        }
#pragma warning restore CA1031 // Do not catch general exception types
    }

    internal virtual Dictionary<string, Dictionary<string, object?>?> GenerateInitialInputs()
    {
        return this.FindInputChannels(this._functions, this._logger);
    }

    /// <summary>
    /// Initializes the step with the provided step information.
    /// </summary>
    /// <returns>A <see cref="ValueTask"/></returns>
    /// <exception cref="KernelException"></exception>
    protected virtual async ValueTask ActivateStepAsync()
    {
        if (this._stepInfo is null)
        {
            throw new KernelException("A step cannot be activated before it has been initialized.").Log(this._logger);
        }

        // Instantiate an instance of the inner step object
        KernelProcessStep stepInstance = (KernelProcessStep)ActivatorUtilities.CreateInstance(this._kernel.Services, this._innerStepType!);
        var kernelPlugin = KernelPluginFactory.CreateFromObject(stepInstance, pluginName: this._stepInfo.State.Name);

        // Load the kernel functions
        foreach (KernelFunction f in kernelPlugin)
        {
            this._functions.Add(f.Name, f);
        }

        // Initialize the input channels
        this._initialInputs = this.GenerateInitialInputs();
        this._inputs = this._initialInputs.ToDictionary(kvp => kvp.Key, kvp => kvp.Value?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value));

        // Activate the step with user-defined state if needed
        KernelProcessStepState? stateObject = null;
        Type? stateType = null;

        // Check if the state has already been persisted
        var stepStateType = await this.StateManager.TryGetStateAsync<string>(ActorStateKeys.StepStateType).ConfigureAwait(false);
        if (stepStateType.HasValue)
        {
            stateType = Type.GetType(stepStateType.Value);
            var stateObjectJson = await this.StateManager.GetStateAsync<string>(ActorStateKeys.StepStateJson).ConfigureAwait(false);
            stateObject = JsonSerializer.Deserialize(stateObjectJson, stateType!) as KernelProcessStepState;
        }
        else
        {
            stateType = this._innerStepType.ExtractStateType(out Type? userStateType, this._logger);
            stateObject = this._stepInfo.State;

            // Persist the state type and type object.
            await this.StateManager.AddStateAsync(ActorStateKeys.StepStateType, stateType.AssemblyQualifiedName).ConfigureAwait(false);
            await this.StateManager.AddStateAsync(ActorStateKeys.StepStateJson, JsonSerializer.Serialize(stateObject)).ConfigureAwait(false);
            await this.StateManager.SaveStateAsync().ConfigureAwait(false);
        }

        if (stateType is null || stateObject is null)
        {
            throw new KernelException("The state object for the KernelProcessStep could not be created.").Log(this._logger);
        }

        MethodInfo? methodInfo =
            this._innerStepType!.GetMethod(nameof(KernelProcessStep.ActivateAsync), [stateType]) ??
            throw new KernelException("The ActivateAsync method for the KernelProcessStep could not be found.").Log(this._logger);

        this._stepState = stateObject;
        this._stepStateType = stateType;

        ValueTask activateTask =
            (ValueTask?)methodInfo.Invoke(stepInstance, [stateObject]) ??
            throw new KernelException("The ActivateAsync method failed to complete.").Log(this._logger);

        await stepInstance.ActivateAsync(stateObject).ConfigureAwait(false);
        await activateTask.ConfigureAwait(false);
    }

    /// <summary>
    /// Invokes the provides function with the provided kernel and arguments.
    /// </summary>
    /// <param name="function">The function to invoke.</param>
    /// <param name="kernel">The kernel to use for invocation.</param>
    /// <param name="arguments">The arguments to invoke with.</param>
    /// <returns>A <see cref="Task"/> containing the result of the function invocation.</returns>
    private Task<FunctionResult> InvokeFunction(KernelFunction function, Kernel kernel, KernelArguments arguments)
    {
        return kernel.InvokeAsync(function, arguments: arguments);
    }

    /// <summary>
    /// Emits an event from the step.
    /// </summary>
    /// <param name="daprEvent">The event to emit.</param>
    internal async ValueTask EmitEventAsync(ProcessEvent daprEvent)
    {
        // Emit the event out of the process (this one) if it's visibility is public.
        if (daprEvent.Visibility == KernelProcessEventVisibility.Public)
        {
            if (this.ParentProcessId is not null)
            {
                // Emit the event to the parent process
                IEventBuffer parentProcess = this.ProxyFactory.CreateActorProxy<IEventBuffer>(new ActorId(this.ParentProcessId), nameof(EventBufferActor));
                await parentProcess.EnqueueAsync(daprEvent.ToJson()).ConfigureAwait(false);
            }
        }

        if (this.EventProxyStepId != null)
        {
            IEventBuffer proxyBuffer = this.ProxyFactory.CreateActorProxy<IEventBuffer>(this.EventProxyStepId, nameof(EventBufferActor));
            await proxyBuffer.EnqueueAsync(daprEvent.ToJson()).ConfigureAwait(false);
        }

        // Get the edges for the event and queue up the messages to be sent to the next steps.
        bool foundEdge = false;
        foreach (KernelProcessEdge edge in this.GetEdgeForEvent(daprEvent.QualifiedId))
        {
            ProcessMessage message = ProcessMessageFactory.CreateFromEdge(edge, daprEvent.SourceId, daprEvent.Data);
            ActorId scopedStepId = this.ScopedActorId(new ActorId(edge.OutputTarget.StepId));
            IMessageBuffer targetStep = this.ProxyFactory.CreateActorProxy<IMessageBuffer>(scopedStepId, nameof(MessageBufferActor));
            await targetStep.EnqueueAsync(message.ToJson()).ConfigureAwait(false);
            foundEdge = true;
        }

        // Error event was raised with no edge to handle it, send it to the global error event buffer.
        if (!foundEdge && daprEvent.IsError && this.ParentProcessId != null)
        {
            IEventBuffer parentProcess1 = this.ProxyFactory.CreateActorProxy<IEventBuffer>(ProcessActor.GetScopedGlobalErrorEventBufferId(this.ParentProcessId), nameof(EventBufferActor));
            await parentProcess1.EnqueueAsync(daprEvent.ToJson()).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Scopes the Id of a step within the process to the process.
    /// </summary>
    /// <param name="actorId">The actor Id to scope.</param>
    /// <returns>A new <see cref="ActorId"/> which is scoped to the process.</returns>
    internal ActorId ScopedActorId(ActorId actorId)
    {
        return new ActorId($"{this.ParentProcessId}.{actorId.GetId()}");
    }

    /// <summary>
    /// Retrieves all edges that are associated with the provided event Id.
    /// </summary>
    /// <param name="eventId">The event Id of interest.</param>
    /// <returns>A <see cref="IEnumerable{T}"/> where T is <see cref="KernelProcessEdge"/></returns>
    internal IEnumerable<KernelProcessEdge> GetEdgeForEvent(string eventId)
    {
        if (this._outputEdges is null)
        {
            return [];
        }

        if (this._outputEdges.TryGetValue(eventId, out List<KernelProcessEdge>? edges) && edges is not null)
        {
            return edges;
        }

        return [];
    }
}
