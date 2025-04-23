// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A component that listens to messages added to the conversation thread, and automatically captures
/// information about the user. It is also able to retrieve this information and add it to the AI invocation context.
/// </summary>
[Experimental("SKEXP0130")]
public class Mem0MemoryComponent : ConversationStatePart
{
    private readonly string? _applicationId;
    private readonly string? _agentId;
    private string? _threadId;
    private readonly string? _userId;
    private readonly bool _scopeToThread;

    private readonly AIFunction[] _aIFunctions;

    private readonly Mem0Client _mem0Client;

    /// <summary>
    /// Initializes a new instance of the <see cref="Mem0MemoryComponent"/> class.
    /// </summary>
    /// <param name="httpClient">The HTTP client used for making requests.</param>
    /// <param name="options">Options for configuring the component.</param>
    /// <remarks>
    /// The base address of the required mem0 service and any authentication headers should be set on the <paramref name="httpClient"/>
    /// already when provided here. E.g.:
    /// <code>
    /// using var httpClient = new HttpClient();
    /// httpClient.BaseAddress = new Uri("https://api.mem0.ai");
    /// httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Token", "&lt;Your APIKey&gt;");
    /// new Mem0Client(httpClient);
    /// </code>
    /// </remarks>
    public Mem0MemoryComponent(HttpClient httpClient, Mem0MemoryComponentOptions? options = default)
    {
        Verify.NotNull(httpClient);

        this._applicationId = options?.ApplicationId;
        this._agentId = options?.AgentId;
        this._threadId = options?.ThreadId;
        this._userId = options?.UserId;
        this._scopeToThread = options?.ScopeToThread ?? false;

        this._aIFunctions = [AIFunctionFactory.Create(this.ClearStoredUserFactsAsync)];

        this._mem0Client = new(httpClient);
    }

    /// <inheritdoc/>
    public override IReadOnlyCollection<AIFunction> AIFunctions => this._aIFunctions;

    /// <inheritdoc/>
    public override Task OnThreadCreatedAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        this._threadId ??= threadId;
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public override async Task OnNewMessageAsync(string? threadId, ChatMessage newMessage, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(newMessage);

        if (newMessage.Role == ChatRole.User && !string.IsNullOrWhiteSpace(newMessage.Text))
        {
            await this._mem0Client.CreateMemoryAsync(
                this._applicationId,
                this._agentId,
                this._scopeToThread ? this._threadId : null,
                this._userId,
                newMessage.Text,
                newMessage.Role.Value).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public override async Task<string> OnModelInvokeAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(newMessages);

        string inputText = string.Join(
            "\n",
            newMessages.
                Where(m => m is not null && !string.IsNullOrWhiteSpace(m.Text)).
                Select(m => m.Text));

        var memories = await this._mem0Client.SearchAsync(
                this._applicationId,
                this._agentId,
                this._scopeToThread ? this._threadId : null,
                this._userId,
                inputText).ConfigureAwait(false);

        var userInformation = string.Join("\n", memories);
        return "The following list contains facts about the user:\n" + userInformation;
    }

    /// <summary>
    /// Plugin method to clear user preferences stored in memory for the current agent/thread/user.
    /// </summary>
    /// <returns>A task that completes when the memory is cleared.</returns>
    [Description("Deletes any user facts that are stored across multiple conversations.")]
    public async Task ClearStoredUserFactsAsync()
    {
        await this._mem0Client.ClearMemoryAsync(
            this._applicationId,
            this._userId,
            this._agentId,
            this._scopeToThread ? this._threadId : null).ConfigureAwait(false);
    }
}
