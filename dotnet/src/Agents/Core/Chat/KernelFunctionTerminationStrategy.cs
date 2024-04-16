// Copyright (c) Microsoft. All rights reserved.
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
public class KernelFunctionTerminationStrategy(KernelFunction function) : TerminationStrategy
{
    /// <summary>
    /// A well-known <see cref="KernelArguments"/> key associated with the agent name.
    /// </summary>
    public const string ArgumentKeyAgent = "_agent_";

    /// <summary>
    /// A well-known <see cref="KernelArguments"/> key associated with the chat history.
    /// </summary>
    public const string ArgumentKeyHistory = "_history_";

    /// <summary>
    /// Optional arguments used when invoking <see cref="KernelFunctionTerminationStrategy.Function"/>.
    /// </summary>
    public KernelArguments? Arguments { get; init; }

    /// <summary>
    /// The <see cref="Microsoft.SemanticKernel.Kernel"/> used when invoking <see cref="KernelFunctionTerminationStrategy.Function"/>.
    /// </summary>
    public Kernel Kernel { get; init; } = Kernel.CreateBuilder().Build();

    /// <summary>
    /// The <see cref="KernelFunction"/> invoked as termination criteria.
    /// </summary>
    public KernelFunction Function { get; } = function;

    /// <summary>
    /// A <see cref="FunctionResultProcessor{TResult}"/> responsible for translating the <see cref="FunctionResult"/>
    /// to the termination criteria.
    /// </summary>
    public FunctionResultProcessor<bool> ResultParser { get; init; } = DefaultInstance;

    /// <summary>
    /// The default result parser.  Always signals termination.
    /// </summary>
    private static FunctionResultProcessor<bool> DefaultInstance { get; } = FunctionResultProcessor<bool>.CreateDefaultInstance(true);

    /// <inheritdoc/>
    protected sealed override async Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        KernelArguments originalArguments = this.Arguments ?? [];
        KernelArguments arguments =
            new(originalArguments, originalArguments.ExecutionSettings?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value))
            {
                { ArgumentKeyAgent, agent.Name ?? agent.Id },
                { ArgumentKeyHistory, JsonSerializer.Serialize(history) }, // TODO: GitHub Task #5894
            };

        FunctionResult result = await this.Function.InvokeAsync(this.Kernel, arguments, cancellationToken).ConfigureAwait(false);

        return this.ResultParser.InterpretResult(result);
    }
}
