// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
using System.Text;
using Json.More;
using Json.Schema;
using Json.Schema.Generation;
using Microsoft.SemanticKernel.Agents;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Builder for a process step that represents an agent.
/// </summary>
public class ProcessAgentBuilder<TProcessState> : ProcessStepBuilder<KernelProcessAgentExecutor> where TProcessState : class, new()
{
    private readonly AgentDefinition _agentDefinition;

    internal Dictionary<string, string> _defaultInputBindings = [];

    /// <summary>
    /// Creates a new instance of the <see cref="ProcessAgentBuilder"/> class.
    /// </summary>
    /// <param name="agentDefinition"></param>
    /// <param name="threadName"></param>
    /// <param name="nodeInputs"></param>
    /// <param name="processBuilder"></param>
    /// <param name="stepId">Id of the step. If not provided, the Id will come from the agent Id.</param>
    /// <exception cref="KernelException"></exception>
    public ProcessAgentBuilder(AgentDefinition agentDefinition, string threadName, Dictionary<string, Type> nodeInputs, ProcessBuilder? processBuilder, string? stepId = null)
        : base(id: stepId ?? agentDefinition.Id ?? agentDefinition.Name ?? throw new KernelException("All declarative agents must have an Id or a Name assigned."), processBuilder)
    {
        Verify.NotNull(agentDefinition);
        this._agentDefinition = agentDefinition;
        this.DefaultThreadName = threadName;
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
    /// <param name="processBuilder"></param>
    /// <exception cref="KernelException"></exception>
    public ProcessAgentBuilder(AgentDefinition agentDefinition, Action<object?, KernelProcessStepContext> onComplete, Action<object?, KernelProcessStepContext> onError, string threadName, Dictionary<string, Type> nodeInputs, ProcessBuilder processBuilder)
        : base(agentDefinition.Id ?? throw new KernelException("AgentDefinition Id must be set"), processBuilder)
    {
        Verify.NotNull(agentDefinition);
        this._agentDefinition = agentDefinition;
        this.OnCompleteCodeAction = onComplete;
        this.OnErrorCodeAction = onError;
        this.DefaultThreadName = threadName;
        this.Inputs = nodeInputs;
    }

    #region Public Interface

    /// <summary>
    /// The optional resolver for the agent ID. This is used to determine the ID of the agent at runtime.
    /// </summary>
    public KernelProcessStateResolver<string?>? AgentIdResolver { get; init; } = null;

    /// <summary>
    /// The name of the thread that this agent will run on.
    /// </summary>
    public string DefaultThreadName { get; init; }

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
    //public NodeInputs Inputs { get; internal set; }
    public Dictionary<string, Type> Inputs { get; internal set; } = [];

    /// <summary>
    /// The human-in-the-loop mode for this agent. This determines whether the agent will wait for human input before proceeding.
    /// </summary>
    public HITLMode HumanInLoopMode { get; init; } = HITLMode.Never;

    /// <summary>
    /// Creates a new instance of the <see cref="DeclarativeEventHandlerGroupBuilder"/> class for the OnComplete event.
    /// </summary>
    /// <returns></returns>
    internal ProcessAgentBuilder<TProcessState> OnComplete(List<DeclarativeProcessCondition> conditions)
    {
        var builder = new DeclarativeEventHandlerGroupBuilder(conditions);
        this.OnCompleteBuilder = builder;
        return this;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="DeclarativeEventHandlerGroupBuilder"/> class for the OnComplete event.
    /// </summary>
    /// <returns></returns>
    public ProcessAgentBuilder<TProcessState> OnError(List<DeclarativeProcessCondition> conditions)
    {
        var builder = new DeclarativeEventHandlerGroupBuilder(conditions);
        this.OnErrorBuilder = builder;
        return this;
    }

    /// <summary>
    /// Sets the inputs for this agent.
    /// </summary>
    /// <param name="inputName"></param>
    /// <param name="inputType"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    internal ProcessAgentBuilder<TProcessState> WithStructuredInput(string inputName, Type inputType)
    {
        Verify.NotNull(inputType, nameof(inputType));

        var schemaBuilder = new JsonSchemaBuilder();
        JsonSchema schema = schemaBuilder
                    .FromType(inputType)
                    .Build();

        var json = schema.ToJsonDocument().RootElement.ToString();
        this.Inputs.Add(inputName, inputType);

        return this;
    }

    /// <summary>
    /// Sets the inputs for this agent.
    /// </summary>
    /// <typeparam name="TProperty"></typeparam>
    /// <param name="propertySelector"></param>
    /// <param name="inputName"></param>
    /// <returns></returns>
    public ProcessAgentBuilder<TProcessState> WithUserStateInput<TProperty>(Expression<Func<TProcessState, TProperty>> propertySelector, string? inputName = null)
    {
        // Extract the property path and type from the expression
        var (_boundPropertyName, _boundPropertyPath, _boundPropertyType) = this.ExtractPropertyInfo(propertySelector);

        this._defaultInputBindings[_boundPropertyName] = _boundPropertyPath;
        this.Inputs.Add(inputName ?? _boundPropertyName, _boundPropertyType);
        return this;
    }

    private (string Name, string Path, Type Type) ExtractPropertyInfo<TState, TProperty>(Expression<Func<TState, TProperty>> propertySelector)
    {
        string propertyName = "";
        var propertyPath = new StringBuilder();
        var expression = propertySelector.Body;
        Type? propertyType = null;

        // Walk up the expression tree to build the property path
        while (expression is MemberExpression memberExpression)
        {
            var member = memberExpression.Member;
            propertyName = member.Name;

            // Add the current member name to the path
            if (propertyPath.Length > 0)
            {
                propertyPath.Insert(0, ".");
            }

            propertyPath.Insert(0, member.Name);

            // If this is our first iteration, save the property type
            if (propertyType == null)
            {
                propertyType = ((PropertyInfo)member).PropertyType;
            }

            // Move to the next level in the expression
            expression = memberExpression.Expression;
        }

        if (expression is ParameterExpression)
        {
            // We've reached the parameter (e.g., 'myState'), which is good
            return (propertyName, propertyPath.ToString(), propertyType ?? typeof(TProperty));
        }

        throw new ArgumentException("Expression must be a property access expression", nameof(propertySelector));
    }

    #endregion

    internal override KernelProcessStepInfo BuildStep(ProcessBuilder processBuilder)
    {
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

        var state = new KernelProcessStepState(this.StepId, "1.0");

        return new KernelProcessAgentStep(this._agentDefinition, agentActions, state, builtEdges, this.DefaultThreadName, this.Inputs) { AgentIdResolver = this.AgentIdResolver, HumanInLoopMode = this.HumanInLoopMode };
    }

    internal ProcessFunctionTargetBuilder GetInvokeAgentFunctionTargetBuilder()
    {
        return new ProcessFunctionTargetBuilder(this, functionName: KernelProcessAgentExecutor.ProcessFunctions.Invoke, parameterName: Constants.MessageParameterName);
    }

    internal static class Constants
    {
        public const string MessageParameterName = "message";
    }
}

/// <summary>
/// Builder for a process step that represents an agent.
/// </summary>
public class ProcessAgentBuilder : ProcessAgentBuilder<ProcessDefaultState>
{
    /// <summary>
    /// Creates a new instance of the <see cref="ProcessAgentBuilder"/> class.
    /// </summary>
    /// <param name="agentDefinition"></param>
    /// <param name="threadName"></param>
    /// <param name="nodeInputs"></param>
    /// <param name="processBuilder"></param>
    /// <param name="stepId"></param>
    public ProcessAgentBuilder(AgentDefinition agentDefinition, string threadName, Dictionary<string, Type> nodeInputs, ProcessBuilder? processBuilder, string? stepId = null) : base(agentDefinition, threadName, nodeInputs, processBuilder, stepId)
    {
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

                if (condition.Type == DeclarativeProcessConditionType.Default)
                {
                    if (this.DefaultHandler is not null)
                    {
                        throw new KernelException("Only one `Default` handler is allowed in a group of event handlers.");
                    }

                    if (!string.IsNullOrWhiteSpace(condition.Expression))
                    {
                        throw new KernelException("`Default` handlers must not have an eval expression.");
                    }

                    this.DefaultHandler = new DeclarativeEventHandlerBuilder(condition);
                }
                else if (condition.Type == DeclarativeProcessConditionType.Eval)
                {
                    this.EvalHandlers ??= [];
                    this.EvalHandlers.Add(new DeclarativeEventHandlerBuilder(condition));
                }
                else if (condition.Type == DeclarativeProcessConditionType.Always)
                {
                    if (this.DefaultHandler is not null)
                    {
                        throw new KernelException("Only one `Always` handler is allowed in a group of event handlers.");
                    }

                    if (!string.IsNullOrWhiteSpace(condition.Expression))
                    {
                        throw new KernelException("`Always` handlers must not have an eval expression.");
                    }

                    this.AlwaysHandler = new DeclarativeEventHandlerBuilder(condition);
                }
                else
                {
                    throw new KernelException($"Unknown condition type: {condition.Type}");
                }
            }
        }
    }

    /// <summary>
    /// The list of semantic handlers for this group of event handlers.
    /// </summary>
    public DeclarativeEventHandlerBuilder? AlwaysHandler { get; init; }

    /// <summary>
    /// The optional default handler for this group of event handlers.
    /// </summary>
    public DeclarativeEventHandlerBuilder? DefaultHandler { get; set; }

    /// <summary>
    /// The list of state based handlers for this group of event handlers.
    /// </summary>
    public List<DeclarativeEventHandlerBuilder>? EvalHandlers { get; init; } = new List<DeclarativeEventHandlerBuilder>();

    /// <summary>
    /// Builds the declarative process condition for this event handler group.
    /// </summary>
    /// <returns></returns>
    public KernelProcessDeclarativeConditionHandler Build()
    {
        return new KernelProcessDeclarativeConditionHandler
        {
            DefaultCondition = this.DefaultHandler?.Build(),
            AlwaysCondition = this.AlwaysHandler?.Build(),
            EvalConditions = this.EvalHandlers?.Select(h => h.Build()).ToList(),
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
