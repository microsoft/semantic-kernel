// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents.Chat;

/// <summary>
/// $$$
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
            chat.AddMessage(AuthorRole.System, agent.Instructions!); // $$$ NAME
        }

        if (input != null)
        {
            this._chat.Add(input); // $$$ VERIFY USER ???
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
            yield return message;
        }
    }

    /// <inheritdoc/>
    public override Task RecieveAsync(IEnumerable<ChatMessageContent> content, CancellationToken cancellationToken)
    {
        return Task.CompletedTask;
    }

    internal ChatChannel(ChatHistory chat, PromptExecutionSettings? settings)
    {
        this._chat = chat;
        this._settings = settings;
    }
}
