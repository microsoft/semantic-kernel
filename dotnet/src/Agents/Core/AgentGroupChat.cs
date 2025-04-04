// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.Agents.Extensions;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Represents an <see cref="AgentChat"/> that supports multi-turn interactions.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class AgentGroupChat : AgentChat
{
    private readonly HashSet<string> _agentIds; // Efficient existence test O(1) vs O(n) for list.
    private readonly List<Agent> _agents; // Maintain order the agents joined the chat

    /// <summary>
    /// Gets or sets a value that indicates if the completion criteria have been met.
    /// </summary>
    /// <value>
    /// <see langword="true"/> if the completion criteria have been met; otherwise <see langword="false"/>.
    /// The default is <see langword="true"/>. Set to <see langword="false"/> to enable more agent interactions.
    /// </value>
    public bool IsComplete { get; set; }

    /// <summary>
    /// Gets or sets the settings for defining chat behavior.
    /// </summary>
    public AgentGroupChatSettings ExecutionSettings { get; set; } = new AgentGroupChatSettings();

    /// <summary>
    /// Gets the agents participating in the chat.
    /// </summary>
    public override IReadOnlyList<Agent> Agents => this._agents.AsReadOnly();

    /// <summary>
    /// Add an <see cref="Agent"/> to the chat.
    /// </summary>
    /// <param name="agent">The <see cref="Agent"/> to add.</param>
    public void AddAgent(Agent agent)
    {
        if (this._agentIds.Add(agent.Id))
        {
            this._agents.Add(agent);
        }
    }

    /// <summary>
    /// Processes a series of interactions between the <see cref="AgentGroupChat.Agents"/> that have joined this <see cref="AgentGroupChat"/>.
    /// </summary>
    /// <remarks>
    /// The interactions will proceed according to the <see cref="SelectionStrategy"/> and the
    /// <see cref="TerminationStrategy"/> defined via <see cref="AgentGroupChat.ExecutionSettings"/>.
    /// In the absence of an <see cref="AgentGroupChatSettings.SelectionStrategy"/>, this method does not invoke any agents.
    /// Any agent can be explicitly selected by calling <see cref="AgentGroupChat.InvokeAsync(Agent, CancellationToken)"/>.
    /// </remarks>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous enumeration of messages.</returns>
    public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.EnsureStrategyLoggerAssignment();
        this.EnsureCompletionStatus();

        this.Logger.LogAgentGroupChatInvokingAgents(nameof(InvokeAsync), this.Agents);

        for (int index = 0; index < this.ExecutionSettings.TerminationStrategy.MaximumIterations; index++)
        {
            // Identify next agent using strategy
            Agent agent = await this.SelectAgentAsync(cancellationToken).ConfigureAwait(false);

            // Invoke agent and process messages along with termination
            await foreach (var message in this.InvokeAsync(agent, cancellationToken).ConfigureAwait(false))
            {
                yield return message;
            }

            if (this.IsComplete)
            {
                break;
            }
        }

        this.Logger.LogAgentGroupChatYield(nameof(InvokeAsync), this.IsComplete);
    }

    /// <summary>
    /// Processes a series of interactions between the <see cref="AgentGroupChat.Agents"/> that have joined this <see cref="AgentGroupChat"/>.
    /// </summary>
    /// <remarks>
    /// The interactions will proceed according to the <see cref="SelectionStrategy"/> and the
    /// <see cref="TerminationStrategy"/> defined via <see cref="AgentGroupChat.ExecutionSettings"/>.
    /// In the absence of an <see cref="AgentGroupChatSettings.SelectionStrategy"/>, this method does not invoke any agents.
    /// Any agent can be explicitly selected by calling <see cref="AgentGroupChat.InvokeAsync(Agent, CancellationToken)"/>.
    /// </remarks>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous enumeration of streaming messages.</returns>
    public override async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.EnsureStrategyLoggerAssignment();
        this.EnsureCompletionStatus();

        this.Logger.LogAgentGroupChatInvokingAgents(nameof(InvokeAsync), this.Agents);

        for (int index = 0; index < this.ExecutionSettings.TerminationStrategy.MaximumIterations; index++)
        {
            // Identify next agent using strategy
            Agent agent = await this.SelectAgentAsync(cancellationToken).ConfigureAwait(false);

            // Invoke agent and process messages along with termination
            await foreach (var message in this.InvokeStreamingAsync(agent, cancellationToken).ConfigureAwait(false))
            {
                yield return message;
            }

            if (this.IsComplete)
            {
                break;
            }
        }

        this.Logger.LogAgentGroupChatYield(nameof(InvokeAsync), this.IsComplete);
    }

    /// <summary>
    /// Processes a single interaction between a given <see cref="Agent"/> and an <see cref="AgentGroupChat"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// The specified agent joins the chat.
    /// </remarks>
    public async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        Agent agent,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.EnsureStrategyLoggerAssignment();

        this.Logger.LogAgentGroupChatInvokingAgent(nameof(InvokeAsync), agent.GetType(), agent.Id, agent.GetDisplayName());

        this.AddAgent(agent);

        await foreach (ChatMessageContent message in base.InvokeAgentAsync(agent, cancellationToken).ConfigureAwait(false))
        {
            yield return message;
        }

        this.IsComplete = await this.ExecutionSettings.TerminationStrategy.ShouldTerminateAsync(agent, this.History, cancellationToken).ConfigureAwait(false);

        this.Logger.LogAgentGroupChatYield(nameof(InvokeAsync), this.IsComplete);
    }

    /// <summary>
    /// Processes a single interaction between a given <see cref="Agent"/> and an <see cref="AgentGroupChat"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// The specified agent joins the chat.
    /// </remarks>
    public async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        Agent agent,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.EnsureStrategyLoggerAssignment();

        this.Logger.LogAgentGroupChatInvokingAgent(nameof(InvokeAsync), agent.GetType(), agent.Id, agent.GetDisplayName());

        this.AddAgent(agent);

        await foreach (StreamingChatMessageContent message in base.InvokeStreamingAgentAsync(agent, cancellationToken).ConfigureAwait(false))
        {
            yield return message;
        }

        this.IsComplete = await this.ExecutionSettings.TerminationStrategy.ShouldTerminateAsync(agent, this.History, cancellationToken).ConfigureAwait(false);

        this.Logger.LogAgentGroupChatYield(nameof(InvokeAsync), this.IsComplete);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> for a given strategy without HTML-encoding the specified parameters.
    /// </summary>
    /// <param name="template">The prompt template string that defines the prompt.</param>
    /// <param name="templateFactory">
    /// An optional <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="template"/>.
    /// The default factory is used when none is provided.
    /// </param>
    /// <param name="safeParameterNames">The parameter names to exclude from being HTML encoded.</param>
    /// <returns>A <see cref="KernelFunction"/> created via <see cref="KernelFunctionFactory"/> using the specified template.</returns>
    /// <remarks>
    /// This method is particularly targeted to easily avoid encoding the history used by <see cref="KernelFunctionSelectionStrategy"/>
    /// or <see cref="KernelFunctionTerminationStrategy"/>.
    /// </remarks>
    public static KernelFunction CreatePromptFunctionForStrategy(string template, IPromptTemplateFactory? templateFactory = null, params string[] safeParameterNames)
    {
        PromptTemplateConfig config =
            new(template)
            {
                InputVariables = safeParameterNames.Select(parameterName => new InputVariable { Name = parameterName, AllowDangerouslySetContent = true }).ToList()
            };

        return KernelFunctionFactory.CreateFromPrompt(config, promptTemplateFactory: templateFactory);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentGroupChat"/> class.
    /// </summary>
    /// <param name="agents">The agents initially participating in the chat.</param>
    public AgentGroupChat(params Agent[] agents)
    {
        this._agents = new(agents);
        this._agentIds = new(this._agents.Select(a => a.Id));
    }

    private void EnsureStrategyLoggerAssignment()
    {
        // Only invoke logger factory when required.
        if (this.ExecutionSettings.SelectionStrategy.Logger == NullLogger.Instance)
        {
            this.ExecutionSettings.SelectionStrategy.Logger = this.LoggerFactory.CreateLogger(this.ExecutionSettings.SelectionStrategy.GetType());
        }

        if (this.ExecutionSettings.TerminationStrategy.Logger == NullLogger.Instance)
        {
            this.ExecutionSettings.TerminationStrategy.Logger = this.LoggerFactory.CreateLogger(this.ExecutionSettings.TerminationStrategy.GetType());
        }
    }

    private void EnsureCompletionStatus()
    {
        if (this.IsComplete)
        {
            // Throw exception if chat is completed and automatic-reset is not enabled.
            if (!this.ExecutionSettings.TerminationStrategy.AutomaticReset)
            {
                throw new KernelException("Agent Failure - Chat has completed.");
            }

            this.IsComplete = false;
        }
    }

    private async Task<Agent> SelectAgentAsync(CancellationToken cancellationToken)
    {
        this.Logger.LogAgentGroupChatSelectingAgent(nameof(InvokeAsync), this.ExecutionSettings.SelectionStrategy.GetType());

        Agent agent;
        try
        {
            agent = await this.ExecutionSettings.SelectionStrategy.NextAsync(this.Agents, this.History, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception exception)
        {
            this.Logger.LogAgentGroupChatNoAgentSelected(nameof(InvokeAsync), exception);
            throw;
        }

        this.Logger.LogAgentGroupChatSelectedAgent(nameof(InvokeAsync), agent.GetType(), agent.Id, agent.GetDisplayName(), this.ExecutionSettings.SelectionStrategy.GetType());

        return agent;
    }
}
