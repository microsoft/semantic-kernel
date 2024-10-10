// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text;
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
using System.Text.Json;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using System.Text.Json;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
using System.Text.Json;
>>>>>>> main
>>>>>>> Stashed changes
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on <see cref="IChatCompletionService"/>.
/// </summary>
/// <remarks>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
/// NOTE: Enable OpenAIPromptExecutionSettings.FunctionChoiceBehavior for agent plugins.
/// (<see cref="ChatHistoryKernelAgent.Arguments"/>)
/// </remarks>
public sealed class ChatCompletionAgent : ChatHistoryKernelAgent
{
    /// <inheritdoc/>
    public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        ChatHistory history,
<<<<<<< main
        KernelArguments? arguments = null,
        Kernel? kernel = null,
=======
        IReadOnlyList<ChatMessageContent> history,
>>>>>>> origin/PR
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;
        arguments ??= this.Arguments;

        (IChatCompletionService chatCompletionService, PromptExecutionSettings? executionSettings) = GetChatCompletionService(kernel, arguments);

        ChatHistory chat = this.SetupAgentChatHistory(history);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
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
        IReadOnlyList<ChatMessageContent> history,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;
        arguments = this.MergeArguments(arguments);

        (IChatCompletionService chatCompletionService, PromptExecutionSettings? executionSettings) = GetChatCompletionService(kernel, arguments);

        ChatHistory chat = await this.SetupAgentChatHistoryAsync(history, arguments, kernel, cancellationToken).ConfigureAwait(false);
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

        int messageCount = chat.Count;

        this.Logger.LogAgentChatServiceInvokingAgent(nameof(InvokeAsync), this.Id, chatCompletionService.GetType());
        this.Logger.LogDebug("[{MethodName}] Invoking {ServiceType}.", nameof(InvokeAsync), chatCompletionService.GetType());

        IReadOnlyList<ChatMessageContent> messages =
            await chatCompletionService.GetChatMessageContentsAsync(
                chat,
                executionSettings,
                kernel,
                cancellationToken).ConfigureAwait(false);

        this.Logger.LogAgentChatServiceInvokedAgent(nameof(InvokeAsync), this.Id, chatCompletionService.GetType(), messages.Count);
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        arguments ??= this.Arguments;

        (IChatCompletionService chatCompletionService, PromptExecutionSettings? executionSettings) = GetChatCompletionService(kernel, arguments);

        ChatHistory chat = this.SetupAgentChatHistory(history);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
        arguments = this.MergeArguments(arguments);

        (IChatCompletionService chatCompletionService, PromptExecutionSettings? executionSettings) = GetChatCompletionService(kernel, arguments);

        ChatHistory chat = await this.SetupAgentChatHistoryAsync(history, arguments, kernel, cancellationToken).ConfigureAwait(false);
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

        int messageCount = chat.Count;

        this.Logger.LogAgentChatServiceInvokingAgent(nameof(InvokeAsync), this.Id, chatCompletionService.GetType());

        IAsyncEnumerable<StreamingChatMessageContent> messages =
            chatCompletionService.GetStreamingChatMessageContentsAsync(
                chat,
                executionSettings,
                kernel,
                cancellationToken);

        this.Logger.LogAgentChatServiceInvokedStreamingAgent(nameof(InvokeAsync), this.Id, chatCompletionService.GetType());

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

    internal static (IChatCompletionService service, PromptExecutionSettings? executionSettings) GetChatCompletionService(Kernel kernel, KernelArguments? arguments)
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// <inheritdoc/>
    protected override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        ChatHistoryChannel channel =
            new()
            {
                Logger = this.LoggerFactory.CreateLogger<ChatHistoryChannel>()
            };

        return Task.FromResult<AgentChannel>(channel);
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        ChatHistory history =
            JsonSerializer.Deserialize<ChatHistory>(channelState) ??
            throw new KernelException("Unable to restore channel: invalid state.");
        return Task.FromResult<AgentChannel>(new ChatHistoryChannel(history));
    }

    private (IChatCompletionService service, PromptExecutionSettings? executionSettings) GetChatCompletionService(Kernel kernel, KernelArguments? arguments)
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    private ChatHistory SetupAgentChatHistory(IReadOnlyList<ChatMessageContent> history)
    {
        ChatHistory chat = [];

        if (!string.IsNullOrWhiteSpace(this.Instructions))
        {
            chat.Add(new ChatMessageContent(AuthorRole.System, this.Instructions) { AuthorName = this.Name });
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        }

        chat.AddRange(history);

        return chat;
    }
}
