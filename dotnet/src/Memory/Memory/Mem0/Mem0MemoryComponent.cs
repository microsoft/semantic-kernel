// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A component that listenes to messages added to the conversation thread, and automatically captures
/// information about the user. It is also able to retrieve this information and add it to the AI invocation context.
/// </summary>
public class Mem0MemoryComponent : ConversationStateExtension
{
    private readonly string? _applicationId;
    private readonly string? _agentId;
    private string? _threadId;
    private readonly string? _userId;
    private readonly bool _scopeToThread;

    private readonly Mem0Client _mem0Client;

    /// <summary>
    /// Initializes a new instance of the <see cref="Mem0MemoryComponent"/> class.
    /// </summary>
    /// <param name="httpClient">The HTTP client used for making requests.</param>
    /// <param name="options">Options for configuring the component.</param>
    public Mem0MemoryComponent(HttpClient httpClient, Mem0MemoryComponentOptions? options = default)
    {
        Verify.NotNull(httpClient);

        this._applicationId = options?.ApplicationId;
        this._agentId = options?.AgentId;
        this._threadId = options?.ThreadId;
        this._userId = options?.UserId;
        this._scopeToThread = options?.ScopeToThread ?? false;

        this._mem0Client = new(httpClient);
    }

    /// <inheritdoc/>
    public override Task OnThreadCreatedAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        this._threadId ??= threadId;
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public override async Task OnNewMessageAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(newMessage);

        if (newMessage.Role == AuthorRole.User && !string.IsNullOrWhiteSpace(newMessage.Content))
        {
            await this._mem0Client.CreateMemoryAsync(
                this._applicationId,
                this._agentId,
                this._scopeToThread ? this._threadId : null,
                this._userId,
                newMessage.Content,
                newMessage.Role.Label).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public override async Task<string> OnAIInvocationAsync(ICollection<ChatMessageContent> newMessages, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(newMessages);

        string inputText = string.Join(
            "\n",
            newMessages.
                Where(m => m is not null && !string.IsNullOrWhiteSpace(m.Content)).
                Select(m => m.Content));

        var memories = await this._mem0Client.SearchAsync(
                this._applicationId,
                this._agentId,
                this._scopeToThread ? this._threadId : null,
                this._userId,
                inputText).ConfigureAwait(false);

        var userInformation = string.Join("\n", memories);
        return "The following list contains facts about the user:\n" + userInformation;
    }

    /// <inheritdoc/>
    public override void RegisterPlugins(Kernel kernel)
    {
        Verify.NotNull(kernel);

        base.RegisterPlugins(kernel);
        kernel.Plugins.AddFromObject(this, "MemZeroMemory");
    }

    /// <summary>
    /// Plugin method to clear user preferences stored in memory for the current agent/thread/user.
    /// </summary>
    /// <returns>A task that completes when the memory is cleared.</returns>
    [KernelFunction]
    [Description("Deletes any user preferences stored about the user.")]
    public async Task ClearUserPreferencesAsync()
    {
        await this._mem0Client.ClearMemoryAsync(
            this._applicationId,
            this._userId,
            this._agentId,
            this._scopeToThread ? this._threadId : null).ConfigureAwait(false);
    }
}
