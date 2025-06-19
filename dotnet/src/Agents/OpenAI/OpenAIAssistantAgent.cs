// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Represents a <see cref="Agent"/> specialization based on Open AI Assistant / GPT.
/// </summary>
public sealed partial class OpenAIAssistantAgent : Agent
{
    /// <summary>
    /// The metadata key that identifies code-interpreter content.
    /// </summary>
    public const string CodeInterpreterMetadataKey = "code";

    internal const string OptionsMetadataKey = "__run_options";
    internal const string TemplateMetadataKey = "__template_format";

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgent"/> class.
    /// </summary>
    /// <param name="definition">The assistant definition.</param>
    /// <param name="client">The OpenAI provider for accessing the Assistant API service.</param>
    /// <param name="plugins">Optional collection of plugins to add to the kernel.</param>
    /// <param name="templateFactory">An optional factory to produce the <see cref="IPromptTemplate"/> for the agent.</param>
    /// <param name="templateFormat">The format of the prompt template used when "templateFactory" parameter is supplied.</param>
    public OpenAIAssistantAgent(
        Assistant definition,
        AssistantClient client,
        IEnumerable<KernelPlugin>? plugins = null,
        IPromptTemplateFactory? templateFactory = null,
        string? templateFormat = null)
    {
        this.Client = client;

        this.Definition = definition;

        this.Description = this.Definition.Description;
        this.Id = this.Definition.Id;
        this.Name = this.Definition.Name;
        this.Instructions = this.Definition.Instructions;

        if (templateFactory != null)
        {
            Verify.NotNullOrWhiteSpace(templateFormat);

            PromptTemplateConfig templateConfig = new(this.Instructions)
            {
                TemplateFormat = templateFormat
            };

            this.Template = templateFactory.Create(templateConfig);
        }

        if (plugins != null)
        {
            this.Kernel.Plugins.AddRange(plugins);
        }
    }

    /// <summary>
    /// Expose client for additional use.
    /// </summary>
    public AssistantClient Client { get; }

    /// <summary>
    /// Gets the assistant definition.
    /// </summary>
    public Assistant Definition { get; }

    /// <summary>
    /// Gets the polling behavior for run processing.
    /// </summary>
    public RunPollingOptions PollingOptions { get; } = new();

    /// <summary>
    /// Gets or sets the run creation options for the assistant.
    /// </summary>
    public RunCreationOptions? RunOptions { get; init; }

    /// <inheritdoc/>
    public override IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        return this.InvokeAsync(
            messages,
            thread,
            options is null ?
                null :
                options is OpenAIAssistantAgentInvokeOptions openAIAssistantAgentInvokeOptions ? openAIAssistantAgentInvokeOptions : new OpenAIAssistantAgentInvokeOptions(options),
            cancellationToken);
    }

    /// <summary>
    /// Invoke the agent with the provided message and arguments.
    /// </summary>
    /// <param name="messages">The messages to pass to the agent.</param>
    /// <param name="thread">The conversation thread to continue with this invocation. If not provided, creates a new thread.</param>
    /// <param name="options">Optional parameters for agent invocation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async list of response items that each contain a <see cref="ChatMessageContent"/> and an <see cref="AgentThread"/>.</returns>
    /// <remarks>
    /// To continue this thread in the future, use an <see cref="AgentThread"/> returned in one of the response items.
    /// </remarks>
    public async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        OpenAIAssistantAgentInvokeOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        OpenAIAssistantAgentThread openAIAssistantAgentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new OpenAIAssistantAgentThread(this.Client),
            cancellationToken).ConfigureAwait(false);

        // Create options that use the RunCreationOptions from the options param if provided or
        // falls back to creating a new RunCreationOptions if additional instructions is provided
        // separately.
        var internalOptions = options?.RunCreationOptions ?? (string.IsNullOrWhiteSpace(options?.AdditionalInstructions) ? null : new RunCreationOptions()
        {
            AdditionalInstructions = options?.AdditionalInstructions,
        });

        Kernel kernel = (options?.Kernel ?? this.Kernel).Clone();

        // Get the context contributions from the AIContextProviders.
#pragma warning disable SKEXP0110, SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        AIContext providersContext = await openAIAssistantAgentThread.AIContextProviders.ModelInvokingAsync(messages, cancellationToken).ConfigureAwait(false);
        kernel.Plugins.AddFromAIContext(providersContext, "Tools");
#pragma warning restore SKEXP0110, SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

        var invokeResults = ActivityExtensions.RunWithActivityAsync(
            () => ModelDiagnostics.StartAgentInvocationActivity(this.Id, this.GetDisplayName(), this.Description),
            () => InternalInvokeAsync(),
            cancellationToken);

        async IAsyncEnumerable<ChatMessageContent> InternalInvokeAsync()
        {
            await foreach ((bool isVisible, ChatMessageContent message) in AssistantThreadActions.InvokeAsync(
                this,
                this.Client,
                openAIAssistantAgentThread.Id!,
                internalOptions,
                providersContext.Instructions,
                this.Logger,
                kernel,
                options?.KernelArguments,
                cancellationToken).ConfigureAwait(false))
            {
                // The thread and the caller should be notified of all messages regardless of visibility.
                await this.NotifyThreadOfNewMessage(openAIAssistantAgentThread, message, cancellationToken).ConfigureAwait(false);
                if (options?.OnIntermediateMessage is not null)
                {
                    await options.OnIntermediateMessage(message).ConfigureAwait(false);
                }

                if (isVisible)
                {
                    yield return message;
                }
            }
        }

        // Notify the thread of new messages and return them to the caller.
        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            yield return new(result, openAIAssistantAgentThread);
        }
    }

    /// <inheritdoc/>
    public override IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        return this.InvokeStreamingAsync(
            messages,
            thread,
            options is null ?
                null :
                options is OpenAIAssistantAgentInvokeOptions openAIAssistantAgentInvokeOptions ? openAIAssistantAgentInvokeOptions : new OpenAIAssistantAgentInvokeOptions(options),
            cancellationToken);
    }

    /// <summary>
    /// Invoke the agent with the provided message and arguments.
    /// </summary>
    /// <param name="messages">The messages to pass to the agent.</param>
    /// <param name="thread">The conversation thread to continue with this invocation. If not provided, creates a new thread.</param>
    /// <param name="options">Optional parameters for agent invocation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async list of response items that each contain a <see cref="StreamingChatMessageContent"/> and an <see cref="AgentThread"/>.</returns>
    /// <remarks>
    /// To continue this thread in the future, use an <see cref="AgentThread"/> returned in one of the response items.
    /// </remarks>
    public async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        OpenAIAssistantAgentInvokeOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        OpenAIAssistantAgentThread openAIAssistantAgentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new OpenAIAssistantAgentThread(this.Client),
            cancellationToken).ConfigureAwait(false);

        Kernel kernel = (options?.Kernel ?? this.Kernel).Clone();

        // Get the context contributions from the AIContextProviders.
#pragma warning disable SKEXP0110, SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        AIContext providersContext = await openAIAssistantAgentThread.AIContextProviders.ModelInvokingAsync(messages, cancellationToken).ConfigureAwait(false);
        kernel.Plugins.AddFromAIContext(providersContext, "Tools");
#pragma warning restore SKEXP0110, SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

        // Create options that use the RunCreationOptions from the options param if provided or
        // falls back to creating a new RunCreationOptions if additional instructions is provided
        // separately.
        var internalOptions = options?.RunCreationOptions ?? (string.IsNullOrWhiteSpace(options?.AdditionalInstructions) ? null : new RunCreationOptions()
        {
            AdditionalInstructions = options?.AdditionalInstructions,
        });

#pragma warning disable SKEXP0001 // ModelDiagnostics is marked experimental.
        ChatHistory newMessagesReceiver = [];
        var invokeResults = ActivityExtensions.RunWithActivityAsync(
            () => ModelDiagnostics.StartAgentInvocationActivity(this.Id, this.GetDisplayName(), this.Description),
            () => InternalInvokeStreamingAsync(),
            cancellationToken);
#pragma warning restore SKEXP0001 // ModelDiagnostics is marked experimental.

        IAsyncEnumerable<StreamingChatMessageContent> InternalInvokeStreamingAsync()
        {
            return AssistantThreadActions.InvokeStreamingAsync(
                this,
                this.Client,
                openAIAssistantAgentThread.Id!,
                newMessagesReceiver,
                internalOptions,
                providersContext.Instructions,
                this.Logger,
                kernel,
                options?.KernelArguments,
                cancellationToken);
        }

        // Return the chunks to the caller.
        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            yield return new(result, openAIAssistantAgentThread);
        }

        // Notify the thread of any new messages that were assembled from the streaming response.
        foreach (var newMessage in newMessagesReceiver)
        {
            await this.NotifyThreadOfNewMessage(openAIAssistantAgentThread, newMessage, cancellationToken).ConfigureAwait(false);

            if (options?.OnIntermediateMessage is not null)
            {
                await options.OnIntermediateMessage(newMessage).ConfigureAwait(false);
            }
        }
    }

    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    protected override IEnumerable<string> GetChannelKeys()
    {
        // Distinguish from other channel types.
        yield return typeof(OpenAIAssistantChannel).FullName!;
        // Distinguish based on client instance.
        yield return this.Client.GetHashCode().ToString();
    }

    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    protected override async Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        this.Logger.LogOpenAIAssistantAgentCreatingChannel(nameof(CreateChannelAsync), nameof(OpenAIAssistantChannel));

        AssistantThread thread = await this.Client.CreateThreadAsync(options: null, cancellationToken).ConfigureAwait(false);

        this.Logger.LogInformation("[{MethodName}] Created assistant thread: {ThreadId}", nameof(CreateChannelAsync), thread.Id);

        OpenAIAssistantChannel channel =
            new(this.Client, thread.Id)
            {
                Logger = this.ActiveLoggerFactory.CreateLogger<OpenAIAssistantChannel>()
            };

        this.Logger.LogOpenAIAssistantAgentCreatedChannel(nameof(CreateChannelAsync), nameof(OpenAIAssistantChannel), thread.Id);

        return channel;
    }

    internal Task<string?> GetInstructionsAsync(Kernel kernel, KernelArguments? arguments, CancellationToken cancellationToken) =>
        this.RenderInstructionsAsync(kernel, arguments, cancellationToken);

    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    protected override async Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        string threadId = channelState;

        this.Logger.LogOpenAIAssistantAgentRestoringChannel(nameof(RestoreChannelAsync), nameof(OpenAIAssistantChannel), threadId);

        AssistantThread thread = await this.Client.GetThreadAsync(threadId, cancellationToken).ConfigureAwait(false);

        this.Logger.LogOpenAIAssistantAgentRestoredChannel(nameof(RestoreChannelAsync), nameof(OpenAIAssistantChannel), threadId);

        return new OpenAIAssistantChannel(this.Client, thread.Id);
    }
}
