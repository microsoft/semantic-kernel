// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.AzureAI.Internal;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on Azure AI Agent.
/// </summary>
public sealed class AzureAIAgent : KernelAgent
{
    /// <summary>
    /// Tool definitions used when associating a file attachment to an input message:
    /// <see cref="FileReferenceContent.Tools"/>.
    /// </summary>
    public static class Tools
    {
        /// <summary>
        /// The code-interpreter tool.
        /// </summary>
        public static readonly string CodeInterpreter = "code_interpreter";

        /// <summary>
        /// The file-search tool.
        /// </summary>
        public const string FileSearch = "file_search";
    }

    /// <summary>
    /// Metadata key that identifies code-interpreter content.
    /// </summary>
    public const string CodeInterpreterMetadataKey = "code";

    private readonly AzureAIClientProvider _provider;
    private readonly AgentsClient _client;
    private readonly string[] _channelKeys;

    /// <summary>
    /// The assistant definition.
    /// </summary>
    public Azure.AI.Projects.Agent Definition { get; private init; }

    /// <summary>
    /// Defines polling behavior for run processing
    /// </summary>
    public RunPollingOptions PollingOptions { get; } = new();

    /// <summary>
    /// Adds a message to the specified thread.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="message">A non-system message with which to append to the conversation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <remarks>
    /// Only supports messages with role = User or agent:
    /// https://platform.openai.com/docs/api-reference/runs/createRun#runs-createrun-additional_messages
    /// </remarks>
    public Task AddChatMessageAsync(string threadId, ChatMessageContent message, CancellationToken cancellationToken = default)
    {
        return AgentThreadActions.CreateMessageAsync(this._client, threadId, message, cancellationToken);
    }

    /// <summary>
    /// Gets messages for a specified thread.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    public IAsyncEnumerable<ChatMessageContent> GetThreadMessagesAsync(string threadId, CancellationToken cancellationToken = default)
    {
        return AgentThreadActions.GetMessagesAsync(this._client, threadId, cancellationToken);
    }

    /// <summary>
    /// Invoke the assistant on the specified thread.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of response messages.</returns>
    /// <remarks>
    /// The `arguments` parameter is not currently used by the agent, but is provided for future extensibility.
    /// </remarks>
    public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        string threadId,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.InvokeAsync(threadId, options: null, arguments, kernel, cancellationToken);
    }

    /// <summary>
    /// Invoke the assistant on the specified thread.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="options">Optional invocation options</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of response messages.</returns>
    /// <remarks>
    /// The `arguments` parameter is not currently used by the agent, but is provided for future extensibility.
    /// </remarks>
    public async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        string threadId,
        AzureAIInvocationOptions? options,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;
        arguments = this.MergeArguments(arguments);

        await foreach ((bool isVisible, ChatMessageContent message) in AgentThreadActions.InvokeAsync(this, this._client, threadId, options, this.Logger, kernel, arguments, cancellationToken).ConfigureAwait(false))
        {
            if (isVisible)
            {
                yield return message;
            }
        }
    }

    /// <summary>
    /// Invoke the assistant on the specified thread with streaming response.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="messages">Optional receiver of the completed messages generated</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// The `arguments` parameter is not currently used by the agent, but is provided for future extensibility.
    /// </remarks>
    public IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        string threadId,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        ChatHistory? messages = null,
        CancellationToken cancellationToken = default)
    {
        return this.InvokeStreamingAsync(threadId, options: null, arguments, kernel, messages, cancellationToken);
    }

    /// <summary>
    /// Invoke the assistant on the specified thread with streaming response.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="options">Optional invocation options</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="messages">Optional receiver of the completed messages generated</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// The `arguments` parameter is not currently used by the agent, but is provided for future extensibility.
    /// </remarks>
    public IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        string threadId,
        AzureAIInvocationOptions? options,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        ChatHistory? messages = null,
        CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;
        arguments = this.MergeArguments(arguments);

        return AgentThreadActions.InvokeStreamingAsync(this, this._client, threadId, messages, options, this.Logger, kernel, arguments, cancellationToken);
    }

    /// <inheritdoc/>
    protected override IEnumerable<string> GetChannelKeys()
    {
        // Distinguish from other channel types.
        yield return typeof(AzureAIChannel).FullName!;

        foreach (string key in this._channelKeys)
        {
            yield return key;
        }
    }

    /// <inheritdoc/>
    protected override async Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        this.Logger.LogAzureAIAgentCreatingChannel(nameof(CreateChannelAsync), nameof(AzureAIChannel));

        string threadId = await AgentThreadActions.CreateThreadAsync(this._client, cancellationToken).ConfigureAwait(false);

        this.Logger.LogInformation("[{MethodName}] Created assistant thread: {ThreadId}", nameof(CreateChannelAsync), threadId);

        AzureAIChannel channel =
            new(this._client, threadId)
            {
                Logger = this.LoggerFactory.CreateLogger<AzureAIChannel>()
            };

        this.Logger.LogAzureAIAgentCreatedChannel(nameof(CreateChannelAsync), nameof(AzureAIChannel), threadId);

        return channel;
    }

    internal Task<string?> GetInstructionsAsync(Kernel kernel, KernelArguments? arguments, CancellationToken cancellationToken)
    {
        return this.FormatInstructionsAsync(kernel, arguments, cancellationToken);
    }

    /// <inheritdoc/>
    protected override async Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        string threadId = channelState;

        this.Logger.LogAzureAIAgentRestoringChannel(nameof(RestoreChannelAsync), nameof(AzureAIChannel), threadId);

        AgentThread thread = await this._client.GetThreadAsync(threadId, cancellationToken).ConfigureAwait(false);

        this.Logger.LogAzureAIAgentRestoredChannel(nameof(RestoreChannelAsync), nameof(AzureAIChannel), threadId);

        return new AzureAIChannel(this._client, thread.Id);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIAgent"/> class.
    /// </summary>
    /// <param name="model">The agent model definition.</param>
    /// <param name="clientProvider">A <see cref="AzureAIClientProvider"/> instance.</param>
    /// <param name="templateFactory">An optional template factory</param>
    public AzureAIAgent(
        Azure.AI.Projects.Agent model,
        AzureAIClientProvider clientProvider,
        IPromptTemplateFactory? templateFactory = null)
    {
        this._provider = clientProvider;
        this._client = clientProvider.Client.GetAgentsClient();
        this._channelKeys = [.. clientProvider.ConfigurationKeys];

        this.Definition = model;
        this.Description = this.Definition.Description;
        this.Id = this.Definition.Id;
        this.Name = this.Definition.Name;
        this.Instructions = this.Definition.Instructions;
        this.Kernel = new();

        if (templateFactory != null)
        {
            PromptTemplateConfig templateConfig = new(this.Instructions);
            this.Template = templateFactory.Create(templateConfig);
        }
    }
}
