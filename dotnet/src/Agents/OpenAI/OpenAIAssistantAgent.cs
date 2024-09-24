// Copyright (c) Microsoft. All rights reserved.
using System.ClientModel;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;
using OpenAI.Assistants;
using OpenAI.Files;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on Open AI Assistant / GPT.
/// </summary>
public sealed class OpenAIAssistantAgent : KernelAgent
{
    /// <summary>
    /// Metadata key that identifies code-interpreter content.
    /// </summary>
    public const string CodeInterpreterMetadataKey = "code";

    internal const string OptionsMetadataKey = "__run_options";
    internal const string TemplateMetadataKey = "__template_format";

    private readonly OpenAIClientProvider _provider;
    private readonly Assistant _assistant;
    private readonly AssistantClient _client;
    private readonly string[] _channelKeys;

    /// <summary>
    /// The assistant definition.
    /// </summary>
    public OpenAIAssistantDefinition Definition { get; private init; }

    /// <summary>
    /// Set when the assistant has been deleted via <see cref="DeleteAsync(CancellationToken)"/>.
    /// An assistant removed by other means will result in an exception when invoked.
    /// </summary>
    public bool IsDeleted { get; private set; }

    /// <summary>
    /// Defines polling behavior for run processing
    /// </summary>
    public RunPollingOptions PollingOptions { get; } = new();

    /// <summary>
    /// Expose predefined tools for run-processing.
    /// </summary>
    internal IReadOnlyList<ToolDefinition> Tools => this._assistant.Tools;

    /// <summary>
    /// Define a new <see cref="OpenAIAssistantAgent"/>.
    /// </summary>
    /// <param name="clientProvider">OpenAI client provider for accessing the API service.</param>
    /// <param name="capabilities">Defines the assistant's capabilities.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="defaultArguments">Required arguments that provide default template parameters, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="templateConfig">Prompt template configuration</param>
    /// <param name="templateFactory">An optional factory to produce the <see cref="IPromptTemplate"/> for the agent</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public async static Task<OpenAIAssistantAgent> CreateFromTemplateAsync(
        OpenAIClientProvider clientProvider,
        OpenAIAssistantCapabilities capabilities,
        Kernel kernel,
        KernelArguments defaultArguments,
        PromptTemplateConfig templateConfig,
        IPromptTemplateFactory? templateFactory = null,
        CancellationToken cancellationToken = default)
    {
        // Validate input
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(defaultArguments, nameof(defaultArguments));
        Verify.NotNull(clientProvider, nameof(clientProvider));
        Verify.NotNull(capabilities, nameof(capabilities));
        Verify.NotNull(templateConfig, nameof(templateConfig));

        // Ensure template is valid (avoid failure after posting assistant creation)
        IPromptTemplate? template = templateFactory?.Create(templateConfig);

        // Create the client
        AssistantClient client = CreateClient(clientProvider);

        // Create the assistant
        AssistantCreationOptions assistantCreationOptions = templateConfig.CreateAssistantOptions(capabilities);
        Assistant model = await client.CreateAssistantAsync(capabilities.ModelId, assistantCreationOptions, cancellationToken).ConfigureAwait(false);

        // Instantiate the agent
        return
            new OpenAIAssistantAgent(model, clientProvider, client)
            {
                Kernel = kernel,
                Arguments = defaultArguments,
                Template = template,
            };
    }

    /// <summary>
    /// Define a new <see cref="OpenAIAssistantAgent"/>.
    /// </summary>
    /// <param name="clientProvider">OpenAI client provider for accessing the API service.</param>
    /// <param name="definition">The assistant definition.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="defaultArguments">Optional default arguments, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public static async Task<OpenAIAssistantAgent> CreateAsync(
        OpenAIClientProvider clientProvider,
        OpenAIAssistantDefinition definition,
        Kernel kernel,
        KernelArguments? defaultArguments = null,
        CancellationToken cancellationToken = default)
    {
        // Validate input
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(clientProvider, nameof(clientProvider));
        Verify.NotNull(definition, nameof(definition));

        // Create the client
        AssistantClient client = CreateClient(clientProvider);

        // Create the assistant
        AssistantCreationOptions assistantCreationOptions = definition.CreateAssistantOptions();
        Assistant model = await client.CreateAssistantAsync(definition.ModelId, assistantCreationOptions, cancellationToken).ConfigureAwait(false);

        // Instantiate the agent
        return
            new OpenAIAssistantAgent(model, clientProvider, client)
            {
                Kernel = kernel,
                Arguments = defaultArguments
            };
    }

    /// <summary>
    /// Retrieve a list of assistant definitions: <see cref="OpenAIAssistantDefinition"/>.
    /// </summary>
    /// <param name="provider">Configuration for accessing the API service.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An list of <see cref="OpenAIAssistantDefinition"/> objects.</returns>
    public static async IAsyncEnumerable<OpenAIAssistantDefinition> ListDefinitionsAsync(
        OpenAIClientProvider provider,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // Create the client
        AssistantClient client = CreateClient(provider);

        // Query and enumerate assistant definitions
        await foreach (var model in client.GetAssistantsAsync(new AssistantCollectionOptions() { Order = AssistantCollectionOrder.Descending }, cancellationToken).ConfigureAwait(false))
        {
            yield return CreateAssistantDefinition(model);
        }
    }

    /// <summary>
    /// Retrieve a <see cref="OpenAIAssistantAgent"/> by identifier.
    /// </summary>
    /// <param name="clientProvider">Configuration for accessing the API service.</param>
    /// <param name="id">The agent identifier</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="defaultArguments">Optional default arguments, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="templateFactory">An optional factory to produce the <see cref="IPromptTemplate"/> for the agent</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public static async Task<OpenAIAssistantAgent> RetrieveAsync(
        OpenAIClientProvider clientProvider,
        string id,
        Kernel kernel,
        KernelArguments? defaultArguments = null,
        IPromptTemplateFactory? templateFactory = null,
        CancellationToken cancellationToken = default)
    {
        // Validate input
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(clientProvider, nameof(clientProvider));
        Verify.NotNullOrWhiteSpace(id, nameof(id));

        // Create the client
        AssistantClient client = CreateClient(clientProvider);

        // Retrieve the assistant
        Assistant model = await client.GetAssistantAsync(id, cancellationToken).ConfigureAwait(false);

        // Ensure template is valid (avoid failure after posting assistant creation)
        IPromptTemplate? template =
            !string.IsNullOrWhiteSpace(model.Instructions) ? templateFactory?.Create(new PromptTemplateConfig(model.Instructions!)) : null;

        // Instantiate the agent
        return
            new OpenAIAssistantAgent(model, clientProvider, client)
            {
                Kernel = kernel,
                Arguments = defaultArguments,
                Template = template,
            };
    }

    /// <summary>
    /// Create a new assistant thread.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The thread identifier</returns>
    public Task<string> CreateThreadAsync(CancellationToken cancellationToken = default)
        => AssistantThreadActions.CreateThreadAsync(this._client, options: null, cancellationToken);

    /// <summary>
    /// Create a new assistant thread.
    /// </summary>
    /// <param name="options">The options for creating the thread</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The thread identifier</returns>
    public Task<string> CreateThreadAsync(OpenAIThreadCreationOptions? options, CancellationToken cancellationToken = default)
        => AssistantThreadActions.CreateThreadAsync(this._client, options, cancellationToken);

    /// <summary>
    /// Create a new assistant thread.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The thread identifier</returns>
    public async Task<bool> DeleteThreadAsync(
        string threadId,
        CancellationToken cancellationToken = default)
    {
        // Validate input
        Verify.NotNullOrWhiteSpace(threadId, nameof(threadId));

        return (await this._client.DeleteThreadAsync(threadId, cancellationToken).ConfigureAwait(false)).Value.Deleted;
    }

    /// <summary>
    /// Uploads an file for the purpose of using with assistant.
    /// </summary>
    /// <param name="stream">The content to upload</param>
    /// <param name="name">The name of the file</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The file identifier</returns>
    /// <remarks>
    /// Use the <see cref="FileClient"/> directly for more advanced file operations.
    /// </remarks>
    public async Task<string> UploadFileAsync(Stream stream, string name, CancellationToken cancellationToken = default)
    {
        FileClient client = this._provider.Client.GetFileClient();

        OpenAIFileInfo fileInfo = await client.UploadFileAsync(stream, name, FileUploadPurpose.Assistants, cancellationToken).ConfigureAwait(false);

        return fileInfo.Id;
    }

    /// <summary>
    /// Adds a message to the specified thread.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="message">A non-system message with which to append to the conversation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public Task AddChatMessageAsync(string threadId, ChatMessageContent message, CancellationToken cancellationToken = default)
    {
        this.ThrowIfDeleted();

        return AssistantThreadActions.CreateMessageAsync(this._client, threadId, message, cancellationToken);
    }

    /// <summary>
    /// Gets messages for a specified thread.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    public IAsyncEnumerable<ChatMessageContent> GetThreadMessagesAsync(string threadId, CancellationToken cancellationToken = default)
    {
        this.ThrowIfDeleted();

        return AssistantThreadActions.GetMessagesAsync(this._client, threadId, cancellationToken);
    }

    /// <summary>
    /// Delete the assistant definition.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>True if assistant definition has been deleted</returns>
    /// <remarks>
    /// Assistant based agent will not be useable after deletion.
    /// </remarks>
    public async Task<bool> DeleteAsync(CancellationToken cancellationToken = default)
    {
        if (!this.IsDeleted)
        {
            this.IsDeleted = (await this._client.DeleteAssistantAsync(this.Id, cancellationToken).ConfigureAwait(false)).Value.Deleted;
        }

        return this.IsDeleted;
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
        => this.InvokeAsync(threadId, options: null, arguments, kernel, cancellationToken);

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
        OpenAIAssistantInvocationOptions? options,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.ThrowIfDeleted();

        kernel ??= this.Kernel;
        arguments ??= this.Arguments;

        await foreach ((bool isVisible, ChatMessageContent message) in AssistantThreadActions.InvokeAsync(this, this._client, threadId, options, this.Logger, kernel, arguments, cancellationToken).ConfigureAwait(false))
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
        => this.InvokeStreamingAsync(threadId, options: null, arguments, kernel, messages, cancellationToken);

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
        OpenAIAssistantInvocationOptions? options,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        ChatHistory? messages = null,
        CancellationToken cancellationToken = default)
    {
        this.ThrowIfDeleted();

        kernel ??= this.Kernel;
        arguments ??= this.Arguments;

        return AssistantThreadActions.InvokeStreamingAsync(this, this._client, threadId, messages, options, this.Logger, kernel, arguments, cancellationToken);
    }

    /// <inheritdoc/>
    protected override IEnumerable<string> GetChannelKeys()
    {
        // Distinguish from other channel types.
        yield return typeof(OpenAIAssistantChannel).FullName!;

        foreach (string key in this._channelKeys)
        {
            yield return key;
        }
    }

    /// <inheritdoc/>
    protected override async Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        this.Logger.LogOpenAIAssistantAgentCreatingChannel(nameof(CreateChannelAsync), nameof(OpenAIAssistantChannel));

        AssistantThread thread = await this._client.CreateThreadAsync(options: null, cancellationToken).ConfigureAwait(false);

        this.Logger.LogInformation("[{MethodName}] Created assistant thread: {ThreadId}", nameof(CreateChannelAsync), thread.Id);

        OpenAIAssistantChannel channel =
            new(this._client, thread.Id)
            {
                Logger = this.LoggerFactory.CreateLogger<OpenAIAssistantChannel>()
            };

        this.Logger.LogOpenAIAssistantAgentCreatedChannel(nameof(CreateChannelAsync), nameof(OpenAIAssistantChannel), thread.Id);

        return channel;
    }

    internal void ThrowIfDeleted()
    {
        if (this.IsDeleted)
        {
            throw new KernelException($"Agent Failure - {nameof(OpenAIAssistantAgent)} agent is deleted: {this.Id}.");
        }
    }

    internal Task<string?> GetInstructionsAsync(Kernel kernel, KernelArguments? arguments, CancellationToken cancellationToken) =>
        this.FormatInstructionsAsync(kernel, arguments, cancellationToken);

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgent"/> class.
    /// </summary>
    private OpenAIAssistantAgent(
        Assistant model,
        OpenAIClientProvider provider,
        AssistantClient client)
    {
        this._provider = provider;
        this._assistant = model;
        this._client = provider.Client.GetAssistantClient();
        this._channelKeys = provider.ConfigurationKeys.ToArray();

        this.Definition = CreateAssistantDefinition(model);

        this.Description = this._assistant.Description;
        this.Id = this._assistant.Id;
        this.Name = this._assistant.Name;
        this.Instructions = this._assistant.Instructions;
    }

    private static OpenAIAssistantDefinition CreateAssistantDefinition(Assistant model)
    {
        OpenAIAssistantExecutionOptions? options = null;

        if (model.Metadata.TryGetValue(OptionsMetadataKey, out string? optionsJson))
        {
            options = JsonSerializer.Deserialize<OpenAIAssistantExecutionOptions>(optionsJson);
        }

        IReadOnlyList<string>? fileIds = (IReadOnlyList<string>?)model.ToolResources?.CodeInterpreter?.FileIds;
        string? vectorStoreId = model.ToolResources?.FileSearch?.VectorStoreIds?.SingleOrDefault();
        bool enableJsonResponse = model.ResponseFormat is not null && model.ResponseFormat == AssistantResponseFormat.JsonObject;

        return new(model.Model)
        {
            Id = model.Id,
            Name = model.Name,
            Description = model.Description,
            Instructions = model.Instructions,
            CodeInterpreterFileIds = fileIds,
            EnableCodeInterpreter = model.Tools.Any(t => t is CodeInterpreterToolDefinition),
            EnableFileSearch = model.Tools.Any(t => t is FileSearchToolDefinition),
            Metadata = model.Metadata,
            EnableJsonResponse = enableJsonResponse,
            TopP = model.NucleusSamplingFactor,
            Temperature = model.Temperature,
            VectorStoreId = string.IsNullOrWhiteSpace(vectorStoreId) ? null : vectorStoreId,
            ExecutionOptions = options,
        };
    }

    private static AssistantClient CreateClient(OpenAIClientProvider config)
    {
        return config.Client.GetAssistantClient();
    }
}
