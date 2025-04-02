// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a step in a process that is running in-process.
/// </summary>
internal class LocalStep : IKernelProcessMessageChannel
{
    private readonly Queue<ProcessEvent> _outgoingEventQueue = new();
    private readonly Lazy<ValueTask> _initializeTask;
    private readonly ILogger _logger;

    protected readonly Kernel _kernel;
    protected readonly Dictionary<string, KernelFunction> _functions = [];

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
    public LocalStep(KernelProcessStepInfo stepInfo, Kernel kernel, string? parentProcessId = null)
    {
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(stepInfo, nameof(stepInfo));

        // This special handling will be removed with the refactoring of KernelProcessState
        if (string.IsNullOrEmpty(stepInfo.State.Id) && stepInfo is KernelProcess)
        {
            stepInfo = stepInfo with { State = stepInfo.State with { Id = Guid.NewGuid().ToString() } };
        }

        Verify.NotNull(stepInfo.State.Id);

        this.ParentProcessId = parentProcessId;
        this._kernel = kernel;
        this._stepInfo = stepInfo;
        this._stepState = stepInfo.State;
        this._initializeTask = new Lazy<ValueTask>(this.InitializeStepAsync);
        this._logger = this._kernel.LoggerFactory?.CreateLogger(this._stepInfo.InnerStepType) ?? new NullLogger<LocalStep>();
        this._outputEdges = this._stepInfo.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList());
        this._eventNamespace = $"{this._stepInfo.State.Name}_{this._stepInfo.State.Id}";
    }

    /// <summary>
    /// The Id of the parent process if one exists.
    /// </summary>
    internal string? ParentProcessId { get; init; }

    /// <summary>
    /// The name of the step.
    /// </summary>
    internal string Name => this._stepInfo.State.Name!;

    /// <summary>
    /// The Id of the step.
    /// </summary>
    internal string Id => this._stepInfo.State.Id!;

    /// <summary>
    /// An event proxy that can be used to intercept events emitted by the step.
    /// </summary>
    internal ProcessEventProxy? EventProxy { get; init; }

    internal IExternalKernelProcessMessageChannel? ExternalMessageChannel { get; init; }

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

        // Add the message values to the inputs for the function
        this.AssignStepFunctionParameterValues(message);

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
            FunctionResult invokeResult = await this.InvokeFunction(function, this._kernel, arguments).ConfigureAwait(false);
            this.EmitEvent(
                ProcessEvent.Create(
                    invokeResult.GetValue<object>(),
                    this._eventNamespace,
                    sourceId: $"{targetFunction}.OnResult",
                    eventVisibility: KernelProcessEventVisibility.Public));
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
        }
#pragma warning restore CA1031 // Do not catch general exception types
    }

    /// <summary>
    /// Initializes the step with the provided step information.
    /// </summary>
    /// <returns>A <see cref="ValueTask"/></returns>
    /// <exception cref="KernelException"></exception>
    protected virtual async ValueTask InitializeStepAsync()
    {
        // Instantiate an instance of the inner step object
        this._stepInstance = (KernelProcessStep)ActivatorUtilities.CreateInstance(this._kernel.Services, this._stepInfo.InnerStepType);
        var kernelPlugin = KernelPluginFactory.CreateFromObject(this._stepInstance, pluginName: this._stepInfo.State.Name);

        // Load the kernel functions
        foreach (KernelFunction f in kernelPlugin)
        {
            this._functions.Add(f.Name, f);
        }

        // Initialize the input channels
        this._initialInputs = this.FindInputChannels(this._functions, this._logger, this.ExternalMessageChannel);
        this._inputs = this._initialInputs.ToDictionary(kvp => kvp.Key, kvp => kvp.Value?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value));

        // Activate the step with user-defined state if needed
        Type stateType = this._stepInfo.InnerStepType.ExtractStateType(out Type? userStateType, this._logger);
        KernelProcessStepState stateObject = this._stepInfo.State;
        stateObject.InitializeUserState(stateType, userStateType);

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
        return localEvent with { Namespace = $"{this.Name}_{this.Id}" };
    }
}
