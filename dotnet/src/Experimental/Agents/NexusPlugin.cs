// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents;

#pragma warning disable IDE0290 // Use primary constructor

/// <summary>
/// Specialization of <see cref="KernelPlugin"/> for <see cref="IAgent"/>
/// </summary>
public sealed class NexusPlugin : KernelPlugin
{
    /// <summary>
    /// $$$
    /// </summary>
    public const string FunctionName = "AskAgent";

    /// <inheritdoc/>
    public override int FunctionCount => 1;

    /// <summary>
    /// $$$
    /// </summary>
    public ChatHistory History => this._chat.History; // $$$ TYPE ???

    /// <summary>
    /// $$$
    /// </summary>
    public Agent Agent { get; }

    private static readonly Regex s_removeInvalidCharsRegex = new("[^0-9A-Za-z-]");

    private readonly PluginChat _chat;
    private readonly KernelFunction _functionAsk;

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="history"></param>
    public void Bind(ChatHistory history) // $$$ ROUGH
    {
        this._chat.Bind(history);
    }

    /// <inheritdoc/>
    public override IEnumerator<KernelFunction> GetEnumerator()
    {
        yield return this._functionAsk;
    }

    /// <inheritdoc/>
    public override bool TryGetFunction(string name, [NotNullWhen(true)] out KernelFunction? function)
    {
        function =
            FunctionName.Equals(name, StringComparison.OrdinalIgnoreCase) ?
            this._functionAsk :
            null;

        return function != null;
    }

    internal NexusPlugin(Agent agent)
        : base(s_removeInvalidCharsRegex.Replace(agent.Name ?? agent.Id, string.Empty), // Uniqueness ???
               agent.Description)
    {
        this.Agent = agent;
        this._chat = new PluginChat(agent);
        this._functionAsk = KernelFunctionFactory.CreateFromMethod(this.InvokeAsync, FunctionName, description: this.Description);
    }

    /// <summary>
    /// Invoke plugin with optional input.
    /// </summary>
    /// <param name="input">Optional input</param>
    /// <param name="cancellationToken">A cancel token</param>
    /// <returns>The agent response</returns>
    private async Task<string?> InvokeAsync(string? input, CancellationToken cancellationToken = default)
    {
        var message = await this._chat.InvokeAsync(input, cancellationToken).LastAsync(cancellationToken).ConfigureAwait(false);

        return message.Content;
    }

    /// <summary>
    /// A special nexus for managing the plug-in interaction.
    /// </summary>
    private sealed class PluginChat : AgentNexus
    {
        private readonly Agent _agent;

        public PluginChat(Agent agent)
        {
            this._agent = agent;
        }

        public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            string? input = null,
            CancellationToken cancellationToken = default) =>
                base.InvokeAgentAsync(this._agent, CreateUserMessage(input), cancellationToken);
    }
}
