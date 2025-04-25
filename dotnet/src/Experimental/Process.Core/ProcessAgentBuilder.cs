// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Json.Schema;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Builder for a process step that represents an agent.
/// </summary>
public class ProcessAgentBuilder : ProcessStepBuilder<KernelProcessAgentExecutor>
{
    private readonly AgentDefinition _agentDefinition;

    /// <summary>
    /// Creates a new instance of the <see cref="ProcessAgentBuilder"/> class.
    /// </summary>
    /// <param name="agentDefinition"></param>
    /// <exception cref="KernelException"></exception>
    public ProcessAgentBuilder(AgentDefinition agentDefinition) : base(id: agentDefinition.Id ?? agentDefinition.Name)
    {
        Verify.NotNull(agentDefinition);
        this._agentDefinition = agentDefinition;
    }

    #region Public Interface

    /// <summary>
    /// The optional handler group for OnComplete events.
    /// </summary>
    public DeclarativeEventHandlerGroupBuilder? OnCompleteBuilder { get; internal set; }

    /// <summary>
    /// The optional handler group for OnError events.
    /// </summary>
    public DeclarativeEventHandlerGroupBuilder? OnErrorBuilder { get; internal set; }

    /// <summary>
    /// The inputs for this agent.
    /// </summary>
    public Dictionary<string, JsonSchema>? Inputs { get; internal set; }

    /// <summary>
    /// Creates a new instance of the <see cref="DeclarativeEventHandlerGroupBuilder"/> class for the OnComplete event.
    /// </summary>
    /// <returns></returns>
    public ProcessAgentBuilder OnComplete(List<DeclarativeProcessCondition> conditions)
    {
        var builder = new DeclarativeEventHandlerGroupBuilder(conditions);
        this.OnCompleteBuilder = builder;
        return this;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="DeclarativeEventHandlerGroupBuilder"/> class for the OnComplete event.
    /// </summary>
    /// <returns></returns>
    public ProcessAgentBuilder OnError(List<DeclarativeProcessCondition> conditions)
    {
        var builder = new DeclarativeEventHandlerGroupBuilder(conditions);
        this.OnErrorBuilder = builder;
        return this;
    }

    /// <summary>
    /// Sets the inputs for this agent.
    /// </summary>
    /// <param name="inputs"></param>
    /// <returns></returns>
    public ProcessAgentBuilder WithInputs(Dictionary<string, JsonSchema> inputs)
    {
        this.Inputs = inputs;
        return this;
    }

    #endregion

    internal override KernelProcessStepInfo BuildStep(KernelProcessStepStateMetadata? stateMetadata = null)
    {
        KernelProcessMapStateMetadata? mapMetadata = stateMetadata as KernelProcessMapStateMetadata;

        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());
        var state = new KernelProcessStepState<KernelProcessAgentExecutorState>(this.Name, "1.0", this.Id);

        return new KernelProcessAgentStep(this._agentDefinition, state, builtEdges)
        {
            OnComplete = this.OnCompleteBuilder?.Build(),
            OnError = this.OnErrorBuilder?.Build(),
            Inputs = this.Inputs,
        };
    }
}

/// <summary>
/// Builder for a group of event handlers.
/// </summary>
public class DeclarativeEventHandlerGroupBuilder
{
    /// <summary>
    /// Creates a new instance of the <see cref="DeclarativeEventHandlerGroupBuilder"/> class.
    /// </summary>
    /// <param name="conditions"></param>
    /// <exception cref="KernelException"></exception>
    public DeclarativeEventHandlerGroupBuilder(List<DeclarativeProcessCondition> conditions)
    {
        if (conditions is not null)
        {
            foreach (var condition in conditions)
            {
                if (condition is null)
                {
                    continue;
                }

                if (condition.Type.Equals("default", StringComparison.OrdinalIgnoreCase))
                {
                    if (this.DefaultHandler is not null)
                    {
                        throw new KernelException("Only one default handler is allowed in a group of event handlers.");
                    }

                    this.DefaultHandler = new DeclarativeEventHandlerBuilder(condition);
                }
                else if (condition.Type.Equals("state", StringComparison.OrdinalIgnoreCase))
                {
                    this.StateHandlers ??= [];
                    this.StateHandlers.Add(new DeclarativeEventHandlerBuilder(condition));
                }
                else if (condition.Type.Equals("semantic", StringComparison.OrdinalIgnoreCase))
                {
                    this.SemanticHandlers ??= [];
                    this.SemanticHandlers.Add(new DeclarativeEventHandlerBuilder(condition));
                }
                else
                {
                    throw new KernelException($"Unknown condition type: {condition.Type}");
                }
            }
        }
    }

    /// <summary>
    /// The optional default handler for this group of event handlers.
    /// </summary>
    public DeclarativeEventHandlerBuilder? DefaultHandler { get; set; }

    /// <summary>
    /// The list of state based handlers for this group of event handlers.
    /// </summary>
    public List<DeclarativeEventHandlerBuilder>? StateHandlers { get; init; } = new List<DeclarativeEventHandlerBuilder>();

    /// <summary>
    /// The list of semantic handlers for this group of event handlers.
    /// </summary>
    public List<DeclarativeEventHandlerBuilder>? SemanticHandlers { get; init; } = new List<DeclarativeEventHandlerBuilder>();

    /// <summary>
    /// Builds the declarative process condition for this event handler group.
    /// </summary>
    /// <returns></returns>
    public KernelProcessDeclarativeConditionHandler Build()
    {
        return new KernelProcessDeclarativeConditionHandler
        {
            Default = this.DefaultHandler?.Build(),
            StateConditions = this.StateHandlers?.Select(h => h.Build()).ToList(),
            SemanticConditions = this.SemanticHandlers?.Select(h => h.Build()).ToList()
        };
    }
}

/// <summary>
/// Builder for events related to declarative steps
/// </summary>
public class DeclarativeEventHandlerBuilder
{
    /// <summary>
    /// The declarative process condition that this event handler is associated with.
    /// </summary>
    public DeclarativeProcessCondition DeclarativeProcessCondition { get; init; }

    /// <summary>
    /// Creates a new instance of the <see cref="DeclarativeEventHandlerBuilder"/> class.
    /// </summary>
    /// <param name="condition"></param>
    public DeclarativeEventHandlerBuilder(DeclarativeProcessCondition condition)
    {
        this.DeclarativeProcessCondition = condition;
    }

    /// <summary>
    /// Builds the declarative process condition for this event handler.
    /// </summary>
    /// <returns></returns>
    public DeclarativeProcessCondition Build()
    {
        return this.DeclarativeProcessCondition;
    }
}
