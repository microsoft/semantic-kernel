// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Builder class for defining Processes that can be exported to Foundry.
/// </summary>
[Experimental("SKEXP0081")]
public class FoundryListenForBuilder
{
    private readonly ProcessBuilder _processBuilder;
    private readonly ListenForBuilder _listenForBuilder;

    /// <summary>
    /// Initializes a new instance of the <see cref="ListenForBuilder"/> class.
    /// </summary>
    /// <param name="processBuilder">The process builder.</param>
    public FoundryListenForBuilder(ProcessBuilder processBuilder)
    {
        this._processBuilder = processBuilder;
        this._listenForBuilder = new ListenForBuilder(processBuilder);
    }

    /// <summary>
    /// Listens for an input event.
    /// </summary>
    /// <param name="eventName"></param>
    /// <param name="condition"></param>
    /// <returns></returns>
    public FoundryListenForTargetBuilder InputEvent(string eventName, KernelProcessEdgeCondition? condition = null)
    {
        return new(this._listenForBuilder.InputEvent(eventName, condition));
    }

    /// <summary>
    /// Defines a message to listen for from a specific process step.
    /// </summary>
    /// <param name="condition"></param>
    /// <returns></returns>
    public FoundryListenForTargetBuilder ProcessStart(KernelProcessEdgeCondition? condition = null)
    {
        return this.InputEvent(ProcessConstants.Declarative.OnEnterEvent, condition);
    }

    /// <summary>
    /// Defines a message to listen for from a specific process step.
    /// </summary>
    /// <param name="messageType">The type of the message.</param>
    /// <param name="from">The process step from which the message originates.</param>
    /// <param name="condition">Condition that must be met for the message to be processed</param>
    /// <returns>A builder for defining the target of the message.</returns>
    public FoundryListenForTargetBuilder Message(string messageType, ProcessStepBuilder from, string? condition = null)
    {
        KernelProcessEdgeCondition? edgeCondition = null;
        if (!string.IsNullOrWhiteSpace(condition))
        {
            edgeCondition = new KernelProcessEdgeCondition(
            (e, s) =>
            {
                var wrapper = new DeclarativeConditionContentWrapper
                {
                    State = s,
                    Event = e.Data
                };

                var result = JMESPathConditionEvaluator.EvaluateCondition(wrapper, condition);
                return Task.FromResult(result);
            }, condition);
        }

        return new(this._listenForBuilder.Message(messageType, from, edgeCondition));
    }

    /// <summary>
    /// Defines a message to listen for from a specific process step.
    /// </summary>
    /// <param name="from">The process step from which the message originates.</param>
    /// <param name="condition">Condition that must be met for the message to be processed</param>
    /// <returns>A builder for defining the target of the message.</returns>
    public FoundryListenForTargetBuilder ResultFrom(ProcessStepBuilder from, string? condition = null)
    {
        KernelProcessEdgeCondition? edgeCondition = null;
        if (!string.IsNullOrWhiteSpace(condition))
        {
            edgeCondition = new KernelProcessEdgeCondition(
            (e, s) =>
            {
                var wrapper = new DeclarativeConditionContentWrapper
                {
                    State = s,
                    Event = e.Data
                };

                var result = JMESPathConditionEvaluator.EvaluateCondition(wrapper, condition);
                return Task.FromResult(result);
            }, condition);
        }

        return new(this._listenForBuilder.OnResult(from, edgeCondition));
    }

    /// <summary>
    /// Listen for the OnEnter event from a specific process step.
    /// </summary>
    /// <param name="from">The process step from which the message originates.</param>
    /// <param name="condition">Condition that must be met for the message to be processed</param>
    /// <returns>A builder for defining the target of the message.</returns>
    public FoundryListenForTargetBuilder OnEnter(ProcessStepBuilder from, string? condition = null)
    {
        return this.Message(ProcessConstants.Declarative.OnEnterEvent, from, condition);
    }

    /// <summary>
    /// Listen for the OnEnter event from a specific process step.
    /// </summary>
    /// <param name="from">The process step from which the message originates.</param>
    /// <param name="condition">Condition that must be met for the message to be processed</param>
    /// <returns>A builder for defining the target of the message.</returns>
    public FoundryListenForTargetBuilder OnExit(ProcessStepBuilder from, string? condition = null)
    {
        return this.Message(ProcessConstants.Declarative.OnExitEvent, from, condition);
    }
}
