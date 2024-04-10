// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Specialization of <see cref="KernelPlugin"/> for <see cref="Agent"/>.
/// </summary>
internal sealed class AgentPlugin : KernelPlugin
{
    /// <summary>
    /// The agent function name.
    /// </summary>
    public const string FunctionName = "AskAgent";

    /// <inheritdoc/>
    public override int FunctionCount => 1;

    private static readonly Regex s_removeInvalidCharsRegex = new("[^0-9A-Za-z_]");

    private KernelFunction Function => this._functionAsk ??= KernelFunctionFactory.CreateFromMethod(this.InvokeAsync, FunctionName, description: this.Description);

    private readonly Agent _agent;
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
        : base(GeneratePluginName(agent), agent.Description)
    {
        this._agent = agent;
    }

    private static string GeneratePluginName(Agent agent)
    {
        string identifier = s_removeInvalidCharsRegex.Replace(agent.Name ?? agent.Id, string.Empty);
        return $"{agent.GetType().Name}_{identifier}";
    }

    /// <summary>
    /// Invoke plugin with optional input.
    /// </summary>
    /// <param name="input">Optional input</param>
    /// <param name="arguments">Context arguments.</param>
    /// <param name="logger">The logger, if provided.</param>
    /// <param name="cancellationToken">A cancel token</param>
    /// <returns>The agent response</returns>
    private async Task<IReadOnlyList<ChatMessageContent>> InvokeAsync(
        string? input,
        KernelArguments arguments,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        PluginChat chat = new(this._agent);

        if (!string.IsNullOrEmpty(input))
        {
            chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));
        }

        return await chat.InvokeAsync(cancellationToken).ToArrayAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// A dedicated chat for managing the plug-in interaction.
    /// </summary>
    private sealed class PluginChat : AgentChat
    {
        private readonly Agent _agent;

        public new ChatHistory History => base.History;

        public PluginChat(Agent agent)
        {
            this._agent = agent;
        }

        public override IAsyncEnumerable<ChatMessageContent> InvokeAsync(CancellationToken cancellationToken = default) =>
                base.InvokeAgentAsync(this._agent, cancellationToken);
    }
}
