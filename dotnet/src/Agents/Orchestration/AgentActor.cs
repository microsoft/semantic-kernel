// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.AgentRuntime.Core;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// An actor that is represents an <see cref="Agents.Agent"/>.
/// </summary>
public abstract class AgentActor : BaseAgent
{
    internal const string DefaultDescription = "A helpful agent"; // %%% TODO - CONSIDER
    /// <summary>
    /// Initializes a new instance of the <see cref="AgentActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="agent">An <see cref="Agents.Agent"/>.</param>
    protected AgentActor(AgentId id, IAgentRuntime runtime, Agent agent)
        : base(id, runtime, agent.Description ?? DefaultDescription, GetLogger(agent))
    {
        this.Agent = agent;
    }

    /// <summary>
    /// The associated agent
    /// </summary>
    protected Agent Agent { get; }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    protected AgentThread? Thread { get; set; }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="input"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    protected ValueTask<ChatMessageContent> InvokeAsync(ChatMessageContent input, CancellationToken cancellationToken)
    {
        input.Role = AuthorRole.User; // %%% HACK
        return this.InvokeAsync([input], cancellationToken);
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="input"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    protected async ValueTask<ChatMessageContent> InvokeAsync(IList<ChatMessageContent> input, CancellationToken cancellationToken)
    {
        AgentResponseItem<ChatMessageContent>[] responses =
            await this.Agent.InvokeAsync(
                input,
                this.Thread,
                options: null,
                cancellationToken).ToArrayAsync(cancellationToken).ConfigureAwait(false);

        AgentResponseItem<ChatMessageContent> response = responses[0];
        this.Thread ??= response.Thread;

        return new ChatMessageContent(response.Message.Role, string.Join("\n\n", responses.Select(response => response.Message))) // %%% HACK
        {
            AuthorName = response.Message.AuthorName,
        };
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="input"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    protected async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(ChatMessageContent input, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var responseStream = this.Agent.InvokeStreamingAsync([input], this.Thread, options: null, cancellationToken);

        await foreach (AgentResponseItem<StreamingChatMessageContent> response in responseStream.ConfigureAwait(false))
        {
            this.Thread ??= response.Thread;
            yield return response.Message;
        }
    }

    private static ILogger GetLogger(Agent agent)
    {
        ILoggerFactory loggerFactory = agent.LoggerFactory ?? NullLoggerFactory.Instance;
        return loggerFactory.CreateLogger<AgentActor>();
    }
}
