// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on <see cref="IChatCompletionService"/>.
/// </summary>
public sealed class ChatCompletionAgent : ChatHistoryKernelAgent
{
    /// <summary>
    /// Optional arguments for the agent.
    /// </summary>
    public KernelArguments? Arguments { get; set; }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;
        arguments ??= this.Arguments;

        KernelFunction nullPrompt = KernelFunctionFactory.CreateFromPrompt("do nothing", arguments?.ExecutionSettings?.Values); // %%%
        if (!kernel.ServiceSelector.TrySelectAIService<IChatCompletionService>(
                kernel,
                nullPrompt,
                arguments ?? [],
                out IChatCompletionService? chatCompletionService,
                out PromptExecutionSettings? executionSettings))
        {
            throw new KernelException("No chat completion service found."); // %%%
        }

        ChatHistory chat = this.SetupAgentChatHistory(history, cancellationToken);

        int messageCount = chat.Count;

        this.Logger.LogAgentChatServiceInvokingAgent(nameof(InvokeAsync), this.Id, chatCompletionService.GetType());

        IReadOnlyList<ChatMessageContent> messages =
            await chatCompletionService.GetChatMessageContentsAsync(
                chat,
                executionSettings,
                kernel,
                cancellationToken).ConfigureAwait(false);

        this.Logger.LogAgentChatServiceInvokedAgent(nameof(InvokeAsync), this.Id, chatCompletionService.GetType(), messages.Count);

        // Capture mutated messages related function calling / tools
        for (int messageIndex = messageCount; messageIndex < chat.Count; messageIndex++)
        {
            ChatMessageContent message = chat[messageIndex];

            message.AuthorName = this.Name;

            history.Add(message);
        }

        foreach (ChatMessageContent message in messages ?? [])
        {
            message.AuthorName = this.Name;

            yield return message;
        }
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;
        arguments ??= this.Arguments;

        KernelFunction nullPrompt = KernelFunctionFactory.CreateFromPrompt("do nothing", arguments?.ExecutionSettings?.Values); // %%%
        if (!kernel.ServiceSelector.TrySelectAIService<IChatCompletionService>(
                kernel,
                nullPrompt,
                arguments ?? [],
                out IChatCompletionService? chatCompletionService,
                out PromptExecutionSettings? executionSettings))
        {
            throw new KernelException("No chat completion service found."); // %%%
        }

        ChatHistory chat = this.SetupAgentChatHistory(history, cancellationToken);

        int messageCount = chat.Count;

        this.Logger.LogAgentChatServiceInvokingAgent(nameof(InvokeAsync), this.Id, chatCompletionService.GetType());

        IAsyncEnumerable<StreamingChatMessageContent> messages =
            chatCompletionService.GetStreamingChatMessageContentsAsync(
                chat,
                executionSettings,
                kernel,
                cancellationToken);

        this.Logger.LogAgentChatServiceInvokedStreamingAgent(nameof(InvokeAsync), this.Id, chatCompletionService.GetType());

        await foreach (StreamingChatMessageContent message in messages.ConfigureAwait(false))
        {
            message.AuthorName = this.Name;

            yield return message;
        }

        // Capture mutated messages related function calling / tools
        for (int messageIndex = messageCount; messageIndex < chat.Count; messageIndex++)
        {
            ChatMessageContent message = chat[messageIndex];

            message.AuthorName = this.Name;

            history.Add(message);
        }
    }

    private ChatHistory SetupAgentChatHistory(
        IReadOnlyList<ChatMessageContent> history,
        CancellationToken cancellationToken)
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
