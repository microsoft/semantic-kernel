// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process;

internal class LocalAgentStep : LocalStep
{
    private new readonly KernelProcessAgentStep _stepInfo;
    private readonly KernelProcessAgentThread _agentThread;
    private readonly ProcessStateManager _processStateManager;
    private readonly ILogger _logger;

    public LocalAgentStep(KernelProcessAgentStep stepInfo, Kernel kernel, KernelProcessAgentThread agentThread, ProcessStateManager processStateManager, string? parentProcessId = null) : base(stepInfo, kernel, parentProcessId)
    {
        this._stepInfo = stepInfo;
        this._agentThread = agentThread;
        this._processStateManager = processStateManager;
        this._logger = this._kernel.LoggerFactory?.CreateLogger(this._stepInfo.InnerStepType) ?? new NullLogger<LocalAgentStep>();
    }

    protected override ValueTask InitializeStepAsync()
    {
        this._stepInstance = new KernelProcessAgentExecutorInternal(this._stepInfo, this._agentThread, this._processStateManager);
        var kernelPlugin = KernelPluginFactory.CreateFromObject(this._stepInstance, pluginName: this._stepInfo.State.Name);

        // Load the kernel functions
        foreach (KernelFunction f in kernelPlugin)
        {
            this._functions.Add(f.Name, f);
        }
        return default;
    }

    internal override async Task HandleMessageAsync(ProcessMessage message)
    {
        Verify.NotNull(message, nameof(message));

        // Lazy one-time initialization of the step before processing a message
        await this._initializeTask.Value.ConfigureAwait(false);

        string targetFunction = "Invoke";
        KernelArguments arguments = new()
        {
            { "message", message.TargetEventData switch
                {
                    KernelProcessEventData proxyData => proxyData.ToObject(),
                    _ => message.TargetEventData
                }
            },
            { "writtenToThread", message.writtenToThread == this._agentThread.ThreadId }
        };
        if (!this._functions.TryGetValue(targetFunction, out KernelFunction? function) || function == null)
        {
            throw new ArgumentException($"Function Invoke not found in plugin {this.Name}");
        }

        object? result = null;

        // Invoke the function, catching all exceptions that it may throw, and then post the appropriate event.
#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            FunctionResult invokeResult = await this.InvokeFunction(function, this._kernel, arguments).ConfigureAwait(false);
            result = invokeResult.GetValue<object>();
            this.EmitEvent(
                ProcessEvent.Create(
                    result,
                    this._eventNamespace,
                    sourceId: $"{targetFunction}.OnResult",
                    eventVisibility: KernelProcessEventVisibility.Public,
                    writtenToThread: this._agentThread.ThreadId)); // TODO: This is keeping track of the thread the message has been written to, clean it up, name it better, etc. 
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Error in Step {StepName}: {ErrorMessage}", this.Name, ex.Message);
            var processError = KernelProcessError.FromException(ex);
            this.EmitEvent(
                ProcessEvent.Create(
                    processError,
                    this._eventNamespace,
                    sourceId: $"{targetFunction}.OnError",
                    eventVisibility: KernelProcessEventVisibility.Public,
                    isError: true));

            if (this._stepInfo.Actions.DeclarativeActions?.OnError is not null)
            {
                await this.ProcessDeclarativeConditionsAsync(processError, this._stepInfo.Actions.DeclarativeActions.OnError).ConfigureAwait(false);
            }
            if (this._stepInfo.Actions.CodeActions?.OnError is not null)
            {
                this._stepInfo.Actions.CodeActions?.OnError(processError, new KernelProcessStepContext(this));
            }

            return;
        }
#pragma warning restore CA1031 // Do not catch general exception types

        // TODO: Should these be handled within the try or out of it?
        if (this._stepInfo.Actions.DeclarativeActions?.OnComplete is not null)
        {
            await this.ProcessDeclarativeConditionsAsync(result, this._stepInfo.Actions.DeclarativeActions.OnComplete).ConfigureAwait(false);
        }
        if (this._stepInfo.Actions.CodeActions?.OnComplete is not null)
        {
            this._stepInfo.Actions.CodeActions?.OnComplete(result, new KernelProcessStepContext(this));
        }
    }

    private async Task ProcessDeclarativeConditionsAsync(object? result, KernelProcessDeclarativeConditionHandler conditionHandler)
    {
        int executedConditionCount = 0;
        foreach (var onCompleteStateCondition in conditionHandler.EvalConditions ?? [])
        {
            // process state conditions
            await this.ProcessConditionsAsync(result, onCompleteStateCondition).ConfigureAwait(false);
            executedConditionCount++;
            // Test condition
            // TODO: Apply state conditions to the result and emit events
        }

        var alwaysCondition = conditionHandler.AlwaysCondition;
        if (alwaysCondition != null)
        {
            // process semantic conditions
            await this.ProcessConditionsAsync(result, alwaysCondition).ConfigureAwait(false);
            executedConditionCount++;
            // TODO: Apply state conditions to the result and emit events
        }

        var defaultCondition = conditionHandler.DefaultCondition;
        if (executedConditionCount == 0 && defaultCondition != null)
        {
            await this.ProcessConditionsAsync(result, defaultCondition).ConfigureAwait(false);
            executedConditionCount++;
        }
    }

    private async Task ProcessConditionsAsync(object? result, DeclarativeProcessCondition declarativeCondition)
    {
        await this._processStateManager.ReduceAsync((stateType, state) =>
        {
            var stateJson = JsonDocument.Parse(JsonSerializer.Serialize(state));

            if (string.IsNullOrWhiteSpace(declarativeCondition.Expression) || JMESPathConditionEvaluator.EvaluateCondition(state, declarativeCondition.Expression))
            {
                if (declarativeCondition.Updates is not null)
                {
                    foreach (var update in declarativeCondition.Updates)
                    {
                        stateJson = JMESUpdate.UpdateState(stateJson, update.Path, update.Operation, update.Value);
                    }
                }

                if (declarativeCondition.Emits is not null)
                {
                    foreach (var emit in declarativeCondition.Emits)
                    {
                        this.EmitEvent(
                            ProcessEvent.Create(
                                result, // TODO: Use the correct value as defined in emit.Payload
                                this._eventNamespace,
                                sourceId: emit.EventType,
                                eventVisibility: KernelProcessEventVisibility.Public));
                    }
                }
            }

            return Task.FromResult(stateJson.Deserialize(stateType));
        }).ConfigureAwait(false);
    }
}
