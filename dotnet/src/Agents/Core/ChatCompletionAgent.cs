// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.Arguments.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Represents a <see cref="Agent"/> specialization based on <see cref="IChatCompletionService"/>.
/// </summary>
/// <remarks>
/// NOTE: Enable <see cref="PromptExecutionSettings.FunctionChoiceBehavior"/> for agent plugins
/// (<see cref="Agent.Arguments"/>).
/// </remarks>
public sealed class ChatCompletionAgent : ChatHistoryAgent
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

        ChatHistoryAgentThread chatHistoryAgentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new ChatHistoryAgentThread(),
            cancellationToken).ConfigureAwait(false);

        Kernel kernel = this.GetKernel(options);
#pragma warning disable SKEXP0110, SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        if (this.UseImmutableKernel)
        {
            kernel = kernel.Clone();
        }

        // Get the context contributions from the AIContextProviders.
        AIContext providersContext = await chatHistoryAgentThread.AIContextProviders.ModelInvokingAsync(messages, cancellationToken).ConfigureAwait(false);

        // Check for compatibility AIContextProviders and the UseImmutableKernel setting.
        if (providersContext.AIFunctions is { Count: > 0 } && !this.UseImmutableKernel)
        {
            throw new InvalidOperationException("AIContextProviders with AIFunctions are not supported when Agent UseImmutableKernel setting is false.");
        }

        kernel.Plugins.AddFromAIContext(providersContext, "Tools");
#pragma warning restore SKEXP0110, SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

        // Invoke Chat Completion with the updated chat history.
        ChatHistory chatHistory = [];
        await foreach (var existingMessage in chatHistoryAgentThread.GetMessagesAsync(cancellationToken).ConfigureAwait(false))
        {
            chatHistory.Add(existingMessage);
        }
        var invokeResults = this.InternalInvokeAsync(
            this.GetDisplayName(),
            chatHistory,
            async (m) =>
            {
                await this.NotifyThreadOfNewMessage(chatHistoryAgentThread, m, cancellationToken).ConfigureAwait(false);
                if (options?.OnIntermediateMessage is not null)
                {
                    await options.OnIntermediateMessage(m).ConfigureAwait(false);
                }
            },
            options?.KernelArguments,
            kernel,
            FormatAdditionalInstructions(providersContext, options),
            cancellationToken);

        // Notify the thread of new messages and return them to the caller.
        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            // 1. During AutoInvoke = true, the function call content is provided via the callback
            // above, since it is not returned as part of the regular response to the user.
            // 2. During AutoInvoke = false, the function call content is returned directly as a
            // regular response here.
            // 3. If the user Terminates the function call, via a filter, the function call content
            // is also returned as part of the regular response here.
            //
            // In the first case, we don't want to add the function call content to the thread here
            // since it should already have been added in the callback above.
            // In the second case, we shouldn't add the function call content to the thread, since
            // we don't know if the user will execute the call. They should add it themselves.
            // In the third case, we don't want to add the function call content to the thread either,
            // since the filter terminated the call, and therefore won't get executed.
            if (!result.Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
            {
                await this.NotifyThreadOfNewMessage(chatHistoryAgentThread, result, cancellationToken).ConfigureAwait(false);

                if (options?.OnIntermediateMessage is not null)
                {
                    await options.OnIntermediateMessage(result).ConfigureAwait(false);
                }
            }

            yield return new(result, chatHistoryAgentThread);
        }
    }

    /// <inheritdoc/>
    /// <remarks>
    /// This method is used by the <see cref="ChatHistoryChannel"/>. Note that if this method is removed, the <see cref="ChatHistoryChannel"/>
    /// would automatically invoke the overload with <see cref="ICollection{ChatMessageContent}"/> since it is interchangeable with <see cref="ChatHistory"/>
    /// but it's behavior is different, so will not work as expected.
    /// </remarks>
    protected internal override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        string agentName = this.GetDisplayName();

        return ActivityExtensions.RunWithActivityAsync(
            () => ModelDiagnostics.StartAgentInvocationActivity(this.Id, agentName, this.Description),
            () => this.InternalInvokeAsync(agentName, history, (m) => Task.CompletedTask, arguments, kernel, null, cancellationToken),
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

        ChatHistoryAgentThread chatHistoryAgentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new ChatHistoryAgentThread(),
            cancellationToken).ConfigureAwait(false);

        Kernel kernel = options?.Kernel ?? this.Kernel;

        // Get the context contributions from the AIContextProviders.
#pragma warning disable SKEXP0110, SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        AIContext providersContext = await chatHistoryAgentThread.AIContextProviders.ModelInvokingAsync(messages, cancellationToken).ConfigureAwait(false);
        kernel.Plugins.AddFromAIContext(providersContext, "Tools");
#pragma warning restore SKEXP0110, SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

        // Invoke Chat Completion with the updated chat history.
        ChatHistory chatHistory = [];
        await foreach (var existingMessage in chatHistoryAgentThread.GetMessagesAsync(cancellationToken).ConfigureAwait(false))
        {
            chatHistory.Add(existingMessage);
        }
        string agentName = this.GetDisplayName();
        var invokeResults = this.InternalInvokeStreamingAsync(
            agentName,
            chatHistory,
            async (m) =>
            {
                await this.NotifyThreadOfNewMessage(chatHistoryAgentThread, m, cancellationToken).ConfigureAwait(false);
                if (options?.OnIntermediateMessage is not null)
                {
                    await options.OnIntermediateMessage(m).ConfigureAwait(false);
                }
            },
            options?.KernelArguments,
            kernel,
            FormatAdditionalInstructions(providersContext, options),
            cancellationToken);

        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            yield return new(result, chatHistoryAgentThread);
        }
    }

    /// <inheritdoc/>
    /// <remarks>
    /// This method is used by the <see cref="ChatHistoryChannel"/>. Note that if this method is removed, the <see cref="ChatHistoryChannel"/>
    /// would automatically invoke the overload with <see cref="ICollection{ChatMessageContent}"/> since it is interchangeable with <see cref="ChatHistory"/>
    /// but it's behavior is different, so will not work as expected.
    /// </remarks>
    protected internal override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
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
                (newMessage) => Task.CompletedTask,
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
        // Need to provide a KernelFunction to the service selector as a container for the execution-settings.
        KernelFunction nullPrompt = KernelFunctionFactory.CreateFromPrompt("placeholder", arguments?.ExecutionSettings?.Values);

        kernel.ServiceSelector.TrySelectAIService<IChatCompletionService>(kernel, nullPrompt, arguments ?? [], out IChatCompletionService? chatCompletionService, out PromptExecutionSettings? executionSettings);

#pragma warning disable CA2000 // Dispose objects before losing scope
        if (chatCompletionService is null
            && kernel.ServiceSelector is IChatClientSelector chatClientSelector
            && chatClientSelector.TrySelectChatClient<Microsoft.Extensions.AI.IChatClient>(kernel, nullPrompt, arguments ?? [], out var chatClient, out executionSettings)
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
        string? additionalInstructions,
        CancellationToken cancellationToken)
    {
        ChatHistory chat = [];

        string? instructions = await this.RenderInstructionsAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

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
        Func<ChatMessageContent, Task> onNewToolMessage,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        string? additionalInstructions = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;

        (IChatCompletionService chatCompletionService, PromptExecutionSettings? executionSettings) = GetChatCompletionService(kernel, this.Arguments.MergeArguments(arguments));

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
            await onNewToolMessage(message).ConfigureAwait(false);
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

        (IChatCompletionService chatCompletionService, PromptExecutionSettings? executionSettings) = GetChatCompletionService(kernel, this.Arguments.MergeArguments(arguments));

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
