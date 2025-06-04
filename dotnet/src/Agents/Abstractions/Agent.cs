// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Arguments.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Base abstraction for all Semantic Kernel agents.  An agent instance
/// may participate in one or more conversations, or <see cref="AgentChat"/>.
/// A conversation may include one or more agents.
/// </summary>
/// <remarks>
/// In addition to identity and descriptive meta-data, an <see cref="Agent"/>
/// must define its communication protocol, or <see cref="AgentChannel"/>.
/// </remarks>
public abstract class Agent
{
    /// <summary>
    /// Gets the description of the agent (optional).
    /// </summary>
    public string? Description { get; init; }

    /// <summary>
    /// Gets the identifier of the agent (optional).
    /// </summary>
    /// <value>
    /// The identifier of the agent. The default is a random GUID value, but that can be overridden.
    /// </value>
    public string Id { get; init; } = Guid.NewGuid().ToString();

    /// <summary>
    /// Gets the name of the agent (optional).
    /// </summary>
    public string? Name { get; init; }

    /// <summary>
    /// A <see cref="ILoggerFactory"/> for this <see cref="Agent"/>.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; }

    /// <summary>
    /// Gets the arguments for the agent instruction parameters (optional).
    /// </summary>
    /// <remarks>
    /// Also includes <see cref="PromptExecutionSettings"/>.
    /// </remarks>
    public KernelArguments? Arguments { get; init; }

    /// <summary>
    /// Gets the instructions for the agent (optional).
    /// </summary>
    public string? Instructions { get; init; }

    /// <summary>
    /// Gets the <see cref="Kernel"/> containing services, plugins, and filters for use throughout the agent lifetime.
    /// </summary>
    /// <value>
    /// The <see cref="Kernel"/> containing services, plugins, and filters for use throughout the agent lifetime. The default value is an empty Kernel, but that can be overridden.
    /// </value>
    public Kernel Kernel { get; init; } = new();

    /// <summary>
    /// Gets or sets a prompt template based on the agent instructions.
    /// </summary>
    public IPromptTemplate? Template { get; set; }

    /// <summary>
    /// Invoke the agent with no message assuming that all required instructions are already provided to the agent or on the thread.
    /// </summary>
    /// <param name="thread">The conversation thread to continue with this invocation. If not provided, creates a new thread.</param>
    /// <param name="options">Optional parameters for agent invocation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async list of response items that each contain a <see cref="ChatMessageContent"/> and an <see cref="AgentThread"/>.</returns>
    /// <remarks>
    /// To continue this thread in the future, use an <see cref="AgentThread"/> returned in one of the response items.
    /// </remarks>
    public virtual IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        return this.InvokeAsync((ICollection<ChatMessageContent>)[], thread, options, cancellationToken);
    }

    /// <summary>
    /// Invoke the agent with the provided message and arguments.
    /// </summary>
    /// <param name="message">The message to pass to the agent.</param>
    /// <param name="thread">The conversation thread to continue with this invocation. If not provided, creates a new thread.</param>
    /// <param name="options">Optional parameters for agent invocation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async list of response items that each contain a <see cref="ChatMessageContent"/> and an <see cref="AgentThread"/>.</returns>
    /// <remarks>
    /// <para>
    /// The provided message string will be treated as a user message.
    /// </para>
    /// <para>
    /// To continue this thread in the future, use an <see cref="AgentThread"/> returned in one of the response items.
    /// </para>
    /// </remarks>
    public virtual IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        string message,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(message);

        return this.InvokeAsync(new ChatMessageContent(AuthorRole.User, message), thread, options, cancellationToken);
    }

    /// <summary>
    /// Invoke the agent with the provided message and arguments.
    /// </summary>
    /// <param name="message">The message to pass to the agent.</param>
    /// <param name="thread">The conversation thread to continue with this invocation. If not provided, creates a new thread.</param>
    /// <param name="options">Optional parameters for agent invocation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async list of response items that each contain a <see cref="ChatMessageContent"/> and an <see cref="AgentThread"/>.</returns>
    /// <remarks>
    /// To continue this thread in the future, use an <see cref="AgentThread"/> returned in one of the response items.
    /// </remarks>
    public virtual IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        ChatMessageContent message,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(message);

        return this.InvokeAsync([message], thread, options, cancellationToken);
    }

    /// <summary>
    /// Invoke the agent with the provided message and arguments.
    /// </summary>
    /// <param name="messages">The messages to pass to the agent.</param>
    /// <param name="thread">The conversation thread to continue with this invocation. If not provided, creates a new thread.</param>
    /// <param name="options">Optional parameters for agent invocation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async list of response items that each contain a <see cref="ChatMessageContent"/> and an <see cref="AgentThread"/>.</returns>
    /// <remarks>
    /// To continue this thread in the future, use an <see cref="AgentThread"/> returned in one of the response items.
    /// </remarks>
    public abstract IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Invoke the agent with no message assuming that all required instructions are already provided to the agent or on the thread.
    /// </summary>
    /// <param name="thread">The conversation thread to continue with this invocation. If not provided, creates a new thread.</param>
    /// <param name="options">Optional parameters for agent invocation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async list of response items that each contain a <see cref="ChatMessageContent"/> and an <see cref="AgentThread"/>.</returns>
    /// <remarks>
    /// To continue this thread in the future, use an <see cref="AgentThread"/> returned in one of the response items.
    /// </remarks>
    public virtual IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        return this.InvokeStreamingAsync((ICollection<ChatMessageContent>)[], thread, options, cancellationToken);
    }

    /// <summary>
    /// Invoke the agent with the provided message and arguments.
    /// </summary>
    /// <param name="message">The message to pass to the agent.</param>
    /// <param name="thread">The conversation thread to continue with this invocation. If not provided, creates a new thread.</param>
    /// <param name="options">Optional parameters for agent invocation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async list of response items that each contain a <see cref="ChatMessageContent"/> and an <see cref="AgentThread"/>.</returns>
    /// <remarks>
    /// <para>
    /// The provided message string will be treated as a user message.
    /// </para>
    /// <para>
    /// To continue this thread in the future, use an <see cref="AgentThread"/> returned in one of the response items.
    /// </para>
    /// </remarks>
    public virtual IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        string message,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(message);

        return this.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, message), thread, options, cancellationToken);
    }

    /// <summary>
    /// Invoke the agent with the provided message and arguments.
    /// </summary>
    /// <param name="message">The message to pass to the agent.</param>
    /// <param name="thread">The conversation thread to continue with this invocation. If not provided, creates a new thread.</param>
    /// <param name="options">Optional parameters for agent invocation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async list of response items that each contain a <see cref="StreamingChatMessageContent"/> and an <see cref="AgentThread"/>.</returns>
    /// <remarks>
    /// To continue this thread in the future, use an <see cref="AgentThread"/> returned in one of the response items.
    /// </remarks>
    public virtual IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        ChatMessageContent message,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(message);

        return this.InvokeStreamingAsync([message], thread, options, cancellationToken);
    }

    /// <summary>
    /// Invoke the agent with the provided message and arguments.
    /// </summary>
    /// <param name="messages">The messages to pass to the agent.</param>
    /// <param name="thread">The conversation thread to continue with this invocation. If not provided, creates a new thread.</param>
    /// <param name="options">Optional parameters for agent invocation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async list of response items that each contain a <see cref="StreamingChatMessageContent"/> and an <see cref="AgentThread"/>.</returns>
    /// <remarks>
    /// To continue this thread in the future, use an <see cref="AgentThread"/> returned in one of the response items.
    /// </remarks>
    public abstract IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// The <see cref="ILogger"/> associated with this  <see cref="Agent"/>.
    /// </summary>
    protected ILogger Logger => this._logger ??= this.ActiveLoggerFactory.CreateLogger(this.GetType());

    /// <summary>
    /// Get the active logger factory, if defined; otherwise, provide the default.
    /// </summary>
    protected virtual ILoggerFactory ActiveLoggerFactory => this.LoggerFactory ?? NullLoggerFactory.Instance;

    /// <summary>
    /// Formats the system instructions for the agent.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The formatted system instructions for the agent.</returns>
    protected async Task<string?> RenderInstructionsAsync(Kernel kernel, KernelArguments? arguments, CancellationToken cancellationToken)
    {
        if (this.Template is null)
        {
            // Use the instructions as-is
            return this.Instructions;
        }

        var mergedArguments = this.Arguments.Merge(arguments);

        // Use the provided template as the instructions
        return await this.Template.RenderAsync(kernel, mergedArguments, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Set of keys to establish channel affinity.  Minimum expected key-set:
    /// <example>
    /// yield return typeof(YourAgentChannel).FullName;
    /// </example>
    /// </summary>
    /// <remarks>
    /// Two specific agents of the same type may each require their own channel.  This is
    /// why the channel type alone is insufficient.
    /// For example, two OpenAI Assistant agents each targeting a different Azure OpenAI endpoint
    /// would require their own channel. In this case, the endpoint could be expressed as an additional key.
    /// </remarks>
    [Experimental("SKEXP0110")]
#pragma warning disable CA1024 // Use properties where appropriate
    protected internal abstract IEnumerable<string> GetChannelKeys();
#pragma warning restore CA1024 // Use properties where appropriate

    /// <summary>
    /// Produce an <see cref="AgentChannel"/> appropriate for the agent type.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="AgentChannel"/> appropriate for the agent type.</returns>
    /// <remarks>
    /// Every agent conversation, or <see cref="AgentChat"/>, will establish one or more <see cref="AgentChannel"/>
    /// objects according to the specific <see cref="Agent"/> type.
    /// </remarks>
    [Experimental("SKEXP0110")]
    protected internal abstract Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken);

    /// <summary>
    /// Produce an <see cref="AgentChannel"/> appropriate for the agent type based on the provided state.
    /// </summary>
    /// <param name="channelState">The channel state, as serialized</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="AgentChannel"/> appropriate for the agent type.</returns>
    /// <remarks>
    /// Every agent conversation, or <see cref="AgentChat"/>, will establish one or more <see cref="AgentChannel"/>
    /// objects according to the specific <see cref="Agent"/> type.
    /// </remarks>
    [Experimental("SKEXP0110")]
    protected internal abstract Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken);

    private ILogger? _logger;

    /// <summary>
    /// Ensures that the thread exists, is of the expected type, and is active, plus adds the provided message to the thread.
    /// </summary>
    /// <typeparam name="TThreadType">The expected type of the thead.</typeparam>
    /// <param name="messages">The messages to add to the thread once it is setup.</param>
    /// <param name="thread">The thread to create if it's null, validate it's type if not null, and start if it is not active.</param>
    /// <param name="constructThread">A callback to use to construct the thread if it's null.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async task that completes once all update are complete.</returns>
    /// <exception cref="KernelException"></exception>
    protected virtual async Task<TThreadType> EnsureThreadExistsWithMessagesAsync<TThreadType>(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread,
        Func<TThreadType> constructThread,
        CancellationToken cancellationToken)
        where TThreadType : AgentThread
    {
        if (thread is null)
        {
            thread = constructThread();
        }

        if (thread is not TThreadType concreteThreadType)
        {
            throw new KernelException($"{this.GetType().Name} currently only supports agent threads of type {nameof(TThreadType)}.");
        }

        // We have to explicitly call create here to ensure that the thread is created
        // before we invoke using the thread. While threads will be created when
        // notified of new messages, some agents support invoking without a message,
        // and in that case no messages will be sent in the next step.
        await thread.CreateAsync(cancellationToken).ConfigureAwait(false);

        // Notify the thread that new messages are available.
        foreach (var message in messages)
        {
            await this.NotifyThreadOfNewMessage(thread, message, cancellationToken).ConfigureAwait(false);
        }

        return concreteThreadType;
    }

    /// <summary>
    /// Notfiy the given thread that a new message is available.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Note that while all agents should notify their threads of new messages,
    /// not all threads will necessarily take action. For some treads, this may be
    /// the only way that they would know that a new message is available to be added
    /// to their history.
    /// </para>
    /// <para>
    /// For other thread types, where history is managed by the service, the thread may
    /// not need to take any action.
    /// </para>
    /// <para>
    /// Where threads manage other memory components that need access to new messages,
    /// notifying the thread will be important, even if the thread itself does not
    /// require the message.
    /// </para>
    /// </remarks>
    /// <param name="thread">The thread to notify of the new message.</param>
    /// <param name="message">The message to pass to the thread.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async task that completes once the notification is complete.</returns>
    protected Task NotifyThreadOfNewMessage(AgentThread thread, ChatMessageContent message, CancellationToken cancellationToken)
    {
        return thread.OnNewMessageAsync(message, cancellationToken);
    }
}
