// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a step in a process that is running in-process.
/// </summary>
internal class LocalStep : IKernelProcessMessageChannel
{
    private readonly Queue<ProcessEvent> _outgoingEventQueue = new();
    protected readonly Lazy<ValueTask> _initializeTask;
    private readonly ILogger _logger;

    protected readonly Kernel _kernel;
    protected readonly Dictionary<string, KernelFunction> _functions = [];
    private readonly Dictionary<string, LocalEdgeGroupProcessor> _edgeGroupProcessors = [];

    protected KernelProcessStepState _stepState;
    protected Dictionary<string, Dictionary<string, object?>?>? _inputs = [];
    protected Dictionary<string, Dictionary<string, object?>?>? _initialInputs = [];
    protected Dictionary<string, List<KernelProcessEdge>> _outputEdges;

    internal KernelProcessStep? _stepInstance = null;
    internal readonly KernelProcessStepInfo _stepInfo;
    internal readonly string _eventNamespace;

    /// <summary>
    /// Represents a step in a process that is running in-process.
    /// </summary>
    /// <param name="stepInfo">An instance of <see cref="KernelProcessStepInfo"/></param>
    /// <param name="kernel">Required. An instance of <see cref="Kernel"/>.</param>
    /// <param name="parentProcessId">Optional. The Id of the parent process if one exists.</param>
    /// <param name="instanceId">Optional: Id of the process if given</param>
    public LocalStep(KernelProcessStepInfo stepInfo, Kernel kernel, string? parentProcessId = null, string? instanceId = null)
    {
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(stepInfo, nameof(stepInfo));

        if (stepInfo is KernelProcess)
        {
            // Only KernelProcess can have a null Id if it is the root process
            stepInfo = stepInfo with { State = stepInfo.State with { RunId = instanceId ?? Guid.NewGuid().ToString() } };
        }
        // For any step that is not a process, step id must already be assigned from parent process in the step state
        Verify.NotNullOrWhiteSpace(stepInfo.State.RunId);

        this._kernel = kernel;
        this._stepInfo = stepInfo;
        this._logger = this._kernel.LoggerFactory?.CreateLogger(this._stepInfo.InnerStepType) ?? new NullLogger<LocalStep>();

        if (stepInfo is not KernelProcess and not KernelProcessMap and not KernelProcessProxy and not KernelProcessAgentStep)
        {
            this.InitializeStepInitialInputs();
        }

        Verify.NotNull(stepInfo.State.RunId);

        this.ParentProcessId = parentProcessId;
        this._stepState = stepInfo.State;
        this._initializeTask = new Lazy<ValueTask>(this.InitializeStepAsync);
        this._outputEdges = this._stepInfo.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList());
        this._eventNamespace = this.Id;
        this._edgeGroupProcessors = this._stepInfo.IncomingEdgeGroups?.ToDictionary(kvp => kvp.Key, kvp => new LocalEdgeGroupProcessor(kvp.Value)) ?? [];
    }

    internal void InitializeStepInitialInputs()
    {
        // Instantiate an instance of the inner step object
        this._stepInstance = this.CreateStepInstance();

        var kernelPlugin = KernelPluginFactory.CreateFromObject(this._stepInstance, pluginName: this._stepInfo.State.StepId);

        // Load the kernel functions
        foreach (KernelFunction f in kernelPlugin)
        {
            this._functions.Add(f.Name, f);
        }

        // Initialize the input channels
        this.PopulateInitialInputs();
    }

    internal virtual KernelProcessStep CreateStepInstance()
    {
        var stepInstance = (KernelProcessStep)ActivatorUtilities.CreateInstance(this._kernel.Services, this._stepInfo.InnerStepType);
        typeof(KernelProcessStep).GetProperty(nameof(KernelProcessStep.StepName))?.SetValue(stepInstance, this._stepInfo.State.RunId);

        return stepInstance;
    }

    internal virtual void PopulateInitialInputs()
    {
        this._initialInputs = this.FindInputChannels(this._functions, this._logger, this.ExternalMessageChannel);
    }

    /// <summary>
    /// The Id of the parent process if one exists.
    /// </summary>
    internal string? ParentProcessId { get; init; }

    /// <summary>
    /// The name of the step.
    /// </summary>
    internal string Name => this._stepInfo.State.StepId!;

    /// <summary>
    /// The Id of the step.
    /// </summary>
    internal string Id => this._stepInfo.State.RunId!;

    /// <summary>
    /// An event proxy that can be used to intercept events emitted by the step.
    /// </summary>
    internal ProcessEventProxy? EventProxy { get; init; }

    internal IExternalKernelProcessMessageChannel? ExternalMessageChannel { get; init; }

    internal ProcessStorageManager? StorageManager { get; init; }

    /// <summary>
    /// Retrieves all events that have been emitted by this step in the previous superstep.
    /// </summary>
    /// <returns>An <see cref="IEnumerable{T}"/> where T is <see cref="KernelProcessEvent"/></returns>
    internal IEnumerable<ProcessEvent> GetAllEvents()
    {
        var allEvents = this._outgoingEventQueue.ToArray();
        this._outgoingEventQueue.Clear();
        return allEvents;
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

    /// <summary>
    /// Emits an event from the step.
    /// </summary>
    /// <param name="processEvent">The event to emit.</param>
    /// <returns>A <see cref="ValueTask"/></returns>
    public ValueTask EmitEventAsync(KernelProcessEvent processEvent)
    {
        Verify.NotNullOrWhiteSpace(processEvent.Id, $"{nameof(processEvent)}.{nameof(KernelProcessEvent.Id)}");

        ProcessEvent emitEvent = ProcessEvent.Create(processEvent, this._eventNamespace);
        if (this.EventProxy?.Invoke(emitEvent) ?? true)
        {
            this.EmitEvent(emitEvent);
        }

        return default;
    }

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
                this._logger.LogWarning("Step {StepName} already has input for {FunctionName}.{Key}, it is being overwritten with a message from Step named '{SourceId}'.", this.Name, message.FunctionName, kvp.Key, message.SourceId);
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
        await this._initializeTask.Value.ConfigureAwait(false);

        if (this._functions is null || this._inputs is null || this._initialInputs is null)
        {
            throw new KernelException("The step has not been initialized.").Log(this._logger);
        }

        string messageLogParameters = string.Join(", ", message.Values.Select(kvp => $"{kvp.Key}: {kvp.Value}"));
        this._logger.LogDebug("Received message from '{SourceId}' targeting function '{FunctionName}' and parameters '{Parameters}'.", message.SourceId, message.FunctionName, messageLogParameters);

        if (!string.IsNullOrEmpty(message.GroupId))
        {
            this._logger.LogDebug("Step {StepName} received message from Step named '{SourceId}' with group Id '{GroupId}'.", this.Name, message.SourceId, message.GroupId);
            if (!this._edgeGroupProcessors.TryGetValue(message.GroupId, out LocalEdgeGroupProcessor? edgeGroupProcessor) || edgeGroupProcessor is null)
            {
                throw new KernelException($"Step {this.Name} received message from Step named '{message.SourceId}' with group Id '{message.GroupId}' that is not registered.").Log(this._logger);
            }

            if (!edgeGroupProcessor.TryGetResult(message, out Dictionary<string, object?>? result))
            {
                // The edge group processor has not received all required messages yet.
                await this.SaveStepEdgeDataAsync().ConfigureAwait(false);
                // Step has not been activated, saving state props before execution
                await this.SaveStepDataAsync().ConfigureAwait(false);
                return;
            }
            // Saving values with updated new edge value
            await this.SaveStepEdgeDataAsync().ConfigureAwait(false);

            // The edge group processor has received all required messages and has produced a result.
            message = message with { Values = result ?? [] };

            // Add the message values to the inputs for the function
            this.AssignStepFunctionParameterValues(message);
        }
        else
        {
            // Add the message values to the inputs for the function
            this.AssignStepFunctionParameterValues(message);

            // Not making use of edge groups, saving edge values only
            await this.SaveStepEdgeDataAsync().ConfigureAwait(false);
        }

        // If we're still waiting for inputs on all of our functions then don't do anything.
        List<string> invocableFunctions = this._inputs.Where(i => i.Value != null && i.Value.All(v => v.Value != null)).Select(i => i.Key).ToList();
        var missingKeys = this._inputs.Where(i => i.Value is null || i.Value.Any(v => v.Value is null));

        if (invocableFunctions.Count == 0)
        {
            string missingKeysLog() => string.Join(", ", missingKeys.Select(k => $"{k.Key}: {string.Join(", ", k.Value?.Where(v => v.Value == null).Select(v => v.Key) ?? [])}"));
            this._logger.LogDebug("No invocable functions, missing keys: {MissingKeys}", missingKeysLog());
            return;
        }

        // A message can only target one function and should not result in a different function being invoked.
        var targetFunction = invocableFunctions.FirstOrDefault((name) => name == message.FunctionName) ??
            throw new InvalidOperationException($"A message targeting function '{message.FunctionName}' has resulted in a function named '{invocableFunctions.First()}' becoming invocable. Are the function names configured correctly?");

        this._logger.LogDebug("Step with Id `{StepId}` received all required input for function [{TargetFunction}] and is executing.", this.Name, targetFunction);

        // Concat all the inputs and run the function
        KernelArguments arguments = new(this._inputs[targetFunction]!);
        if (!this._functions.TryGetValue(targetFunction, out KernelFunction? function) || function == null)
        {
            throw new ArgumentException($"Function {targetFunction} not found in plugin {this.Name}");
        }

        // Invoke the function, catching all exceptions that it may throw, and then post the appropriate event.
#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            // TODO: Process edges for the OnStepEnter event: This feels like a good use for filters in the non-declarative version

            FunctionResult invokeResult = await this.InvokeFunction(function, this._kernel, arguments).ConfigureAwait(false);
            this.EmitEvent(
                ProcessEvent.Create(
                    invokeResult.GetValue<object>(),
                    this._eventNamespace,
                    sourceId: $"{targetFunction}.OnResult",
                    eventVisibility: KernelProcessEventVisibility.Public));

            // TODO: Process edges for the OnStepExit event: This feels like a good use for filters in the non-declarative version
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Error in Step {StepName}: {ErrorMessage}", this.Name, ex.Message);
            this.EmitEvent(
                ProcessEvent.Create(
                    KernelProcessError.FromException(ex),
                    this._eventNamespace,
                    sourceId: $"{targetFunction}.OnError",
                    eventVisibility: KernelProcessEventVisibility.Public,
                    isError: true));
        }
        finally
        {
            // Reset the inputs for the function that was just executed
            this._inputs[targetFunction] = new(this._initialInputs[targetFunction] ?? []);

            await this.SaveStepDataAsync().ConfigureAwait(false);
            if (this._edgeGroupProcessors != null)
            {
                foreach (var item in this._edgeGroupProcessors)
                {
                    item.Value.ClearMessageData();
                }
            }

            await this.SaveStepEdgeDataAsync().ConfigureAwait(false);
        }
#pragma warning restore CA1031 // Do not catch general exception types
    }

    private async Task<Dictionary<string, Dictionary<string, object?>?>?> TryGetCachedInputEdgesValuesAsync()
    {
        var storageKeyValues = this.GetStepStorageKeyValues();
        if (this._initialInputs == null)
        {
            throw new KernelException("Initial Inputs have not been initialize, cannot initialize step properly");
        }

        if (this.StorageManager != null)
        {
            var storedEdgesData = await this.StorageManager.GetStepEdgeDataAsync(storageKeyValues.Item1, storageKeyValues.Item2).ConfigureAwait(false);
            if (this._edgeGroupProcessors != null && storedEdgesData.Item1 && storedEdgesData.Item2 != null)
            {
                foreach (var edgeGroup in this._edgeGroupProcessors)
                {
                    if (storedEdgesData.Item2.TryGetValue(edgeGroup.Key, out Dictionary<string, KernelProcessEventData?>? edgeGroupData) && edgeGroupData != null)
                    {
                        edgeGroup.Value.RehydrateMessageData(edgeGroupData.ToDictionary(edgeGroupData => edgeGroupData.Key, edgeGroupData => edgeGroupData.Value?.ToObject()));
                    }
                }
            }
            // it is not an edge group, it is regular edge
            else if (!storedEdgesData.Item1 && storedEdgesData.Item2 != null)
            {
                Dictionary<string, Dictionary<string, object?>?> inputValuesDictionary = [];
                foreach (var function in this._initialInputs)
                {
                    if (storedEdgesData.Item2.TryGetValue(function.Key, out Dictionary<string, KernelProcessEventData?>? functionParameters) && functionParameters != null)
                    {
                        inputValuesDictionary[function.Key] = [];
                        foreach (var parameter in function.Value ?? [])
                        {
                            if (functionParameters != null && functionParameters.TryGetValue(parameter.Key, out KernelProcessEventData? data) && data != null)
                            {
                                // If the parameter is a KernelProcessEventData, we need to convert it to the original type
                                inputValuesDictionary[function.Key]![parameter.Key] = data.ToObject();
                            }
                            else
                            {
                                inputValuesDictionary[function.Key]![parameter.Key] = parameter.Value;
                            }
                        }
                    }
                }

                return inputValuesDictionary;
            }
        }

        return null;
    }

    private async Task<KernelProcessStepState?> TryGetCachedStepStateAsync(Type stateType, Type? userStateType)
    {
        var storageKeyValues = this.GetStepStorageKeyValues();
        if (this.StorageManager != null)
        {
            var storedMetadataState = await this.StorageManager.GetStepDataAsync(storageKeyValues.Item1, storageKeyValues.Item2).ConfigureAwait(false);
            if (storedMetadataState != null)
            {
                var stateObject = (KernelProcessStepState?)Activator.CreateInstance(stateType, this.Name, storedMetadataState.VersionInfo, this.Id);

                if (userStateType != null)
                {
                    // it is a step with custom state
                    stateType.GetProperty(nameof(KernelProcessStepState<object>.State))?.SetValue(stateObject, storedMetadataState.State);
                }

                stateObject?.InitializeUserState(stateType, userStateType);
                return stateObject;
            }
        }

        return null;
    }

    /// <summary>
    /// Initializes the step with the provided step information.
    /// </summary>
    /// <returns>A <see cref="ValueTask"/></returns>
    /// <exception cref="KernelException"></exception>
    protected virtual async ValueTask InitializeStepAsync()
    {
        if (this._initialInputs == null || this._stepInstance == null)
        {
            throw new KernelException("Initial Inputs have not been initialize, cannot initialize step properly");
        }

        // Populating step function inputs
        this._inputs = await this.TryGetCachedInputEdgesValuesAsync().ConfigureAwait(false) ?? this._initialInputs.ToDictionary(kvp => kvp.Key, kvp => kvp.Value?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value));

        // Activate the step with user-defined state if needed
        Type stateType = this._stepInfo.InnerStepType.ExtractStateType(out Type? userStateType, this._logger);
        KernelProcessStepState? stateObject = await this.TryGetCachedStepStateAsync(stateType, userStateType).ConfigureAwait(false);

        if (stateObject == null)
        {
            // no previous state in storage found, try using the default state instead
            stateObject = this._stepInfo.State;
            stateObject.InitializeUserState(stateType, userStateType);
        }

        if (stateObject is null)
        {
            throw new KernelException("The state object for the KernelProcessStep could not be created.").Log(this._logger);
        }

        MethodInfo methodInfo =
            this._stepInfo.InnerStepType.GetMethod(nameof(KernelProcessStep.ActivateAsync), [stateType]) ??
            throw new KernelException("The ActivateAsync method for the KernelProcessStep could not be found.").Log(this._logger);

        this._stepState = stateObject;

        ValueTask activateTask =
            (ValueTask?)methodInfo.Invoke(this._stepInstance, [stateObject]) ??
            throw new KernelException("The ActivateAsync method failed to complete.").Log(this._logger);

        await this._stepInstance.ActivateAsync(stateObject).ConfigureAwait(false);
        await activateTask.ConfigureAwait(false);
    }

    /// <summary>
    /// Deinitializes the step
    /// </summary>
    public virtual Task DeinitializeStepAsync()
    {
        this._logger.LogInformation("Step {Name} has deinitialized", this.Name);
        return Task.CompletedTask;
    }

    internal (string, string) GetStepStorageKeyValues()
    {
        return (this._stepInfo.State.StepId, this._stepInfo.State.RunId!);
    }

    internal virtual async Task SaveStepDataAsync()
    {
        var storageKeyValues = this.GetStepStorageKeyValues();

        var state = (this._stepInfo with { State = this._stepState }).ToProcessStateMetadata();

        if (state != null && this.StorageManager != null)
        {
            bool stateSaved = await this.StorageManager.SaveStepStateDataAsync(storageKeyValues.Item1, storageKeyValues.Item2, state).ConfigureAwait(false);
            bool parentSaved = await this.StorageManager.SaveParentDataAsync(storageKeyValues.Item1, storageKeyValues.Item2, new() { ParentId = this.ParentProcessId! }).ConfigureAwait(false);
        }
    }

    internal async Task SaveStepEdgeDataAsync()
    {
        bool fromEdgeGroup = false;
        Dictionary<string, Dictionary<string, object?>?>? stepEdgesData = this._inputs;
        if (this._edgeGroupProcessors != null && this._edgeGroupProcessors.Count > 0)
        {
            stepEdgesData = this._edgeGroupProcessors.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.MessageData)!;
            fromEdgeGroup = true;
        }

        var storageKeyValues = this.GetStepStorageKeyValues();
        if (this.StorageManager != null && stepEdgesData != null)
        {
            bool edgeDataSaved = await this.StorageManager.SaveStepEdgeDataAsync(storageKeyValues.Item1, storageKeyValues.Item2, stepEdgesData, fromEdgeGroup).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Invokes the provides function with the provided kernel and arguments.
    /// </summary>
    /// <param name="function">The function to invoke.</param>
    /// <param name="kernel">The kernel to use for invocation.</param>
    /// <param name="arguments">The arguments to invoke with.</param>
    /// <returns>A <see cref="Task"/> containing the result of the function invocation.</returns>
    internal Task<FunctionResult> InvokeFunction(KernelFunction function, Kernel kernel, KernelArguments arguments)
    {
        return kernel.InvokeAsync(function, arguments: arguments);
    }

    /// <summary>
    /// Extracts the current state of the step and returns it as a <see cref="KernelProcessStepInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcessStepInfo"/></returns>
    internal virtual async Task<KernelProcessStepInfo> ToKernelProcessStepInfoAsync()
    {
        // Lazy one-time initialization of the step before extracting state information.
        // This allows state information to be extracted even if the step has not been activated.
        await this._initializeTask.Value.ConfigureAwait(false);

        KernelProcessStepInfo stepInfo = new(this._stepInfo.InnerStepType, this._stepState!, this._outputEdges);
        return stepInfo;
    }

    /// <summary>
    /// Emits an event from the step.
    /// </summary>
    /// <param name="localEvent">The event to emit.</param>
    protected void EmitEvent(ProcessEvent localEvent)
    {
        var scopedEvent = this.ScopedEvent(localEvent);
        this._outgoingEventQueue.Enqueue(scopedEvent);
    }

    /// <summary>
    /// Generates a scoped event for the step.
    /// </summary>
    /// <param name="localEvent">The event.</param>
    /// <returns>A <see cref="ProcessEvent"/> with the correctly scoped namespace.</returns>
    protected ProcessEvent ScopedEvent(ProcessEvent localEvent)
    {
        Verify.NotNull(localEvent, nameof(localEvent));
        return localEvent with { Namespace = this.Id };
    }
}
