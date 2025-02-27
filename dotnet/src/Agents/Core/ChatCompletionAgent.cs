// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;

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
    /// <param name="templateFactory">An optional factory to produce the <see cref="IPromptTemplate"/> for the agent.</param>
    /// <remarks>
    /// When a template factory argument isn't provided, the default <see cref="KernelPromptTemplateFactory"/> is used.
    /// </remarks>
    public ChatCompletionAgent(
        PromptTemplateConfig templateConfig,
        IPromptTemplateFactory? templateFactory = null)
    {
        this.Name = templateConfig.Name;
        this.Description = templateConfig.Description;
        this.Instructions = templateConfig.Template;
        this.Arguments = new(templateConfig.ExecutionSettings.Values);
        this.Template = templateFactory?.Create(templateConfig);
    }

    /// <summary>
    /// Gets the role used for the agent instructions.  Defaults to "system".
    /// </summary>
    /// <remarks>
    /// Certain versions of "O*" series (deep reasoning) models require the instructions
    /// to be provided as "developer" role.  Other versions support neither role and
    /// an agent targeting such a model cannot provide instructions.  Agent functionality
    /// will be dictated entirely by the provided plugins.
    /// </remarks>
    public AuthorRole InstructionsRole { get; init; } = AuthorRole.System;

    /// <inheritdoc/>
    public override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var agentName = this.GetDisplayName();

        return ActivityExtensions.RunWithActivityAsync(
            () => ModelDiagnostics.StartAgentInvocationActivity(this.Id, agentName, this.Description),
            () => this.InternalInvokeAsync(agentName, history, arguments, kernel, cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    public override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var agentName = this.GetDisplayName();

        return ActivityExtensions.RunWithActivityAsync(
            () => ModelDiagnostics.StartAgentInvocationActivity(this.Id, agentName, this.Description),
            () => this.InternalInvokeStreamingAsync(agentName, history, arguments, kernel, cancellationToken),
            cancellationToken);
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

        kernel.ServiceSelector.TrySelectAIService<IChatCompletionService>(kernel, nullPrompt, arguments ?? [], out IChatCompletionService? chatCompletionService, out PromptExecutionSettings? executionSettings);

#pragma warning disable CA2000 // Dispose objects before losing scope
        if (chatCompletionService is null
            && kernel.ServiceSelector is IServiceSelector chatClientSelector
            && chatClientSelector.TrySelect<Microsoft.Extensions.AI.IChatClient>(kernel, nullPrompt, arguments ?? [], out var chatClient, out executionSettings)
            && chatClient is not null)
        {
            // This change is temporary until Agents support IChatClient natively in near future.
            chatCompletionService = chatClient!.AsChatCompletionService();
        }
#pragma warning restore CA2000 // Dispose objects before losing scope

        if (chatCompletionService is null)
        {
            var message = new StringBuilder().Append("No service was found for any of the supported types: ").Append(typeof(IChatCompletionService)).Append(", ").Append(typeof(Microsoft.Extensions.AI.IChatClient)).Append('.');
            if (nullPrompt.ExecutionSettings is not null)
            {
                string serviceIds = string.Join("|", nullPrompt.ExecutionSettings.Keys);
                if (!string.IsNullOrEmpty(serviceIds))
                {
                    message.Append(" Expected serviceIds: ").Append(serviceIds).Append('.');
                }

                string modelIds = string.Join("|", nullPrompt.ExecutionSettings.Values.Select(model => model.ModelId));
                if (!string.IsNullOrEmpty(modelIds))
                {
                    message.Append(" Expected modelIds: ").Append(modelIds).Append('.');
                }
            }

            throw new KernelException(message.ToString());
        }

        return (chatCompletionService!, executionSettings);
    }

    #region private

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
            chat.Add(new ChatMessageContent(this.InstructionsRole, instructions) { AuthorName = this.Name });
        }

        chat.AddRange(history);

        return chat;
    }

    private async IAsyncEnumerable<ChatMessageContent> InternalInvokeAsync(
        string agentName,
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

            history.Add(message);
        }

        // Do not duplicate terminated function result to history
        if (role != AuthorRole.Tool)
        {
            history.Add(new(role ?? AuthorRole.Assistant, builder.ToString()) { AuthorName = this.Name });
        }
    }

    #endregion
}
