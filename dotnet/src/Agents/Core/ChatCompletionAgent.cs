// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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
/// A <see cref="KernelAgent"/> specialization based on <see cref="IChatCompletionService"/>.
/// </summary>
/// <remarks>
/// NOTE: Enable <see cref="PromptExecutionSettings.FunctionChoiceBehavior"/> for agent plugins.
/// (<see cref="KernelAgent.Arguments"/>)
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
    /// <param name="templateConfig">Prompt template configuration</param>
    /// <param name="templateFactory">An optional factory to produce the <see cref="IPromptTemplate"/> for the agent</param>
    /// <remarks>
    /// When 'templateFactory' parameter is not provided, the default <see cref="KernelPromptTemplateFactory"/> is used.
    /// </remarks>
    public ChatCompletionAgent(
        PromptTemplateConfig templateConfig,
        IPromptTemplateFactory? templateFactory = null)
    {
        this.Name = templateConfig.Name;
        this.Description = templateConfig.Description;
        this.Instructions = templateConfig.Template;
        this.Template = templateFactory?.Create(templateConfig);
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;
        arguments = this.MergeArguments(arguments);

        (IChatCompletionService chatCompletionService, PromptExecutionSettings? executionSettings) = GetChatCompletionService(kernel, arguments);

        ChatHistory chat = await this.SetupAgentChatHistoryAsync(history, arguments, kernel, cancellationToken).ConfigureAwait(false);

        int messageCount = chat.Count;

        var serviceType = chatCompletionService.GetType();
        var agentDisplayName = this.GetDisplayName();

        using var activity = ModelDiagnostics.StartAgentInvocationActivity(this.Id, agentDisplayName, this.Description);

        IReadOnlyList<ChatMessageContent> messages;

        try
        {
            this.Logger.LogAgentChatServiceInvokingAgent(nameof(InvokeAsync), this.Id, agentDisplayName, serviceType);

            messages =
                await chatCompletionService.GetChatMessageContentsAsync(
                    chat,
                    executionSettings,
                    kernel,
                    cancellationToken).ConfigureAwait(false);

            this.Logger.LogAgentChatServiceInvokedAgent(nameof(InvokeAsync), this.Id, agentDisplayName, serviceType, messages.Count);
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            throw;
        }

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

    /// <inheritdoc/>
    public override async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;
        arguments = this.MergeArguments(arguments);

        (IChatCompletionService chatCompletionService, PromptExecutionSettings? executionSettings) = GetChatCompletionService(kernel, arguments);

        ChatHistory chat = await this.SetupAgentChatHistoryAsync(history, arguments, kernel, cancellationToken).ConfigureAwait(false);

        int messageCount = chat.Count;

        var serviceType = chatCompletionService.GetType();
        var agentDisplayName = this.GetDisplayName();

        using var activity = ModelDiagnostics.StartAgentInvocationActivity(this.Id, agentDisplayName, this.Description);

        IAsyncEnumerable<StreamingChatMessageContent> messages;

        try
        {
            this.Logger.LogAgentChatServiceInvokingAgent(nameof(InvokeAsync), this.Id, agentDisplayName, serviceType);

            messages = chatCompletionService.GetStreamingChatMessageContentsAsync(
                chat,
                executionSettings,
                kernel,
                cancellationToken);
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            throw;
        }

        AuthorRole? role = null;
        StringBuilder builder = new();

        var resultEnumerator = messages.ConfigureAwait(false).GetAsyncEnumerator();

        try
        {
            while (true)
            {
                try
                {
                    if (!await resultEnumerator.MoveNextAsync())
                    {
                        break;
                    }
                }
                catch (Exception ex) when (activity is not null)
                {
                    activity.SetError(ex);
                    throw;
                }

                var message = resultEnumerator.Current;

                role = message.Role;
                message.Role ??= AuthorRole.Assistant;
                message.AuthorName = this.Name;

                builder.Append(message.ToString());

                yield return message;
            }
        }
        finally
        {
            await resultEnumerator.DisposeAsync();
        }

        this.Logger.LogAgentChatServiceInvokedStreamingAgent(nameof(InvokeAsync), this.Id, agentDisplayName, serviceType);

        // Capture mutated messages related function calling / tools
        for (int messageIndex = messageCount; messageIndex < chat.Count; messageIndex++)
        {
            ChatMessageContent message = chat[messageIndex];

            message.AuthorName = this.Name;

            history.Add(message);
        }

        // Do not duplicate terminated function result to history
        if (role != AuthorRole.Tool)
        {
            history.Add(new(role ?? AuthorRole.Assistant, builder.ToString()) { AuthorName = this.Name });
        }
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        ChatHistory history =
            JsonSerializer.Deserialize<ChatHistory>(channelState) ??
            throw new KernelException("Unable to restore channel: invalid state.");
        return Task.FromResult<AgentChannel>(new ChatHistoryChannel(history));
    }

    internal static (IChatCompletionService service, PromptExecutionSettings? executionSettings) GetChatCompletionService(Kernel kernel, KernelArguments? arguments)
    {
        // Need to provide a KernelFunction to the service selector as a container for the execution-settings.
        KernelFunction nullPrompt = KernelFunctionFactory.CreateFromPrompt("placeholder", arguments?.ExecutionSettings?.Values);
        (IChatCompletionService chatCompletionService, PromptExecutionSettings? executionSettings) =
            kernel.ServiceSelector.SelectAIService<IChatCompletionService>(
                kernel,
                nullPrompt,
                arguments ?? []);

        return (chatCompletionService, executionSettings);
    }

    private async Task<ChatHistory> SetupAgentChatHistoryAsync(
        IReadOnlyList<ChatMessageContent> history,
        KernelArguments? arguments,
        Kernel kernel,
        CancellationToken cancellationToken)
    {
        ChatHistory chat = [];

        string? instructions = await this.FormatInstructionsAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        if (!string.IsNullOrWhiteSpace(instructions))
        {
            chat.Add(new ChatMessageContent(AuthorRole.System, instructions) { AuthorName = this.Name });
        }

        chat.AddRange(history);

        return chat;
    }
}
