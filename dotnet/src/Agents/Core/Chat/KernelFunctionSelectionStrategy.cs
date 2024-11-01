﻿// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.Agents.Internal;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Determines agent selection based on the evaluation of a <see cref="KernelFunction"/>.
/// </summary>
/// <param name="function">A <see cref="KernelFunction"/> used for selection criteria</param>
/// <param name="kernel">A kernel instance with services for function execution.</param>
public class KernelFunctionSelectionStrategy(KernelFunction function, Kernel kernel) : SelectionStrategy
{
    /// <summary>
    /// The default value for <see cref="KernelFunctionSelectionStrategy.AgentsVariableName"/>.
    /// </summary>
    public const string DefaultAgentsVariableName = "_agents_";

    /// <summary>
    /// The default value for <see cref="KernelFunctionSelectionStrategy.HistoryVariableName"/>.
    /// </summary>
    public const string DefaultHistoryVariableName = "_history_";

    /// <summary>
    /// The <see cref="KernelArguments"/> key associated with the list of agent names when
    /// invoking <see cref="KernelFunctionSelectionStrategy.Function"/>.
    /// </summary>
    public string AgentsVariableName { get; init; } = DefaultAgentsVariableName;

    /// <summary>
    /// The <see cref="KernelArguments"/> key associated with the chat history when
    /// invoking <see cref="KernelFunctionSelectionStrategy.Function"/>.
    /// </summary>
    public string HistoryVariableName { get; init; } = DefaultHistoryVariableName;

    /// <summary>
    /// Optional arguments used when invoking <see cref="KernelFunctionSelectionStrategy.Function"/>.
    /// </summary>
    public KernelArguments? Arguments { get; init; }

    /// <summary>
    /// The <see cref="Microsoft.SemanticKernel.Kernel"/> used when invoking <see cref="KernelFunctionSelectionStrategy.Function"/>.
    /// </summary>
    public Kernel Kernel => kernel;

    /// <summary>
    /// The <see cref="KernelFunction"/> invoked as selection criteria.
    /// </summary>
    public KernelFunction Function { get; } = function;

    /// <summary>
    /// Optionally specify a <see cref="IChatHistoryReducer"/> to reduce the history.
    /// </summary>
    public IChatHistoryReducer? HistoryReducer { get; init; }

    /// <summary>
    /// When set, will use <see cref="SelectionStrategy.InitialAgent"/> in the event of a failure to select an agent.
    /// </summary>
    public bool UseInitialAgentAsFallback { get; init; }

    /// <summary>
    /// A callback responsible for translating the <see cref="FunctionResult"/>
    /// to the termination criteria.
    /// </summary>
    public Func<FunctionResult, string> ResultParser { get; init; } = (result) => result.GetValue<string>() ?? string.Empty;

    /// <inheritdoc/>
    protected sealed override async Task<Agent> SelectAgentAsync(IReadOnlyList<Agent> agents, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        history = await history.ReduceAsync(this.HistoryReducer, cancellationToken).ConfigureAwait(false);

        KernelArguments originalArguments = this.Arguments ?? [];
        KernelArguments arguments =
            new(originalArguments, originalArguments.ExecutionSettings?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value))
            {
                { this.AgentsVariableName, string.Join(",", agents.Select(a => a.Name)) },
                { this.HistoryVariableName, ChatMessageForPrompt.Format(history) },
            };

        this.Logger.LogKernelFunctionSelectionStrategyInvokingFunction(nameof(NextAsync), this.Function.PluginName, this.Function.Name);

        FunctionResult result = await this.Function.InvokeAsync(this.Kernel, arguments, cancellationToken).ConfigureAwait(false);

        this.Logger.LogKernelFunctionSelectionStrategyInvokedFunction(nameof(NextAsync), this.Function.PluginName, this.Function.Name, result.ValueType);

        string? agentName = this.ResultParser.Invoke(result);
        if (string.IsNullOrEmpty(agentName) && (!this.UseInitialAgentAsFallback || this.InitialAgent == null))
        {
            throw new KernelException("Agent Failure - Strategy unable to determine next agent.");
        }

        Agent? agent = agents.FirstOrDefault(a => (a.Name ?? a.Id) == agentName);
        if (agent == null && this.UseInitialAgentAsFallback)
        {
            agent = this.InitialAgent;
        }

        return agent ?? throw new KernelException($"Agent Failure - Strategy unable to select next agent: {agentName}");
    }
}
