// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.Agents.Internal;
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Determines agent selection based on the evaluation of a <see cref="KernelFunction"/>.
/// </summary>
/// <param name="function">A <see cref="KernelFunction"/> used for selection criteria</param>
/// <param name="kernel">A kernel instance with services for function execution.</param>
public class KernelFunctionSelectionStrategy(KernelFunction function, Kernel kernel) : SelectionStrategy
{
    /// <summary>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// The default value for <see cref="KernelFunctionTerminationStrategy.AgentVariableName"/>.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    /// The default value for <see cref="KernelFunctionTerminationStrategy.AgentVariableName"/>.
=======
    /// The default value for <see cref="KernelFunctionSelectionStrategy.AgentsVariableName"/>.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    /// The default value for <see cref="KernelFunctionSelectionStrategy.AgentsVariableName"/>.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
    /// </summary>
    public const string DefaultAgentsVariableName = "_agents_";

    /// <summary>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// The default value for <see cref="KernelFunctionTerminationStrategy.HistoryVariableName"/>.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    /// The default value for <see cref="KernelFunctionTerminationStrategy.HistoryVariableName"/>.
=======
    /// The default value for <see cref="KernelFunctionSelectionStrategy.HistoryVariableName"/>.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    /// The default value for <see cref="KernelFunctionSelectionStrategy.HistoryVariableName"/>.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// The <see cref="Microsoft.SemanticKernel.Kernel"/> used when invoking <see cref="KernelFunctionSelectionStrategy.Function"/>.
    /// </summary>
    public Kernel Kernel => kernel;

    /// <summary>
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    /// The <see cref="KernelFunction"/> invoked as selection criteria.
    /// </summary>
    public KernelFunction Function { get; } = function;

    /// <summary>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    /// When set, will use <see cref="SelectionStrategy.InitialAgent"/> in the event of a failure to select an agent.
    /// </summary>
    public bool UseInitialAgentAsFallback { get; init; }

    /// <summary>
    /// The <see cref="Microsoft.SemanticKernel.Kernel"/> used when invoking <see cref="KernelFunctionSelectionStrategy.Function"/>.
    /// </summary>
    public Kernel Kernel => kernel;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// Optionally specify a <see cref="IChatHistoryReducer"/> to reduce the history.
    /// </summary>
    public IChatHistoryReducer? HistoryReducer { get; init; }

    /// <summary>
    /// When set, will use <see cref="SelectionStrategy.InitialAgent"/> in the event of a failure to select an agent.
    /// </summary>
    public bool UseInitialAgentAsFallback { get; init; }
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

    /// <summary>
    /// A callback responsible for translating the <see cref="FunctionResult"/>
    /// to the termination criteria.
    /// </summary>
    public Func<FunctionResult, string> ResultParser { get; init; } = (result) => result.GetValue<string>() ?? string.Empty;

    /// <inheritdoc/>
    protected sealed override async Task<Agent> SelectAgentAsync(IReadOnlyList<Agent> agents, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
        history = await history.ReduceAsync(this.HistoryReducer, cancellationToken).ConfigureAwait(false);

>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        history = await history.ReduceAsync(this.HistoryReducer, cancellationToken).ConfigureAwait(false);

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        KernelArguments originalArguments = this.Arguments ?? [];
        KernelArguments arguments =
            new(originalArguments, originalArguments.ExecutionSettings?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value))
            {
                { this.AgentsVariableName, string.Join(",", agents.Select(a => a.Name)) },
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                { this.HistoryVariableName, JsonSerializer.Serialize(history) }, // TODO: GitHub Task #5894
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
                { this.HistoryVariableName, JsonSerializer.Serialize(history) }, // TODO: GitHub Task #5894
=======
                { this.HistoryVariableName, ChatMessageForPrompt.Format(history) },
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                { this.HistoryVariableName, ChatMessageForPrompt.Format(history) },
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
