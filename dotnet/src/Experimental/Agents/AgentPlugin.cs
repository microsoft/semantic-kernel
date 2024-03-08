// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Specialization of <see cref="KernelPlugin"/> for <see cref="IAgent"/>
/// </summary>
public abstract class AgentPlugin : KernelPlugin
{
    /// <inheritdoc/>
    protected AgentPlugin(string name, string? description = null)
        : base(name, description)
    {
        // No specialization...
    }

    internal abstract Agent Agent { get; }

    /// <summary>
    /// Invoke plugin with user input
    /// </summary>
    /// <param name="input">The user input</param>
    /// <param name="cancellationToken">A cancel token</param>
    /// <returns>The agent response</returns>
    public async Task<string> InvokeAsync(string input, CancellationToken cancellationToken = default)
    {
        return await this.InvokeAsync(input, arguments: null, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Invoke plugin with user input
    /// </summary>
    /// <param name="input">The user input</param>
    /// <param name="arguments">The arguments</param>
    /// <param name="cancellationToken">A cancel token</param>
    /// <returns>The agent response</returns>
    public async Task<string> InvokeAsync(string input, KernelArguments? arguments, CancellationToken cancellationToken = default)
    {
        arguments ??= new KernelArguments();

        arguments["input"] = input;

        var result = await this.First().InvokeAsync(this.Agent.Kernel, arguments, cancellationToken).ConfigureAwait(false);
        var response = result.GetValue<AgentResponse>()!;

        return response.Message;
    }
}
