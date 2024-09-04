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

    private readonly OpenAIClientProvider _provider;
    private readonly Assistant _assistant;
    private readonly AssistantClient _client;
    private readonly string[] _channelKeys;

    /// <summary>
    /// Optional arguments for the agent.
    /// </summary>
    /// <remarks>
    /// This property is not currently used by the agent, but is provided for future extensibility.
    /// </remarks>
    public KernelArguments? Arguments { get; init; }

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
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="clientProvider">OpenAI client provider for accessing the API service.</param>
    /// <param name="definition">The assistant definition.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public static async Task<OpenAIAssistantAgent> CreateAsync(
        Kernel kernel,
        OpenAIClientProvider clientProvider,
        OpenAIAssistantDefinition definition,
        CancellationToken cancellationToken = default)
    {
        // Validate input
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(clientProvider, nameof(clientProvider));
        Verify.NotNull(definition, nameof(definition));

        // Create the client
        AssistantClient client = CreateClient(clientProvider);

        // Create the assistant
        AssistantCreationOptions assistantCreationOptions = CreateAssistantCreationOptions(definition);
        Assistant model = await client.CreateAssistantAsync(definition.ModelId, assistantCreationOptions, cancellationToken).ConfigureAwait(false);

        // Instantiate the agent
        return
            new OpenAIAssistantAgent(model, clientProvider, client)
            {
                Kernel = kernel,
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
        await foreach (PageResult<Assistant> page in client.GetAssistantsAsync(new AssistantCollectionOptions() { Order = ListOrder.NewestFirst }, cancellationToken).ConfigureAwait(false))
        {
            foreach (Assistant model in page.Values)
            {
                yield return CreateAssistantDefinition(model);
            }
        }
    }

    /// <summary>
    /// Retrieve a <see cref="OpenAIAssistantAgent"/> by identifier.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="provider">Configuration for accessing the API service.</param>
    /// <param name="id">The agent identifier</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public static async Task<OpenAIAssistantAgent> RetrieveAsync(
        Kernel kernel,
        OpenAIClientProvider provider,
        string id,
        CancellationToken cancellationToken = default)
    {
        // Create the client
        AssistantClient client = CreateClient(provider);

        // Retrieve the assistant
        Assistant model = await client.GetAssistantAsync(id, cancellationToken).ConfigureAwait(false);

        // Instantiate the agent
        return
            new OpenAIAssistantAgent(model, provider, client)
            {
                Kernel = kernel,
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

        return await this._client.DeleteThreadAsync(threadId, cancellationToken).ConfigureAwait(false);
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
            this.IsDeleted = (await this._client.DeleteAssistantAsync(this.Id, cancellationToken).ConfigureAwait(false)).Value;
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
    /// <returns>Asynchronous enumeration of messages.</returns>
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
    /// <returns>Asynchronous enumeration of messages.</returns>
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
    /// Invoke the assistant on the specified thread.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="messages">The receiver for the completed messages generated</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// The `arguments` parameter is not currently used by the agent, but is provided for future extensibility.
    /// </remarks>
    public IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        string threadId,
        ChatHistory messages,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
            => this.InvokeStreamingAsync(threadId, messages, options: null, arguments, kernel, cancellationToken);

    /// <summary>
    /// Invoke the assistant on the specified thread.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="messages">The receiver for the completed messages generated</param>
    /// <param name="options">Optional invocation options</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// The `arguments` parameter is not currently used by the agent, but is provided for future extensibility.
    /// </remarks>
    public IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        string threadId,
        ChatHistory messages,
        OpenAIAssistantInvocationOptions? options,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
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

    private static AssistantCreationOptions CreateAssistantCreationOptions(OpenAIAssistantDefinition definition)
    {
        AssistantCreationOptions assistantCreationOptions =
            new()
            {
                Description = definition.Description,
                Instructions = definition.Instructions,
                Name = definition.Name,
                ToolResources =
                    AssistantToolResourcesFactory.GenerateToolResources(
                        definition.EnableFileSearch ? definition.VectorStoreId : null,
                        definition.EnableCodeInterpreter ? definition.CodeInterpreterFileIds : null),
                ResponseFormat = definition.EnableJsonResponse ? AssistantResponseFormat.JsonObject : AssistantResponseFormat.Auto,
                Temperature = definition.Temperature,
                NucleusSamplingFactor = definition.TopP,
            };

        if (definition.Metadata != null)
        {
            foreach (KeyValuePair<string, string> item in definition.Metadata)
            {
                assistantCreationOptions.Metadata[item.Key] = item.Value;
            }
        }

        if (definition.ExecutionOptions != null)
        {
            string optionsJson = JsonSerializer.Serialize(definition.ExecutionOptions);
            assistantCreationOptions.Metadata[OptionsMetadataKey] = optionsJson;
        }

        if (definition.EnableCodeInterpreter)
        {
            assistantCreationOptions.Tools.Add(ToolDefinition.CreateCodeInterpreter());
        }

        if (definition.EnableFileSearch)
        {
            assistantCreationOptions.Tools.Add(ToolDefinition.CreateFileSearch());
        }

        return assistantCreationOptions;
    }

    private static AssistantClient CreateClient(OpenAIClientProvider config)
    {
        return config.Client.GetAssistantClient();
    }

    private static IEnumerable<string> DefineChannelKeys(OpenAIClientProvider config)
    {
        // Distinguish from other channel types.
        yield return typeof(AgentChannel<OpenAIAssistantAgent>).FullName!;

        foreach (string key in config.ConfigurationKeys)
        {
            yield return key;
        }
    }
}
