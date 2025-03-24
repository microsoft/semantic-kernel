// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Represents a <see cref="KernelAgent"/> specialization based on <see cref="IChatCompletionService"/>.
/// </summary>
/// <remarks>
/// NOTE: Enable <see cref="PromptExecutionSettings.FunctionChoiceBehavior"/> for agent plugins
/// (<see cref="KernelAgent.Arguments"/>).
/// </remarks>
public sealed class ChatCompletionAgent : ChatHistoryKernelAgent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ChatCompletionAgent"/> class.
    /// </summary>
    public ChatCompletionAgent() { }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatCompletionAgent"/> class from
    /// a <see cref="PromptTemplateConfig"/>.
    /// </summary>
    /// <param name="templateConfig">The prompt template configuration.</param>
    /// <param name="templateFactory">The prompt template factory used to produce the <see cref="IPromptTemplate"/> for the agent.</param>
    public ChatCompletionAgent(
        PromptTemplateConfig templateConfig,
        IPromptTemplateFactory templateFactory)
    {
        this.Name = templateConfig.Name;
        this.Description = templateConfig.Description;
        this.Instructions = templateConfig.Template;
        this.Arguments = new(templateConfig.ExecutionSettings.Values);
        this.Template = templateFactory.Create(templateConfig);
    }

    /// <summary>
    /// Gets the role used for agent instructions.  Defaults to "system".
    /// </summary>
    /// <remarks>
    /// Certain versions of "O*" series (deep reasoning) models require the instructions
    /// to be provided as "developer" role.  Other versions support neither role and
    /// an agent targeting such a model cannot provide instructions.  Agent functionality
    /// will be dictated entirely by the provided plugins.
    /// </remarks>
    public AuthorRole InstructionsRole { get; init; } = AuthorRole.System;

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        var chatHistoryAgentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new ChatHistoryAgentThread(),
            cancellationToken).ConfigureAwait(false);

        // Invoke Chat Completion with the updated chat history.
        var chatHistory = new ChatHistory();
        await foreach (var existingMessage in chatHistoryAgentThread.GetMessagesAsync(cancellationToken).ConfigureAwait(false))
        {
            chatHistory.Add(existingMessage);
        }
        string agentName = this.GetDisplayName();
        var invokeResults = this.InternalInvokeAsync(
            agentName,
            chatHistory,
            this.MergeArguments(options?.KernelArguments),
            options?.Kernel ?? this.Kernel,
            options?.AdditionalInstructions,
            cancellationToken);

        // Notify the thread of new messages and return them to the caller.
        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            await this.NotifyThreadOfNewMessage(chatHistoryAgentThread, result, cancellationToken).ConfigureAwait(false);
            yield return new(result, chatHistoryAgentThread);
        }
    }

    /// <inheritdoc/>
    [Obsolete("Use InvokeAsync with AgentThread instead.")]
    public override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        string agentName = this.GetDisplayName();

        return ActivityExtensions.RunWithActivityAsync(
            () => ModelDiagnostics.StartAgentInvocationActivity(this.Id, agentName, this.Description),
            () => this.InternalInvokeAsync(agentName, history, arguments, kernel, null, cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        var chatHistoryAgentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new ChatHistoryAgentThread(),
            cancellationToken).ConfigureAwait(false);

        // Invoke Chat Completion with the updated chat history.
        var chatHistory = new ChatHistory();
        await foreach (var existingMessage in chatHistoryAgentThread.GetMessagesAsync(cancellationToken).ConfigureAwait(false))
        {
            chatHistory.Add(existingMessage);
        }
        string agentName = this.GetDisplayName();
        var invokeResults = this.InternalInvokeStreamingAsync(
            agentName,
            chatHistory,
            (newMessage) => this.NotifyThreadOfNewMessage(chatHistoryAgentThread, newMessage, cancellationToken),
            this.MergeArguments(options?.KernelArguments),
            options?.Kernel ?? this.Kernel,
            options?.AdditionalInstructions,
            cancellationToken);

        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            yield return new(result, chatHistoryAgentThread);
        }
    }

    /// <inheritdoc/>
    [Obsolete("Use InvokeStreamingAsync with AgentThread instead.")]
    public override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        string agentName = this.GetDisplayName();

        return ActivityExtensions.RunWithActivityAsync(
            () => ModelDiagnostics.StartAgentInvocationActivity(this.Id, agentName, this.Description),
            () => this.InternalInvokeStreamingAsync(
                agentName,
                history,
                (newMessage) =>
                {
                    history.Add(newMessage);
                    return Task.CompletedTask;
                },
                arguments,
                kernel,
                null,
                cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        ChatHistory history =
            JsonSerializer.Deserialize<ChatHistory>(channelState) ??
            throw new KernelException("Unable to restore channel: invalid state.");
        return Task.FromResult<AgentChannel>(new ChatHistoryChannel(history));
    }

    internal static (IChatCompletionService service, PromptExecutionSettings? executionSettings) GetChatCompletionService(Kernel kernel, KernelArguments? arguments)
    {
        (IChatCompletionService chatCompletionService, PromptExecutionSettings? executionSettings) =
            kernel.ServiceSelector.SelectAIService<IChatCompletionService>(
                kernel,
                arguments?.ExecutionSettings,
                arguments ?? []);

        return (chatCompletionService, executionSettings);
    }

    #region private

    private async Task<ChatHistory> SetupAgentChatHistoryAsync(
        IReadOnlyList<ChatMessageContent> history,
        KernelArguments? arguments,
        Kernel kernel,
        string? additionalInstructions,
        CancellationToken cancellationToken)
    {
        ChatHistory chat = [];

        string? instructions = await this.FormatInstructionsAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        if (!string.IsNullOrWhiteSpace(instructions))
        {
            chat.Add(new ChatMessageContent(this.InstructionsRole, instructions) { AuthorName = this.Name });
        }

        if (!string.IsNullOrWhiteSpace(additionalInstructions))
        {
            chat.Add(new ChatMessageContent(AuthorRole.System, additionalInstructions) { AuthorName = this.Name });
        }

        chat.AddRange(history);

        return chat;
    }

    private async IAsyncEnumerable<ChatMessageContent> InternalInvokeAsync(
        string agentName,
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        string? additionalInstructions = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;
        arguments = this.MergeArguments(arguments);

        (IChatCompletionService chatCompletionService, PromptExecutionSettings? executionSettings) = GetChatCompletionService(kernel, arguments);

        ChatHistory chat = await this.SetupAgentChatHistoryAsync(history, arguments, kernel, additionalInstructions, cancellationToken).ConfigureAwait(false);

        int messageCount = chat.Count;

        Type serviceType = chatCompletionService.GetType();

        this.Logger.LogAgentChatServiceInvokingAgent(nameof(InvokeAsync), this.Id, agentName, serviceType);

        IReadOnlyList<ChatMessageContent> messages =
            await chatCompletionService.GetChatMessageContentsAsync(
                chat,
                executionSettings,
                kernel,
                cancellationToken).ConfigureAwait(false);

        this.Logger.LogAgentChatServiceInvokedAgent(nameof(InvokeAsync), this.Id, agentName, serviceType, messages.Count);

        // Capture mutated messages related function calling / tools
        for (int messageIndex = messageCount; messageIndex < chat.Count; messageIndex++)
        {
            ChatMessageContent message = chat[messageIndex];

            message.AuthorName = this.Name;

            history.Add(message);
        }

        foreach (ChatMessageContent message in messages)
        {
            message.AuthorName = this.Name;

            yield return message;
        }
    }

    private async IAsyncEnumerable<StreamingChatMessageContent> InternalInvokeStreamingAsync(
        string agentName,
        ChatHistory history,
        Func<ChatMessageContent, Task> onNewMessage,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        string? additionalInstructions = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;
        arguments = this.MergeArguments(arguments);

        (IChatCompletionService chatCompletionService, PromptExecutionSettings? executionSettings) = GetChatCompletionService(kernel, arguments);

        ChatHistory chat = await this.SetupAgentChatHistoryAsync(history, arguments, kernel, additionalInstructions, cancellationToken).ConfigureAwait(false);

        int messageCount = chat.Count;

        Type serviceType = chatCompletionService.GetType();

        this.Logger.LogAgentChatServiceInvokingAgent(nameof(InvokeAsync), this.Id, agentName, serviceType);

        IAsyncEnumerable<StreamingChatMessageContent> messages =
            chatCompletionService.GetStreamingChatMessageContentsAsync(
                chat,
                executionSettings,
                kernel,
                cancellationToken);

        this.Logger.LogAgentChatServiceInvokedStreamingAgent(nameof(InvokeAsync), this.Id, agentName, serviceType);

        AuthorRole? role = null;
        StringBuilder builder = new();
        await foreach (StreamingChatMessageContent message in messages.ConfigureAwait(false))
        {
            role = message.Role;
            message.Role ??= AuthorRole.Assistant;
            message.AuthorName = this.Name;

            builder.Append(message.ToString());

            yield return message;
        }

        // Capture mutated messages related function calling / tools
        for (int messageIndex = messageCount; messageIndex < chat.Count; messageIndex++)
        {
            ChatMessageContent message = chat[messageIndex];

            message.AuthorName = this.Name;

            await onNewMessage(message).ConfigureAwait(false);
            history.Add(message);
        }

        // Do not duplicate terminated function result to history
        if (role != AuthorRole.Tool)
        {
            await onNewMessage(new(role ?? AuthorRole.Assistant, builder.ToString()) { AuthorName = this.Name }).ConfigureAwait(false);
            history.Add(new(role ?? AuthorRole.Assistant, builder.ToString()) { AuthorName = this.Name });
        }
    }

    #endregion
}
