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
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

internal class StepActor : Actor, IStep, IKernelProcessMessageChannel
{
    private const string DaprStepInfoStateName = "DaprStepInfo";
    private const string StepStateJson = "kernelStepStateJson";
    private const string StepStateType = "kernelStepStateType";
    private const string StepParentProcessId = "parentProcessId";
    private const string StepIncomingMessagesState = "incomingMessagesState";

    /// <summary>
    /// The generic state type for a process step.
    /// </summary>
    private static readonly Type s_genericType = typeof(KernelProcessStep<>);

    private readonly Kernel _kernel;
    private readonly Lazy<ValueTask> _activateTask;

    private DaprStepInfo? _stepInfo;
    private ILogger? _logger;
    private string? _eventNamespace;
    private Type? _innerStepType;

    private bool _isInitialized;

    internal Queue<ProcessMessage> _incomingMessages = new();
    internal KernelProcessStepState? _stepState;
    internal Type? _stepStateType;
    internal readonly ILoggerFactory? LoggerFactory;
    internal Dictionary<string, List<KernelProcessEdge>>? _outputEdges;
    internal readonly Dictionary<string, KernelFunction> _functions = [];
    internal Dictionary<string, Dictionary<string, object?>?>? _inputs = [];
    internal Dictionary<string, Dictionary<string, object?>?>? _initialInputs = [];

    internal string? ParentProcessId;

    /// <summary>
    /// Represents a step in a process that is running in-process.
    /// </summary>
    /// <param name="host">The host.</param>
    /// <param name="kernel">Required. An instance of <see cref="Kernel"/>.</param>
    /// <param name="loggerFactory">An instance of <see cref="ILoggerFactory"/> used to create loggers.</param>
    public StepActor(ActorHost host, Kernel kernel, ILoggerFactory? loggerFactory)
        : base(host)
    {
        this.LoggerFactory = loggerFactory;
        this._kernel = kernel;
        this._activateTask = new Lazy<ValueTask>(this.ActivateStepAsync);
    }

    #region Public Actor Methods

    /// <summary>
    /// Initializes the step with the provided step information.
    /// </summary>
    /// <param name="stepInfo">The <see cref="KernelProcessStepInfo"/> instance describing the step.</param>
    /// <param name="parentProcessId">The Id of the parent process if one exists.</param>
    /// <returns>A <see cref="ValueTask"/></returns>
    public async Task InitializeStepAsync(DaprStepInfo stepInfo, string? parentProcessId)
    {
        Verify.NotNull(stepInfo);

        // Only initialize once. This check is required as the actor can be re-activated from persisted state and
        // this should not result in multiple initializations.
        if (this._isInitialized)
        {
            return;
        }

        await this.Int_InitializeStepAsync(stepInfo, parentProcessId).ConfigureAwait(false);

        // Save initial state
        await this.StateManager.AddStateAsync(DaprStepInfoStateName, stepInfo).ConfigureAwait(false);
        await this.StateManager.AddStateAsync(StepParentProcessId, parentProcessId).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Initializes the step with the provided step information.
    /// </summary>
    /// <param name="stepInfo">The <see cref="KernelProcessStepInfo"/> instance describing the step.</param>
    /// <param name="parentProcessId">The Id of the parent process if one exists.</param>
    /// <returns>A <see cref="ValueTask"/></returns>
    public Task Int_InitializeStepAsync(DaprStepInfo stepInfo, string? parentProcessId)
    {
        Verify.NotNull(stepInfo);

        // Attempt to load the inner step type
        this._innerStepType = Type.GetType(stepInfo.InnerStepDotnetType);
        if (this._innerStepType is null)
        {
            var errorMessage = $"Could not load the inner step type '{stepInfo.InnerStepDotnetType}'.";
            this._logger?.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException(errorMessage);
        }

        this.ParentProcessId = parentProcessId;
        this._stepInfo = stepInfo;
        this._stepState = this._stepInfo.State;
        this._logger = this.LoggerFactory?.CreateLogger(this._innerStepType) ?? new NullLogger<StepActor>();
        this._outputEdges = this._stepInfo.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList());
        this._eventNamespace = $"{this._stepInfo.State.Name}_{this._stepInfo.State.Id}";
        this._isInitialized = true;
        return Task.CompletedTask;
    }

    /// <summary>
    /// Triggers the step to dequeue all pending messages and prepare for processing.
    /// </summary>
    /// <returns>A <see cref="Task{Task}"/> where T is an <see cref="int"/> indicating the number of messages that are prepared for processing.</returns>
    public async Task<int> PrepareIncomingMessagesAsync()
    {
        var messageQueue = this.ProxyFactory.CreateActorProxy<IMessageBuffer>(new ActorId(this.Id.GetId()), nameof(MessageBufferActor));
        var incoming = await messageQueue.DequeueAllAsync().ConfigureAwait(false);
        foreach (var message in incoming)
        {
            this._incomingMessages.Enqueue(message);
        }

        // Save the incoming messages to state
        await this.StateManager.SetStateAsync(StepIncomingMessagesState, this._incomingMessages).ConfigureAwait(false);
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
            await this.StateManager.SetStateAsync(StepIncomingMessagesState, this._incomingMessages).ConfigureAwait(false);
            await this.StateManager.SaveStateAsync().ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Extracts the current state of the step and returns it as a <see cref="KernelProcessStepInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcessStepInfo"/></returns>
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
        var existingStepInfo = await this.StateManager.TryGetStateAsync<DaprStepInfo>(DaprStepInfoStateName).ConfigureAwait(false);
        if (existingStepInfo.HasValue)
        {
            // Initialize the step from persisted state
            var parentProcessId = await this.StateManager.GetStateAsync<string>(StepParentProcessId).ConfigureAwait(false);
            await this.Int_InitializeStepAsync(existingStepInfo.Value, parentProcessId).ConfigureAwait(false);

            // Load the persisted incoming messages
            var incomingMessages = await this.StateManager.TryGetStateAsync<Queue<ProcessMessage>>(StepIncomingMessagesState).ConfigureAwait(false);
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
    protected virtual string Name => this._stepInfo?.State.Name ?? throw new KernelException("The Step must be initialized before accessing the Name property.");

    /// <summary>
    /// Emits an event from the step.
    /// </summary>
    /// <param name="processEvent">The event to emit.</param>
    /// <returns>A <see cref="ValueTask"/></returns>
    public ValueTask EmitEventAsync(KernelProcessEvent processEvent)
    {
        return this.EmitEventAsync(ProcessEvent.FromKernelProcessEvent(processEvent, this._eventNamespace!));
    }

    /// <summary>
    /// Handles a <see cref="ProcessMessage"/> that has been sent to the step.
    /// </summary>
    /// <param name="message">The message to process.</param>
    /// <returns>A <see cref="Task"/></returns>
    /// <exception cref="KernelException"></exception>
    internal virtual async Task HandleMessageAsync(ProcessMessage message)
    {
        Verify.NotNull(message);

        // Lazy one-time initialization of the step before processing a message
        await this._activateTask.Value.ConfigureAwait(false);

        if (this._functions is null || this._inputs is null || this._initialInputs is null)
        {
            throw new KernelException("The step has not been initialized.");
        }

        string messageLogParameters = string.Join(", ", message.Values.Select(kvp => $"{kvp.Key}: {kvp.Value}"));
        this._logger?.LogDebug("Received message from '{SourceId}' targeting function '{FunctionName}' and parameters '{Parameters}'.", message.SourceId, message.FunctionName, messageLogParameters);

        // Add the message values to the inputs for the function
        foreach (var kvp in message.Values)
        {
            if (this._inputs.TryGetValue(message.FunctionName, out Dictionary<string, object?>? functionName) && functionName != null && functionName.TryGetValue(kvp.Key, out object? parameterName) && parameterName != null)
            {
                this._logger?.LogWarning("Step {StepName} already has input for {FunctionName}.{Key}, it is being overwritten with a message from Step named '{SourceId}'.", this.Name, message.FunctionName, kvp.Key, message.SourceId);
            }

            if (!this._inputs.TryGetValue(message.FunctionName, out Dictionary<string, object?>? functionParameters))
            {
                this._inputs[message.FunctionName] = new();
                functionParameters = this._inputs[message.FunctionName];
            }

            functionParameters![kvp.Key] = kvp.Value;
        }

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
            throw new InvalidOperationException($"A message targeting function '{message.FunctionName}' has resulted in a function named '{invocableFunctions.First()}' becoming invocable. Are the function names configured correctly?");

        this._logger?.LogInformation("Step with Id `{StepId}` received all required input for function [{TargetFunction}] and is executing.", this.Name, targetFunction);

        // Concat all the inputs and run the function
        KernelArguments arguments = new(this._inputs[targetFunction]!);
        if (!this._functions.TryGetValue(targetFunction, out KernelFunction? function) || function == null)
        {
            throw new ArgumentException($"Function {targetFunction} not found in plugin {this.Name}");
        }

        FunctionResult? invokeResult = null;
        string? eventName = null;
        object? eventValue = null;

        // Invoke the function, catching all exceptions that it may throw, and then post the appropriate event.
#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            this?._logger?.LogInformation("Invoking function {FunctionName} with arguments {Arguments}", targetFunction, arguments);
            invokeResult = await this.InvokeFunction(function, this._kernel, arguments).ConfigureAwait(false);

            this?.Logger?.LogInformation("Function {FunctionName} returned {Result}", targetFunction, invokeResult);
            eventName = $"{targetFunction}.OnResult";
            eventValue = invokeResult?.GetValue<object>();

            // Persist the state after the function has been executed
            var stateJson = JsonSerializer.Serialize(this._stepState, this._stepStateType!);
            await this.StateManager.SetStateAsync(StepStateJson, stateJson).ConfigureAwait(false);
            await this.StateManager.SaveStateAsync().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            this._logger?.LogInformation("Error in Step {StepName}: {ErrorMessage}", this.Name, ex.Message);
            eventName = $"{targetFunction}.OnError";
            eventValue = ex.Message;
        }
        finally
        {
            await this.EmitEventAsync(new KernelProcessEvent { Id = eventName, Data = eventValue }).ConfigureAwait(false);

            // Reset the inputs for the function that was just executed
            this._inputs[targetFunction] = new(this._initialInputs[targetFunction] ?? []);
        }
#pragma warning restore CA1031 // Do not catch general exception types
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
            var errorMessage = "A step cannot be activated before it has been initialized.";
            this._logger?.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException(errorMessage);
        }

        // Instantiate an instance of the inner step object
        KernelProcessStep stepInstance = (KernelProcessStep)ActivatorUtilities.CreateInstance(this._kernel.Services, this._innerStepType!);
        var kernelPlugin = KernelPluginFactory.CreateFromObject(stepInstance, pluginName: this._stepInfo.State.Name!);

        // Load the kernel functions
        foreach (KernelFunction f in kernelPlugin)
        {
            this._functions.Add(f.Name, f);
        }

        // Initialize the input channels
        this._initialInputs = this.FindInputChannels();
        this._inputs = this._initialInputs.ToDictionary(kvp => kvp.Key, kvp => kvp.Value?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value));

        // Activate the step with user-defined state if needed
        KernelProcessStepState? stateObject = null;
        Type? stateType = null;

        // Check if the state has already been persisted
        var stepStateType = await this.StateManager.TryGetStateAsync<string>(StepStateType).ConfigureAwait(false);
        if (stepStateType.HasValue)
        {
            stateType = Type.GetType(stepStateType.Value);
            var stateObjectJson = await this.StateManager.GetStateAsync<string>(StepStateJson).ConfigureAwait(false);
            stateObject = JsonSerializer.Deserialize(stateObjectJson, stateType!) as KernelProcessStepState;
        }
        else
        {
            stateObject = this._stepInfo.State;
            if (TryGetSubtypeOfStatefulStep(this._innerStepType, out Type? genericStepType) && genericStepType is not null)
            {
                // The step is a subclass of KernelProcessStep<>, so we need to extract the generic type argument
                // and create an instance of the corresponding KernelProcessStepState<>.
                var userStateType = genericStepType.GetGenericArguments()[0];
                if (userStateType is null)
                {
                    var errorMessage = "The generic type argument for the KernelProcessStep subclass could not be determined.";
                    this._logger?.LogError("{ErrorMessage}", errorMessage);
                    throw new KernelException(errorMessage);
                }

                stateType = typeof(KernelProcessStepState<>).MakeGenericType(userStateType);
                if (stateType is null)
                {
                    var errorMessage = "The generic type argument for the KernelProcessStep subclass could not be determined.";
                    this._logger?.LogError("{ErrorMessage}", errorMessage);
                    throw new KernelException(errorMessage);
                }
            }
            else
            {
                // The step is a KernelProcessStep with no user-defined state, so we can use the base KernelProcessStepState.
                stateType = typeof(KernelProcessStepState);
            }

            // Persist the state type and type object.
            await this.StateManager.AddStateAsync(StepStateType, stateType.AssemblyQualifiedName).ConfigureAwait(false);
            await this.StateManager.AddStateAsync(StepStateJson, JsonSerializer.Serialize(stateObject)).ConfigureAwait(false);
            await this.StateManager.SaveStateAsync().ConfigureAwait(false);
        }

        if (stateType is null || stateObject is null)
        {
            var errorMessage = "The state object for the KernelProcessStep could not be created.";
            this._logger?.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException(errorMessage);
        }

        MethodInfo? methodInfo = this._innerStepType!.GetMethod(nameof(KernelProcessStep.ActivateAsync), [stateType]);

        if (methodInfo is null)
        {
            var errorMessage = "The ActivateAsync method for the KernelProcessStep could not be found.";
            this._logger?.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException(errorMessage);
        }

        this._stepState = stateObject;
        this._stepStateType = stateType;
        methodInfo.Invoke(stepInstance, [stateObject]);
        await stepInstance.ActivateAsync(stateObject).ConfigureAwait(false);
    }

    /// <summary>
    /// Examines the KernelFunction for the step and creates a dictionary of input channels.
    /// Some types such as KernelProcessStepContext are special and need to be injected into
    /// the function parameter. Those objects are instantiated at this point.
    /// </summary>
    /// <returns><see cref="Dictionary{TKey, TValue}"/></returns>
    /// <exception cref="InvalidOperationException"></exception>
    private Dictionary<string, Dictionary<string, object?>?> FindInputChannels()
    {
        if (this._functions is null)
        {
            var errorMessage = "Internal Error: The step has not been initialized.";
            this._logger?.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException(errorMessage);
        }

        Dictionary<string, Dictionary<string, object?>?> inputs = new();
        foreach (var kvp in this._functions)
        {
            inputs[kvp.Key] = new();
            foreach (var param in kvp.Value.Metadata.Parameters)
            {
                // Optional parameters are should not be added to the input dictionary.
                if (!param.IsRequired)
                {
                    continue;
                }

                // Parameters of type KernelProcessStepContext are injected by the process
                // and are instantiated here.
                if (param.ParameterType == typeof(KernelProcessStepContext))
                {
                    inputs[kvp.Key]![param.Name] = new KernelProcessStepContext(this);
                }
                else
                {
                    inputs[kvp.Key]![param.Name] = null;
                }
            }
        }

        return inputs;
    }

    /// <summary>
    /// Attempts to find an instance of <![CDATA['KernelProcessStep<>']]> within the provided types hierarchy.
    /// </summary>
    /// <param name="type">The type to examine.</param>
    /// <param name="genericStateType">The matching type if found, otherwise null.</param>
    /// <returns>True if a match is found, false otherwise.</returns>
    /// TODO: Move this to a share process utilities project.
    private static bool TryGetSubtypeOfStatefulStep(Type? type, out Type? genericStateType)
    {
        while (type != null && type != typeof(object))
        {
            if (type.IsGenericType && type.GetGenericTypeDefinition() == s_genericType)
            {
                genericStateType = type;
                return true;
            }

            type = type.BaseType;
        }

        genericStateType = null;
        return false;
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
        var scopedEvent = this.ScopedEvent(daprEvent);

        // Emit the event out of the process (this one) if it's visibility is public.
        if (daprEvent.Visibility == KernelProcessEventVisibility.Public)
        {
            if (this.ParentProcessId is not null)
            {
                // Emit the event to the parent process
                var parentProcess = this.ProxyFactory.CreateActorProxy<IEventBuffer>(new ActorId(this.ParentProcessId), nameof(EventBufferActor));
                await parentProcess.EnqueueAsync(scopedEvent).ConfigureAwait(false);
            }
        }

        // Get the edges for the event and queue up the messages to be sent to the next steps.
        foreach (var edge in this.GetEdgeForEvent(daprEvent.Id!))
        {
            ProcessMessage message = ProcessMessageFactory.CreateFromEdge(edge, daprEvent.Data);
            var scopedStepId = this.ScopedActorId(new ActorId(edge.OutputTarget.StepId));
            var targetStep = this.ProxyFactory.CreateActorProxy<IMessageBuffer>(scopedStepId, nameof(MessageBufferActor));
            await targetStep.EnqueueAsync(message).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Generates a scoped event for the step.
    /// </summary>
    /// <param name="daprEvent">The event.</param>
    /// <returns>A <see cref="ProcessEvent"/> with the correctly scoped namespace.</returns>
    internal ProcessEvent ScopedEvent(ProcessEvent daprEvent)
    {
        Verify.NotNull(daprEvent);
        return daprEvent with { Namespace = $"{this.Name}_{this.Id}" };
    }

    /// <summary>
    /// Scopes the Id of a step within the process to the process.
    /// </summary>
    /// <param name="actorId">The actor Id to scope.</param>
    /// <returns>A new <see cref="ActorId"/> which is scoped to the process.</returns>
    private ActorId ScopedActorId(ActorId actorId)
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
