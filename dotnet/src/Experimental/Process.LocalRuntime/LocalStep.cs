// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a step in a process that is running in-process.
/// </summary>
internal class LocalStep : KernelProcessMessageChannel
{
    /// <summary>
    /// The generic state type for a process step.
    /// </summary>
    private static readonly Type s_genericType = typeof(KernelProcessStep<>);
    private Dictionary<string, Dictionary<string, object?>?>? _inputs;
    private Dictionary<string, Dictionary<string, object?>?>? _initialInputs;
    private bool _isInitialized;
    private ILogger? _logger;

    private readonly Dictionary<string, KernelFunction> _functions = [];
    private readonly Kernel _kernel;
    private readonly Queue<KernelProcessEvent> _eventQueue = new();

    protected readonly string? ParentProcessId;
    protected readonly ILoggerFactory? LoggerFactory;
    protected Dictionary<string, List<KernelProcessEdge>>? _outputEdges;

    public readonly string Name;
    public readonly string Id;

    /// <summary>
    /// Represents a step in a process that is running in-process.
    /// </summary>
    /// <param name="name">Required. The name of the step.</param>
    /// <param name="id">Required. The unique Id of the step.</param>
    /// <param name="kernel">Required. An instance of <see cref="Kernel"/>.</param>
    /// <param name="parentProcessId">Optional. The Id of the parent process if one exists.</param>
    /// <param name="loggerFactory">An instance of <see cref="LoggerFactory"/> used to create loggers.</param>
    public LocalStep(string name, string id, Kernel kernel, string? parentProcessId = null, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(name);
        Verify.NotNullOrWhiteSpace(id);
        Verify.NotNull(kernel);

        this.Name = name;
        this.Id = id;
        this.ParentProcessId = parentProcessId;
        this.LoggerFactory = loggerFactory;
        this._kernel = kernel;
    }

    /// <summary>
    /// Initializes the step with the provided step information.
    /// </summary>
    /// <param name="stepInfo">An instance of <see cref="KernelProcessStepInfo"/></param>
    /// <returns>A <see cref="ValueTask"/></returns>
    /// <exception cref="KernelException"></exception>
    public virtual async ValueTask InitializeAsync(KernelProcessStepInfo stepInfo)
    {
        Verify.NotNull(stepInfo);

        // Only initialize the step once
        if (this._isInitialized)
        {
            return;
        }

        this._isInitialized = true;
        this._logger = this.LoggerFactory?.CreateLogger(stepInfo.InnerStepType) ?? new NullLogger<LocalStep>();
        this._outputEdges = stepInfo.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList());

        // Instantiate an instance of the inner step object
        KernelProcessStep stepInstance = (KernelProcessStep)ActivatorUtilities.CreateInstance(this._kernel.Services, stepInfo.InnerStepType);
        var kernelPlugin = KernelPluginFactory.CreateFromObject(stepInstance, pluginName: stepInfo.State.Name!);

        // Load the kernel functions
        foreach (KernelFunction f in kernelPlugin)
        {
            this._functions.Add(f.Name, f);
        }

        // Initialize the input channels
        this._initialInputs = this.FindInputChannels();
        this._inputs = new(this._initialInputs);

        // Activate the step with user-defined state if needed
        KernelProcessStepState? stateObject = null;
        Type? stateType = null;

        if (TryGetSubtypeOfStatefulStep(stepInfo.InnerStepType, out Type? genericStepType) && genericStepType is not null)
        {
            // The step is a subclass of KernelProcessStep<>, so we need to extract the generic type argument
            // and create an instance of the corresponding KernelProcessStepState<>.
            var userStateType = genericStepType.GetGenericArguments()[0];
            if (userStateType is null)
            {
                throw new KernelException("The generic type argument for the KernelProcessStep subclass could not be determined.");
            }

            stateType = typeof(KernelProcessStepState<>).MakeGenericType(userStateType);
            if (stateType is null)
            {
                throw new KernelException("The generic type argument for the KernelProcessStep subclass could not be determined.");
            }

            stateObject = (KernelProcessStepState?)Activator.CreateInstance(stateType, this.Id, this.Name);
        }
        else
        {
            // The step is a KernelProcessStep with no user-defined state, so we can use the base KernelProcessStepState.
            stateType = typeof(KernelProcessStepState);
            stateObject = new KernelProcessStepState(this.Id, this.Name);
        }

        if (stateObject is null)
        {
            throw new KernelException("The state object for the KernelProcessStep could not be created.");
        }

        MethodInfo? methodInfo = stepInfo.InnerStepType.GetMethod(nameof(KernelProcessStep.ActivateAsync), [stateType]);

        if (methodInfo is null)
        {
            throw new KernelException("The ActivateAsync method for the KernelProcessStep could not be found.");
        }

        methodInfo.Invoke(stepInstance, [stateObject]);
        await stepInstance.ActivateAsync(stateObject).ConfigureAwait(false);
    }

    /// <summary>
    /// Retrieves all events that have been sent to the step.
    /// </summary>
    /// <returns>An <see cref="IEnumerable{T}"/> where T is <see cref="KernelProcessEvent"/></returns>
    public IEnumerable<KernelProcessEvent> GetAllEvents()
    {
        var allEvents = this._eventQueue.ToArray();
        this._eventQueue.Clear();
        return allEvents;
    }

    /// <summary>
    /// Retrieves all edges that are associated with the provided event Id.
    /// </summary>
    /// <param name="eventId">The event Id of interest.</param>
    /// <returns>A <see cref="IEnumerable{T}"/> where T is <see cref="KernelProcessEdge"/></returns>
    public IEnumerable<KernelProcessEdge> GetEdgeForEvent(string eventId)
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
    /// Handles a message that has been sent to the step.
    /// </summary>
    /// <param name="message">The message.</param>
    /// <returns>A <see cref="Task"/></returns>
    /// <exception cref="KernelException"></exception>
    public async Task HandleMessageAsync(LocalMessage message)
    {
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
            this._logger?.LogDebug("No invocable functions, missing keys: {MissingKeys}", missingKeysLog());
            return;
        }

        // A message can only target one function and should not result in a different function being invoked.
        var targetFunction = invocableFunctions.FirstOrDefault((name) => name == message.FunctionName) ??
            throw new InvalidOperationException($"A message targeting function '{message.FunctionName}' has resulted in a function named '{invocableFunctions.First()}' becoming invocable. Are the function names configured correctly?");

        this._logger?.LogDebug("Step with Id `{StepId}` received all required input for function [{TargetFunction}] and is executing.", this.Name, targetFunction);

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
            invokeResult = await this.InvokeFunction(function, this._kernel, arguments).ConfigureAwait(false);
            eventName = $"{targetFunction}.OnResult";
            eventValue = invokeResult?.GetValue<object>();
        }
        catch (Exception ex)
        {
            this._logger?.LogError("Error in Step {StepName}: {ErrorMessage}", this.Name, ex.Message);
            eventName = $"{targetFunction}.OnError";
            eventValue = ex.Message;
        }
        finally
        {
            await this.EmitEventAsync(new KernelProcessEvent { Id = eventName, Data = eventValue }).ConfigureAwait(false);

            // Reset the inputs for the function that was just executed
            this._inputs[targetFunction] = this._initialInputs[targetFunction];
        }
#pragma warning restore CA1031 // Do not catch general exception types
    }

    /// <summary>
    /// Emits an event from the step.
    /// </summary>
    /// <param name="processEvent">The event to emit.</param>
    /// <returns>A <see cref="ValueTask"/></returns>
    public override ValueTask EmitEventAsync(KernelProcessEvent processEvent)
    {
        var scopedEvent = processEvent with { Id = this.StepScopedEventId(processEvent.Id!) };
        this._eventQueue.Enqueue(scopedEvent);
        return default;
    }

    private Task<FunctionResult> InvokeFunction(KernelFunction function, Kernel kernel, KernelArguments arguments)
    {
        return kernel.InvokeAsync(function, arguments: arguments);
    }

    private string StepScopedEventId(string eventType)
    {
        return $"{this.Name}_{this.Id}.{eventType}";
    }

    private Dictionary<string, Dictionary<string, object?>?> FindInputChannels()
    {
        if (this._functions is null)
        {
            throw new InvalidOperationException("The step has not been initialized.");
        }

        Dictionary<string, Dictionary<string, object?>?> inputs = new();
        foreach (var kvp in this._functions)
        {
            inputs[kvp.Key] = new();
            foreach (var param in kvp.Value.Metadata.Parameters)
            {
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
}
