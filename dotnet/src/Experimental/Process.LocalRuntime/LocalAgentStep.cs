// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process;
internal class LocalAgentStep : LocalStep
{
    private readonly AgentFactory _agentFactory;
    private new readonly KernelProcessAgentStep _stepInfo;

    public LocalAgentStep(KernelProcessAgentStep stepInfo, AgentFactory agentFactory, Kernel kernel, string? parentProcessId = null) : base(stepInfo, kernel, parentProcessId)
    {
        this._agentFactory = agentFactory;
        this._stepInfo = stepInfo;
    }

    protected override ValueTask InitializeStepAsync()
    {
        this._stepInstance = new KernelProcessAgentExecutor(this._agentFactory, this._stepInfo);
        return default;
    }

    internal override async Task HandleMessageAsync(ProcessMessage message)
    {
        string targetFunction = "Invoke";
        this._inputs["Invoke"]["message"] = message.TargetEventData;
        KernelArguments arguments = new(this._inputs[targetFunction]!);
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

            if (this._stepInfo.OnComplete is not null)
            {
                foreach (var onCompleteStateCondition in this._stepInfo.OnComplete.StateConditions ?? [])
                {
                    // TODO: Apply state conditions to the result and emit events
                }
                foreach (var onCompleteSemanticCondition in this._stepInfo.OnComplete.SemanticConditions ?? [])
                {
                    // TODO: Apply state conditions to the result and emit events
                }
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
        }
        finally
        {
            // Reset the inputs for the function that was just executed
            this._inputs[targetFunction] = new(this._initialInputs[targetFunction] ?? []);
        }
#pragma warning restore CA1031 // Do not catch general exception types
    }
}
