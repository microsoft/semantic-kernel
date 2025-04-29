// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process;
internal class LocalAgentStep : LocalStep
{
    private readonly AgentFactory _agentFactory;
    private new readonly KernelProcessAgentStep _stepInfo;
    private readonly string? _threadId;

    public LocalAgentStep(KernelProcessAgentStep stepInfo, AgentFactory agentFactory, Kernel kernel, string? parentProcessId = null, string? threadId = null) : base(stepInfo, kernel, parentProcessId)
    {
        this._agentFactory = agentFactory;
        this._stepInfo = stepInfo;
        this._threadId = threadId;
    }

    protected override ValueTask InitializeStepAsync()
    {
        this._stepInstance = new KernelProcessAgentExecutor(this._agentFactory, this._stepInfo, this._threadId);
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
            this.EmitEvent(
                ProcessEvent.Create(
                    invokeResult.GetValue<object>(),
                    this._eventNamespace,
                    sourceId: $"{targetFunction}.OnResult",
                    eventVisibility: KernelProcessEventVisibility.Public));

            if (this._stepInfo.Actions.DeclarativeActions?.OnComplete is not null)
            {
                int executedConditionCount = 0;
                foreach (var onCompleteStateCondition in this._stepInfo.Actions.DeclarativeActions.OnComplete.StateConditions ?? [])
                {
                    executedConditionCount++;
                    // TODO: Apply state conditions to the result and emit events
                }
                foreach (var onCompleteSemanticCondition in this._stepInfo.Actions.DeclarativeActions.OnComplete.SemanticConditions ?? [])
                {
                    executedConditionCount++;
                    // TODO: Apply state conditions to the result and emit events
                }

                var defaultCondition = this._stepInfo.Actions.DeclarativeActions.OnComplete.Default;
                if (executedConditionCount == 0 && defaultCondition != null)
                {
                    // TODO: Apply state conditions to the result and emit events
                    if (defaultCondition.Emits is not null)
                    {
                        foreach (var emit in defaultCondition.Emits)
                        {
                            this.EmitEvent(
                                ProcessEvent.Create(
                                    invokeResult.GetValue<object>(), // TODO: Use the correct value as defined in emit.Payload
                                    this._eventNamespace,
                                    sourceId: emit.EventType,
                                    eventVisibility: KernelProcessEventVisibility.Public));
                        }
                    }
                    if (defaultCondition.Updates is not null)
                    {
                        // TODO: Apply state updates
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
