// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents.Chat;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with <see cref="ChatAgent"/>.
/// </summary>
public sealed class ChatChannel : AgentChannel
{
    private readonly ChatHistory _chat;
    private readonly PromptExecutionSettings? _settings;

    /// <inheritdoc/>
    public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(KernelAgent agent, ChatMessageContent? input, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var chat = new ChatHistory();

        if (!string.IsNullOrWhiteSpace(agent.Instructions))
        {
            chat.AddMessage(AuthorRole.System, agent.Instructions!, name: agent.Name);
        }

        if (input != null)
        {
            yield return input;
        }

        chat.AddRange(this._chat);

        var chatCompletionService = agent.Kernel.GetRequiredService<IChatCompletionService>();

        var messages =
            await chatCompletionService.GetChatMessageContentsAsync(
                chat,
                this._settings,
                agent.Kernel,
                cancellationToken).ConfigureAwait(false);

        foreach (var message in messages)
        {
            message.Source = new AgentMessageSource(agent.Id).ToJson();

            yield return message;
        }
    }

    /// <inheritdoc/>
    public override Task RecieveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return this._chat.Reverse().ToAsyncEnumerable();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatChannel"/> class.
    /// </summary>
    internal ChatChannel(ChatHistory chat, PromptExecutionSettings? settings)
    {
        this._chat = chat;
        this._settings = settings;
    }
}
