// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
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
        this._stepInstance = new KernelProcessAgentExecutorInternal(this._stepInfo, this._agentThread);
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
        KernelArguments arguments = new() { { "message", message.TargetEventData } };
        if (!this._functions.TryGetValue("Invoke", out KernelFunction? function) || function == null)
        {
            throw new ArgumentException($"Function Invoke not found in plugin {this.Name}");
        }

        // Invoke the function, catching all exceptions that it may throw, and then post the appropriate event.
#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            FunctionResult invokeResult = await this.InvokeFunction(function, this._kernel, arguments).ConfigureAwait(false);
            object? result = invokeResult.GetValue<object>();
            this.EmitEvent(
                ProcessEvent.Create(
                    result,
                    this._eventNamespace,
                    sourceId: $"{targetFunction}.OnResult",
                    eventVisibility: KernelProcessEventVisibility.Public));

            if (this._stepInfo.Actions.DeclarativeActions?.OnComplete is not null)
            {
                int executedConditionCount = 0;
                foreach (var onCompleteStateCondition in this._stepInfo.Actions.DeclarativeActions.OnComplete.StateConditions ?? [])
                {
                    if (onCompleteStateCondition.Expression is null)
                    {
                        throw new ArgumentException($"State condition expression is null in {this.Name}");
                    }

                    executedConditionCount++;
                    await this._processStateManager.ReduceAsync((state) =>
                    {
                        if (JMESPathConditionEvaluator.EvaluateCondition(state, onCompleteStateCondition.Expression))
                        {
                            if (onCompleteStateCondition.Emits is not null)
                            {
                                foreach (var emit in onCompleteStateCondition.Emits)
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

                        return Task.FromResult<object?>(state);
                    }).ConfigureAwait(false);

                    // Test condition
                    // TODO: Apply state conditions to the result and emit events
                }
                foreach (var onCompleteSemanticCondition in this._stepInfo.Actions.DeclarativeActions.OnComplete.SemanticConditions ?? [])
                {
                    executedConditionCount++;

                    //if (onCompleteSemanticCondition.Updates is not null)
                    //{
                    //    await this._processStateManager.ReduceAsync((state) =>
                    //    {
                    //        foreach (var update in onCompleteSemanticCondition.Updates)
                    //        {
                    //            this.UpdateState(state, update.Path, update.Operation.Value, update.Value);
                    //        }

                    //        return Task.FromResult(state);
                    //    }).ConfigureAwait(false);
                    //}
                    // TODO: Apply state conditions to the result and emit events
                }

                var defaultCondition = this._stepInfo.Actions.DeclarativeActions.OnComplete.Default;
                if (executedConditionCount == 0 && defaultCondition != null)
                {
                    //if (defaultCondition.Updates is not null)
                    //{
                    //    await this._processStateManager.ReduceAsync((state) =>
                    //    {
                    //        foreach (var update in defaultCondition.Updates)
                    //        {
                    //            this.UpdateState(state, update.Path, update.Operation.Value, update.Value);
                    //        }

                    //        return Task.FromResult(state);
                    //    }).ConfigureAwait(false);
                    //}

                    // TODO: Apply state conditions to the result and emit events
                    if (defaultCondition.Emits is not null)
                    {
                        foreach (var emit in defaultCondition.Emits)
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
            }
            else if (this._stepInfo.Actions.CodeActions?.OnComplete is not null)
            {
                // invoke the action
                this._stepInfo.Actions.CodeActions?.OnComplete(invokeResult.GetValue<object>(), new KernelProcessStepContext(this));
            }
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

            // TODO: Handle error events and confitions
        }
        finally
        {
        }
#pragma warning restore CA1031 // Do not catch general exception types
    }
}
