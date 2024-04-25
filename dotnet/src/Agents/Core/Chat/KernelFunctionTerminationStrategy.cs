// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

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
    /// The <see cref="KernelFunction"/> invoked as termination criteria.
    /// </summary>
    public KernelFunction Function { get; } = function;

    /// <summary>
    /// The <see cref="Microsoft.SemanticKernel.Kernel"/> used when invoking <see cref="KernelFunctionTerminationStrategy.Function"/>.
    /// </summary>
    public Kernel Kernel => kernel;

    /// <summary>
    /// A callback responsible for translating the <see cref="FunctionResult"/>
    /// to the termination criteria.
    /// </summary>
    public Func<FunctionResult, bool> ResultParser { get; init; } = (_) => true;

    /// <inheritdoc/>
    protected sealed override async Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        KernelArguments originalArguments = this.Arguments ?? [];
        KernelArguments arguments =
            new(originalArguments, originalArguments.ExecutionSettings?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value))
            {
                { this.AgentVariableName, agent.Name ?? agent.Id },
                { this.HistoryVariableName, JsonSerializer.Serialize(history) }, // TODO: GitHub Task #5894
            };

        FunctionResult result = await this.Function.InvokeAsync(this.Kernel, arguments, cancellationToken).ConfigureAwait(false);

        return this.ResultParser.Invoke(result);
    }
}
