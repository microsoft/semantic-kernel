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
/// Signals termination based on the evaluation of a <see cref="KernelFunction"/>.
/// </summary>
/// <param name="function">A <see cref="KernelFunction"/> used for termination criteria</param>
/// <param name="kernel">A kernel instance with services for function execution.</param>
public class KernelFunctionTerminationStrategy(KernelFunction function, Kernel kernel) : TerminationStrategy
{
    /// <summary>
    /// The default value for <see cref="KernelFunctionTerminationStrategy.AgentVariableName"/>.
    /// </summary>
    public const string DefaultAgentVariableName = "_agent_";

    /// <summary>
    /// The default value for <see cref="KernelFunctionTerminationStrategy.HistoryVariableName"/>.
    /// </summary>
    public const string DefaultHistoryVariableName = "_history_";

    /// <summary>
    /// The <see cref="KernelArguments"/> key associated with the agent name when
    /// invoking <see cref="KernelFunctionSelectionStrategy.Function"/>.
    /// </summary>
    public string AgentVariableName { get; init; } = DefaultAgentVariableName;

    /// <summary>
    /// The <see cref="KernelArguments"/> key associated with the chat history when
    /// invoking <see cref="KernelFunctionTerminationStrategy.Function"/>.
    /// </summary>
    public string HistoryVariableName { get; init; } = DefaultHistoryVariableName;

    /// <summary>
    /// Optional arguments used when invoking <see cref="KernelFunctionTerminationStrategy.Function"/>.
    /// </summary>
    public KernelArguments? Arguments { get; init; }

    /// <summary>
    /// The <see cref="Microsoft.SemanticKernel.Kernel"/> used when invoking <see cref="KernelFunctionTerminationStrategy.Function"/>.
    /// </summary>
    public Kernel Kernel => kernel;

    /// <summary>
    /// The <see cref="KernelFunction"/> invoked as termination criteria.
    /// </summary>
    public KernelFunction Function { get; } = function;

    /// <summary>
    /// A callback responsible for translating the <see cref="FunctionResult"/>
    /// to the termination criteria.
    /// </summary>
    public Func<FunctionResult, bool> ResultParser { get; init; } = (_) => true;

    /// <summary>
    /// Optionally specify a <see cref="IChatHistoryReducer"/> to reduce the history.
    /// </summary>
    public IChatHistoryReducer? HistoryReducer { get; init; }

    /// <inheritdoc/>
    protected sealed override async Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        history = await history.ReduceAsync(this.HistoryReducer, cancellationToken).ConfigureAwait(false);

        KernelArguments originalArguments = this.Arguments ?? [];
        KernelArguments arguments =
            new(originalArguments, originalArguments.ExecutionSettings?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value))
            {
                { this.AgentVariableName, agent.Name ?? agent.Id },
                { this.HistoryVariableName, ChatMessageForPrompt.Format(history) },
            };

        this.Logger.LogKernelFunctionTerminationStrategyInvokingFunction(nameof(ShouldAgentTerminateAsync), this.Function.PluginName, this.Function.Name);

        FunctionResult result = await this.Function.InvokeAsync(this.Kernel, arguments, cancellationToken).ConfigureAwait(false);

        this.Logger.LogKernelFunctionTerminationStrategyInvokedFunction(nameof(ShouldAgentTerminateAsync), this.Function.PluginName, this.Function.Name, result.ValueType);

        return this.ResultParser.Invoke(result);
    }
}
