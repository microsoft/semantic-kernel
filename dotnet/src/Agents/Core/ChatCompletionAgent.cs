// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on <see cref="IChatCompletionService"/>.
/// </summary>
/// <remarks>
/// NOTE: Enable OpenAIPromptExecutionSettings.ToolCallBehavior for agent plugins.
/// (<see cref="ChatCompletionAgent.ExecutionSettings"/>)
/// </remarks>
public sealed class ChatCompletionAgent : ChatHistoryKernelAgent
{
    /// <summary>
    /// Optional execution settings for the agent.
    /// </summary>
    public PromptExecutionSettings? ExecutionSettings { get; set; }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        ChatHistory history,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        IChatCompletionService chatCompletionService = this.Kernel.GetRequiredService<IChatCompletionService>();

        ChatHistory chat = this.SetupAgentChatHistory(history);

        int messageCount = chat.Count;

        this.Logger.LogDebug("[{MethodName}] Invoking {ServiceType}.", nameof(InvokeAsync), chatCompletionService.GetType());

        IReadOnlyList<ChatMessageContent> messages =
            await chatCompletionService.GetChatMessageContentsAsync(
                chat,
                this.ExecutionSettings,
                this.Kernel,
                cancellationToken).ConfigureAwait(false);

        if (this.Logger.IsEnabled(LogLevel.Information)) // Avoid boxing if not enabled
        {
            this.Logger.LogInformation("[{MethodName}] Invoked {ServiceType} with message count: {MessageCount}.", nameof(InvokeAsync), chatCompletionService.GetType(), messages.Count);
        }

        // Capture mutated messages related function calling / tools
        for (int messageIndex = messageCount; messageIndex < chat.Count; messageIndex++)
        {
            ChatMessageContent message = chat[messageIndex];

            message.AuthorName = this.Name;

            history.Add(message);
        }

        foreach (ChatMessageContent message in messages ?? [])
        {
            // TODO: MESSAGE SOURCE - ISSUE #5731
            message.AuthorName = this.Name;

            yield return message;
        }
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        ChatHistory history,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        IChatCompletionService chatCompletionService = this.Kernel.GetRequiredService<IChatCompletionService>();

        ChatHistory chat = this.SetupAgentChatHistory(history);

        int messageCount = chat.Count;

        this.Logger.LogDebug("[{MethodName}] Invoking {ServiceType}.", nameof(InvokeAsync), chatCompletionService.GetType());

        IAsyncEnumerable<StreamingChatMessageContent> messages =
            chatCompletionService.GetStreamingChatMessageContentsAsync(
                chat,
                this.ExecutionSettings,
                this.Kernel,
                cancellationToken);

        if (this.Logger.IsEnabled(LogLevel.Information))
        {
            this.Logger.LogInformation("[{MethodName}] Invoked {ServiceType} with streaming messages.", nameof(InvokeAsync), chatCompletionService.GetType());
        }

        // Capture mutated messages related function calling / tools
        for (int messageIndex = messageCount; messageIndex < chat.Count; messageIndex++)
        {
            ChatMessageContent message = chat[messageIndex];

            message.AuthorName = this.Name;

            history.Add(message);
        }

        await foreach (StreamingChatMessageContent message in messages.ConfigureAwait(false))
        {
            // TODO: MESSAGE SOURCE - ISSUE #5731
            message.AuthorName = this.Name;

            yield return message;
        }
    }

    private ChatHistory SetupAgentChatHistory(IReadOnlyList<ChatMessageContent> history)
    {
        ChatHistory chat = [];

        if (!string.IsNullOrWhiteSpace(this.Instructions))
        {
            chat.Add(new ChatMessageContent(AuthorRole.System, this.Instructions) { AuthorName = this.Name });
        }

        chat.AddRange(history);

        return chat;
    }
}
