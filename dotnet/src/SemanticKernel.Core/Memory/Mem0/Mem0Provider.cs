// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A component that listens to messages added to the conversation thread, and automatically captures
/// information about the user. It is also able to retrieve this information and add it to the AI invocation context.
/// </summary>
/// <remarks>
/// <para>
/// Mem0 allows memories to be stored under one or more optional scopes: application, agent, thread, and user.
/// At least one scope must always be provided.
/// </para>
/// <para>
/// There are some special considerations when using thread as a scope.
/// A thread id may not be available at the time that this component is instantiated.
/// It is therefore possible to provide no thread id when instantiating this class and instead set
/// <see cref="Mem0ProviderOptions.ScopeToPerOperationThreadId"/> to <see langword="true"/>.
/// The component will then capture a thread id when a thread is created or when messages are received
/// and use this thread id to scope the memories in mem0.
/// </para>
/// <para>
/// Note that this component will keep the current thread id in a private field for the duration of
/// the component's lifetime, and therefore using the component with multiple threads, with
/// <see cref="Mem0ProviderOptions.ScopeToPerOperationThreadId"/> set to <see langword="true"/> is not supported.
/// </para>
/// </remarks>
[Experimental("SKEXP0130")]
public sealed class Mem0Provider : AIContextProvider
{
    private const string DefaultContextPrompt = "## Memories\nConsider the following memories when answering user questions:";

    private readonly string? _applicationId;
    private readonly string? _agentId;
    private readonly string? _threadId;
    private string? _perOperationThreadId;
    private readonly string? _userId;
    private readonly bool _scopeToPerOperationThreadId;
    private readonly string _contextPrompt;

    private readonly Mem0Client _mem0Client;
    private readonly ILogger<Mem0Provider>? _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="Mem0Provider"/> class.
    /// </summary>
    /// <param name="httpClient">The HTTP client used for making requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="options">Options for configuring the component.</param>
    /// <remarks>
    /// The base address of the required mem0 service, and any authentication headers, should be set on the <paramref name="httpClient"/>
    /// already, when passed as a parameter here. E.g.:
    /// <code>
    /// using var httpClient = new HttpClient();
    /// httpClient.BaseAddress = new Uri("https://api.mem0.ai");
    /// httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Token", "&lt;Your APIKey&gt;");
    /// new Mem0Client(httpClient);
    /// </code>
    /// </remarks>
    public Mem0Provider(HttpClient httpClient, ILoggerFactory? loggerFactory = default, Mem0ProviderOptions? options = default)
    {
        Verify.NotNull(httpClient);

        if (string.IsNullOrWhiteSpace(httpClient.BaseAddress?.AbsolutePath))
        {
            throw new ArgumentException("The BaseAddress of the provided httpClient parameter must be set.", nameof(httpClient));
        }

        this._applicationId = options?.ApplicationId;
        this._agentId = options?.AgentId;
        this._threadId = options?.ThreadId;
        this._userId = options?.UserId;
        this._scopeToPerOperationThreadId = options?.ScopeToPerOperationThreadId ?? false;
        this._contextPrompt = options?.ContextPrompt ?? DefaultContextPrompt;
        this._logger = loggerFactory?.CreateLogger<Mem0Provider>();

        this._mem0Client = new(httpClient);
    }

    /// <inheritdoc/>
    public override Task ConversationCreatedAsync(string? conversationId, CancellationToken cancellationToken = default)
    {
        this.ValidatePerOperationThreadId(conversationId);

        this._perOperationThreadId ??= conversationId;
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public override async Task MessageAddingAsync(string? conversationId, ChatMessage newMessage, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(newMessage);
        this.ValidatePerOperationThreadId(conversationId);

        switch (newMessage.Role)
        {
            case ChatRole u when u == ChatRole.User:
            case ChatRole a when a == ChatRole.Assistant:
            case ChatRole s when s == ChatRole.System:
                break;
            default:
                return;
        }

        this._perOperationThreadId ??= conversationId;

        if (!string.IsNullOrWhiteSpace(newMessage.Text))
        {
            await this._mem0Client.CreateMemoryAsync(
                this._applicationId,
                this._agentId,
                this._scopeToPerOperationThreadId ? this._perOperationThreadId : this._threadId,
                this._userId,
                newMessage.Text,
                newMessage.Role.Value).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public override async Task<AIContext> ModelInvokingAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(newMessages);

        string inputText = string.Join(
            Environment.NewLine,
            newMessages.
                Where(m => m is not null && !string.IsNullOrWhiteSpace(m.Text)).
                Select(m => m.Text));

        var memories = (await this._mem0Client.SearchAsync(
                this._applicationId,
                this._agentId,
                this._scopeToPerOperationThreadId ? this._perOperationThreadId : this._threadId,
                this._userId,
                inputText).ConfigureAwait(false)).ToList();

        var lineSeparatedMemories = string.Join(Environment.NewLine, memories);

        var context = new AIContext
        {
            Instructions =
                $"""
                {this._contextPrompt}
                {lineSeparatedMemories}
                """
        };

        if (this._logger != null)
        {
            this._logger.LogInformation("Mem0Behavior: Retrieved {Count} memories from mem0.", memories.Count);
            this._logger.LogTrace("Mem0Behavior:\nInput messages:{Input}\nOutput context instructions:\n{Instructions}", inputText, context.Instructions);
        }

        return context;
    }

    /// <summary>
    /// Plugin method to clear memories for the current agent/thread/user.
    /// </summary>
    /// <returns>A task that completes when the memory is cleared.</returns>
    public Task ClearStoredMemoriesAsync()
    {
        return this._mem0Client.ClearMemoryAsync(
            this._applicationId,
            this._agentId,
            this._scopeToPerOperationThreadId ? this._perOperationThreadId : this._threadId,
            this._userId);
    }

    /// <summary>
    /// Validate that we are not receiving a new thread id when the component has already received one before.
    /// </summary>
    /// <param name="threadId">The new thread id.</param>
    private void ValidatePerOperationThreadId(string? threadId)
    {
        if (this._scopeToPerOperationThreadId && !string.IsNullOrWhiteSpace(threadId) && this._perOperationThreadId != null && threadId != this._perOperationThreadId)
        {
            throw new InvalidOperationException($"The {nameof(Mem0Provider)} can only be used with one thread at a time when {nameof(Mem0ProviderOptions.ScopeToPerOperationThreadId)} is set to true.");
        }
    }
}
