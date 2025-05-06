// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Json.Schema;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Process.Models;
using Json.Schema.Generation;
using Json.More;

namespace Microsoft.SemanticKernel;

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
    /// <param name="threadName"></param>
    /// <param name="nodeInputs"></param>
    /// <exception cref="KernelException"></exception>
    public ProcessAgentBuilder(AgentDefinition agentDefinition, string threadName, NodeInputs nodeInputs) : base(id: agentDefinition.Id ?? agentDefinition.Name ?? throw new KernelException("All declarative agents must have an Id or a Name assigned."))
    {
        Verify.NotNull(agentDefinition);
        this._agentDefinition = agentDefinition;
        this.ThreadName = threadName;
        this.Inputs = nodeInputs;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="ProcessAgentBuilder"/> class.
    /// </summary>
    /// <param name="agentDefinition"></param>
    /// <param name="onComplete"></param>
    /// <param name="onError"></param>
    /// <param name="threadName"></param>
    /// <param name="nodeInputs"></param>
    /// <exception cref="KernelException"></exception>
    public ProcessAgentBuilder(AgentDefinition agentDefinition, Action<object?, KernelProcessStepContext> onComplete, Action<object?, KernelProcessStepContext> onError, string threadName, NodeInputs nodeInputs) : base(agentDefinition.Id ?? throw new KernelException("AgentDefinition Id must be set"))
    {
        Verify.NotNull(agentDefinition);
        this._agentDefinition = agentDefinition;
        this.OnCompleteCodeAction = onComplete;
        this.OnErrorCodeAction = onError;
        this.ThreadName = threadName;
        this.Inputs = nodeInputs;
    }

    #region Public Interface

    /// <summary>
    /// The name of the thread that this agent will run on.
    /// </summary>
    public string ThreadName { get; init; }

    /// <summary>
    /// The optional handler group for OnComplete events.
    /// </summary>
    public Action<object?, KernelProcessStepContext>? OnCompleteCodeAction { get; init; }

    /// <summary>
    /// The optional handler group for OnError events.
    /// </summary>
    public Action<object?, KernelProcessStepContext>? OnErrorCodeAction { get; init; }

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
    public NodeInputs Inputs { get; internal set; }

    /// <summary>
    /// Creates a new instance of the <see cref="DeclarativeEventHandlerGroupBuilder"/> class for the OnComplete event.
    /// </summary>
    /// <returns></returns>
    public DeclarativeEventHandlerGroupBuilder OnComplete(List<DeclarativeProcessCondition> conditions)
    {
        var builder = new DeclarativeEventHandlerGroupBuilder(conditions);
        this.OnCompleteBuilder = builder;
        return builder;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="DeclarativeEventHandlerGroupBuilder"/> class for the OnComplete event.
    /// </summary>
    /// <returns></returns>
    public DeclarativeEventHandlerGroupBuilder OnError(List<DeclarativeProcessCondition> conditions)
    {
        var builder = new DeclarativeEventHandlerGroupBuilder(conditions);
        this.OnErrorBuilder = builder;
        return builder;
    }

    /// <summary>
    /// Sets the inputs for this agent.
    /// </summary>
    /// <param name="schema"></param>
    /// <param name="defaultValue"></param>
    /// <returns></returns>
    public ProcessAgentBuilder WithStructuredInputs(JsonNode schema, object? defaultValue = null)
    {
        Verify.NotNull(schema, nameof(schema));

        this.Inputs = new NodeInputs { Type = AgentInputType.Structured, StructuredInputSchema = schema.ToJsonString(), Default = defaultValue };
        return this;
    }

    /// <summary>
    /// Sets the inputs for this agent.
    /// </summary>
    /// <param name="defaultValue"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    internal ProcessAgentBuilder WithStructuredInput<T>(T? defaultValue = default) where T : class, new()
    {
        return this.WithStructuredInput(typeof(T), defaultValue);
    }

    /// <summary>
    /// Sets the inputs for this agent.
    /// </summary>
    /// <param name="inputType"></param>
    /// <param name="defaultValue"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    internal ProcessAgentBuilder WithStructuredInput(Type inputType, object? defaultValue = null)
    {
        Verify.NotNull(inputType, nameof(inputType));

        // TODO, verify that defaultValue is of the same type as inputType

        var schemaBuilder = new JsonSchemaBuilder();
        JsonSchema schema = schemaBuilder
                    .FromType(inputType)
                    .Build();

        var json = schema.ToJsonDocument().RootElement.ToString();
        this.Inputs = new NodeInputs
        {
            Type = AgentInputType.Structured,
            StructuredInputSchema = json,
            Default = defaultValue
        };

        return this;
    }

    internal ProcessAgentBuilder WithNodeInputs(NodeInputs nodeInputs)
    {
        Verify.NotNull(nodeInputs, nameof(nodeInputs));
        this.Inputs = nodeInputs;
        return this;
    }

    /// <summary>
    /// Sets the inputs for this agent.
    /// </summary>
    /// <param name="path"></param>
    /// <returns></returns>
    public ProcessAgentBuilder WithUserStateInput(string path)
    {
        // TODO: Get schema from state object
        this.Inputs = new NodeInputs { Type = AgentInputType.Structured, Default = $"state.{path}" };
        return this;
    }

    /// <summary>
    /// Sets the inputs for this agent.
    /// </summary>
    /// <returns></returns>
    public ProcessAgentBuilder WithMessageInput()
    {
        this.Inputs = new NodeInputs { Type = AgentInputType.Thread };
        return this;
    }

    #endregion

    internal override KernelProcessStepInfo BuildStep(KernelProcessStepStateMetadata? stateMetadata = null)
    {
        KernelProcessMapStateMetadata? mapMetadata = stateMetadata as KernelProcessMapStateMetadata;

        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());
        var agentActions = new ProcessAgentActions(
            codeActions: new ProcessAgentCodeActions
            {
                OnComplete = this.OnCompleteCodeAction,
                OnError = this.OnCompleteCodeAction
            },
            declarativeActions: new ProcessAgentDeclarativeActions
            {
                OnComplete = this.OnCompleteBuilder?.Build(),
                OnError = this.OnErrorBuilder?.Build()
            });

        var state = new KernelProcessStepState(this.Name, "1.0", this.Id);

        return new KernelProcessAgentStep(this._agentDefinition, agentActions, state, builtEdges, this.ThreadName, this.Inputs);
    }

    internal ProcessFunctionTargetBuilder GetInvokeAgentFunctionTargetBuilder()
    {
        return new ProcessFunctionTargetBuilder(this, functionName: KernelProcessAgentExecutor.Functions.InvokeAgent, parameterName: "message");
    }

    internal ProcessFunctionTargetBuilder GetResetAgentThreadIdFunctionTargetBuilder()
    {
        return new ProcessFunctionTargetBuilder(this, functionName: KernelProcessAgentExecutor.Functions.ResetThreadId);
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
