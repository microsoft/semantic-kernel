// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
=======
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.Agents.Internal;
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
    /// The <see cref="KernelFunction"/> invoked as termination criteria.
    /// </summary>
    public KernelFunction Function { get; } = function;

    /// <summary>
    /// The <see cref="Microsoft.SemanticKernel.Kernel"/> used when invoking <see cref="KernelFunctionTerminationStrategy.Function"/>.
    /// </summary>
    public Kernel Kernel => kernel;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
    /// The <see cref="Microsoft.SemanticKernel.Kernel"/> used when invoking <see cref="KernelFunctionTerminationStrategy.Function"/>.
    /// </summary>
    public Kernel Kernel => kernel;

    /// <summary>
    /// The <see cref="KernelFunction"/> invoked as termination criteria.
    /// </summary>
    public KernelFunction Function { get; } = function;
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    /// <summary>
    /// A callback responsible for translating the <see cref="FunctionResult"/>
    /// to the termination criteria.
    /// </summary>
    public Func<FunctionResult, bool> ResultParser { get; init; } = (_) => true;

<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <inheritdoc/>
    protected sealed override async Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <inheritdoc/>
    protected sealed override async Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
=======
    /// <summary>
    /// Optionally specify a <see cref="IChatHistoryReducer"/> to reduce the history.
    /// </summary>
    public IChatHistoryReducer? HistoryReducer { get; init; }

    /// <inheritdoc/>
    protected sealed override async Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        history = await history.ReduceAsync(this.HistoryReducer, cancellationToken).ConfigureAwait(false);

>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        KernelArguments originalArguments = this.Arguments ?? [];
        KernelArguments arguments =
            new(originalArguments, originalArguments.ExecutionSettings?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value))
            {
                { this.AgentVariableName, agent.Name ?? agent.Id },
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                { this.HistoryVariableName, JsonSerializer.Serialize(history) }, // TODO: GitHub Task #5894
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                { this.HistoryVariableName, JsonSerializer.Serialize(history) }, // TODO: GitHub Task #5894
=======
                { this.HistoryVariableName, ChatMessageForPrompt.Format(history) },
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            };

        this.Logger.LogKernelFunctionTerminationStrategyInvokingFunction(nameof(ShouldAgentTerminateAsync), this.Function.PluginName, this.Function.Name);

        FunctionResult result = await this.Function.InvokeAsync(this.Kernel, arguments, cancellationToken).ConfigureAwait(false);

        this.Logger.LogKernelFunctionTerminationStrategyInvokedFunction(nameof(ShouldAgentTerminateAsync), this.Function.PluginName, this.Function.Name, result.ValueType);

        return this.ResultParser.Invoke(result);
    }
}
