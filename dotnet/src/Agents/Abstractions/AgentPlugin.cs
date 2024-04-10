// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Specialization of <see cref="KernelPlugin"/> for <see cref="Agent"/>.
/// </summary>
public sealed class AgentPlugin : KernelPlugin
{
    /// <summary>
    /// $$$
    /// </summary>
    public const string FunctionName = "Ask"; // $$$

    /// <inheritdoc/>
    public override int FunctionCount => 1;

    /// <summary>
    /// $$$
    /// </summary>
    public IReadOnlyList<ChatMessageContent> History
    {
        get => this._chat.History;
        init => this._chat.AddChatMessages(value);
    }

    /// <summary>
    /// $$$
    /// </summary>
    public Agent Agent { get; }

    private KernelFunction Function => this._functionAsk ??= KernelFunctionFactory.CreateFromMethod(this.InvokeAsync, FunctionName, description: this.Description);

    private static readonly Regex s_removeInvalidCharsRegex = new("[^0-9A-Za-z-]");

    private readonly PluginChat _chat;

    private KernelFunction? _functionAsk;

    /// <inheritdoc/>
    public override IEnumerator<KernelFunction> GetEnumerator()
    {
        yield return this.Function;
    }

    /// <inheritdoc/>
    public override bool TryGetFunction(string name, [NotNullWhen(true)] out KernelFunction? function)
    {
        function =
            FunctionName.Equals(name, StringComparison.OrdinalIgnoreCase) ?
            this.Function :
            null;

        return function != null;
    }

    internal AgentPlugin(Agent agent)
        : base(s_removeInvalidCharsRegex.Replace(agent.Name ?? agent.Id, string.Empty), // Uniqueness ???
               agent.Description)
    {
        this.Agent = agent;
        this._chat = new PluginChat(agent);
    }

    /// <summary>
    /// Invoke plugin with optional input.
    /// </summary>
    /// <param name="input">Optional input</param>
    /// <param name="cancellationToken">A cancel token</param>
    /// <returns>The agent response</returns>
    private async Task<string?> InvokeAsync(string? input, CancellationToken cancellationToken = default) // $$$ TYPE / GENERIC (INPUT/OUTPUT) ???
    {
        this._chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

        var message = await this._chat.InvokeAsync(cancellationToken).LastAsync(cancellationToken).ConfigureAwait(false); // $$$ HACK: LAST / BEHAVIOR

        return message.Content;
    }

    /// <summary>
    /// A special nexus for managing the plug-in interaction.
    /// </summary>
    private sealed class PluginChat : AgentChat
    {
        private readonly Agent _agent;

        public new ChatHistory History => base.History;

        public PluginChat(Agent agent)
        {
            this._agent = agent;
        }

        public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            CancellationToken cancellationToken = default) =>
                base.InvokeAgentAsync(this._agent, cancellationToken);
    }
}
