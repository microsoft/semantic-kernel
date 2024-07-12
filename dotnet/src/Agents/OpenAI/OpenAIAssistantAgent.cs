// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using OpenAI;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on Open AI Assistant / GPT.
/// </summary>
public sealed class OpenAIAssistantAgent : KernelAgent
{
    private const string SettingsMetadataKey = "__settings";

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
    public RunPollingConfiguration Polling { get; } = new();

    /// <summary>
    /// Expose predefined tools merged with available kernel functions.
    /// </summary>
    internal IReadOnlyList<ToolDefinition> Tools => [.. this._assistant.Tools, .. this.Kernel.Plugins.SelectMany(p => p.Select(f => f.ToToolDefinition(p.Name)))];

    /// <summary>
    /// Define a new <see cref="OpenAIAssistantAgent"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="config">Configuration for accessing the Assistants API service.</param>
    /// <param name="definition">The assistant definition.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public static async Task<OpenAIAssistantAgent> CreateAsync(
        Kernel kernel,
        OpenAIServiceConfiguration config,
        OpenAIAssistantDefinition definition,
        CancellationToken cancellationToken = default)
    {
        // Validate input
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(config, nameof(config));
        Verify.NotNull(definition, nameof(definition));

        // Create the client
        AssistantClient client = CreateClient(config);

        // Create the assistant
        AssistantCreationOptions assistantCreationOptions = CreateAssistantCreationOptions(definition);
        Assistant model = await client.CreateAssistantAsync(definition.ModelName, assistantCreationOptions, cancellationToken).ConfigureAwait(false);

        // Instantiate the agent
        return
            new OpenAIAssistantAgent(client, model, DefineChannelKeys(config))
            {
                Kernel = kernel,
            };
    }

    /// <summary>
    /// Retrieve a list of assistant definitions: <see cref="OpenAIAssistantDefinition"/>.
    /// </summary>
    /// <param name="config">Configuration for accessing the Assistants API service.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An list of <see cref="OpenAIAssistantDefinition"/> objects.</returns>
    public static async IAsyncEnumerable<OpenAIAssistantDefinition> ListDefinitionsAsync(
        OpenAIServiceConfiguration config,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // Create the client
        AssistantClient client = CreateClient(config);

        // Query and enumerate assistant definitions
        await foreach (Assistant model in client.GetAssistantsAsync(ListOrder.NewestFirst, cancellationToken).ConfigureAwait(false))
        {
            yield return CreateAssistantDefinition(model);
        }
    }

    /// <summary>
    /// Retrieve a <see cref="OpenAIAssistantAgent"/> by identifier.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="config">Configuration for accessing the Assistants API service.</param>
    /// <param name="id">The agent identifier</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public static async Task<OpenAIAssistantAgent> RetrieveAsync(
        Kernel kernel,
        OpenAIServiceConfiguration config,
        string id,
        CancellationToken cancellationToken = default)
    {
        // Create the client
        AssistantClient client = CreateClient(config);

        // Retrieve the assistant
        Assistant model = await client.GetAssistantAsync(id).ConfigureAwait(false); // %%% BUG CANCEL TOKEN

        // Instantiate the agent
        return
            new OpenAIAssistantAgent(client, model, DefineChannelKeys(config))
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
        => this.CreateThreadAsync(settings: null, cancellationToken);

    /// <summary>
    /// Create a new assistant thread.
    /// </summary>
    /// <param name="settings">%%%</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The thread identifier</returns>
    public async Task<string> CreateThreadAsync(OpenAIThreadCreationSettings? settings, CancellationToken cancellationToken = default)
    {
        ThreadCreationOptions options =
            new()
            {
                ToolResources = GenerateToolResources(settings?.VectorStoreId, settings?.CodeInterpterFileIds),
            };

        //options.InitialMessages, // %%% TODO

        if (settings?.Metadata != null)
        {
            foreach (KeyValuePair<string, string> item in settings.Metadata)
            {
                options.Metadata[item.Key] = item.Value;
            }
        }

        AssistantThread thread = await this._client.CreateThreadAsync(options, cancellationToken).ConfigureAwait(false);

        return thread.Id;
    }

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
    /// <param name="cancellationToken"></param>
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
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        string threadId,
        CancellationToken cancellationToken = default)
            => this.InvokeAsync(threadId, settings: null, cancellationToken);

    /// <summary>
    /// Invoke the assistant on the specified thread.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="settings">Optional invocation settings</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        string threadId,
        OpenAIAssistantInvocationSettings? settings,
        CancellationToken cancellationToken = default)
    {
        this.ThrowIfDeleted();

        return AssistantThreadActions.InvokeAsync(this, this._client, threadId, settings, this.Logger, cancellationToken);
    }

    /// <inheritdoc/>
    protected override IEnumerable<string> GetChannelKeys() => this._channelKeys;

    /// <inheritdoc/>
    protected override async Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        this.Logger.LogOpenAIAssistantAgentCreatingChannel(nameof(CreateChannelAsync), nameof(OpenAIAssistantChannel));

        AssistantThread thread = await this._client.CreateThreadAsync(options: null, cancellationToken).ConfigureAwait(false);

        this.Logger.LogInformation("[{MethodName}] Created assistant thread: {ThreadId}", nameof(CreateChannelAsync), thread.Id);

        OpenAIAssistantChannel channel =
            new (this._client, thread.Id)
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
        AssistantClient client,
        Assistant model,
        IEnumerable<string> channelKeys)
    {
        this._assistant = model;
        this._client = client;
        this._channelKeys = channelKeys.ToArray();

        this.Definition = CreateAssistantDefinition(model);

        this.Description = this._assistant.Description;
        this.Id = this._assistant.Id;
        this.Name = this._assistant.Name;
        this.Instructions = this._assistant.Instructions;
    }

    private static OpenAIAssistantDefinition CreateAssistantDefinition(Assistant model)
    {
        OpenAIAssistantExecutionSettings? settings = null;

        if (model.Metadata.TryGetValue(SettingsMetadataKey, out string? settingsJson))
        {
            settings = JsonSerializer.Deserialize<OpenAIAssistantExecutionSettings>(settingsJson);
        }

        IReadOnlyList<string>? fileIds = (IReadOnlyList<string>?)model.ToolResources?.CodeInterpreter?.FileIds;
        string? vectorStoreId = model.ToolResources?.FileSearch?.VectorStoreIds?.Single();
        bool enableJsonResponse = model.ResponseFormat is not null && model.ResponseFormat == AssistantResponseFormat.JsonObject;

        return
            new()
            {
                Id = model.Id,
                Name = model.Name,
                Description = model.Description,
                Instructions = model.Instructions,
                CodeInterpterFileIds = fileIds,
                EnableCodeInterpreter = model.Tools.Any(t => t is CodeInterpreterToolDefinition),
                Metadata = model.Metadata,
                ModelName = model.Model,
                EnableJsonResponse = enableJsonResponse,
                TopP = model.NucleusSamplingFactor,
                Temperature = model.Temperature,
                VectorStoreId = vectorStoreId,
                ExecutionSettings = settings,
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
                ToolResources = GenerateToolResources(definition.VectorStoreId, definition.EnableCodeInterpreter ? definition.CodeInterpterFileIds : null),
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

        if (definition.ExecutionSettings != null)
        {
            string settingsJson = JsonSerializer.Serialize(definition.ExecutionSettings);
            assistantCreationOptions.Metadata[SettingsMetadataKey] = settingsJson;
        }

        if (definition.EnableCodeInterpreter)
        {
            assistantCreationOptions.Tools.Add(new CodeInterpreterToolDefinition());
        }

        if (!string.IsNullOrWhiteSpace(definition.VectorStoreId))
        {
            assistantCreationOptions.Tools.Add(new FileSearchToolDefinition());
        }

        return assistantCreationOptions;
    }

    private static ToolResources? GenerateToolResources(string? vectorStoreId, IReadOnlyList<string>? codeInterpreterFileIds)
    {
        bool hasFileSearch = !string.IsNullOrWhiteSpace(vectorStoreId);
        bool hasCodeInterpreterFiles = (codeInterpreterFileIds?.Count ?? 0) > 0;

        ToolResources? toolResources = null;

        if (hasFileSearch || hasCodeInterpreterFiles)
        {
            toolResources =
                new ToolResources()
                {
                    FileSearch =
                        hasFileSearch ?
                            new FileSearchToolResources()
                            {
                                VectorStoreIds = [vectorStoreId!],
                            } :
                            null,
                    CodeInterpreter =
                        hasCodeInterpreterFiles ?
                            new CodeInterpreterToolResources()
                            {
                                FileIds = (IList<string>)codeInterpreterFileIds!,
                            } :
                            null,
                };
        }

        return toolResources;
    }

    private static AssistantClient CreateClient(OpenAIServiceConfiguration config)
    {
        OpenAIClient openAIClient = OpenAIClientFactory.CreateClient(config);
        return openAIClient.GetAssistantClient();
    }

    private static IEnumerable<string> DefineChannelKeys(OpenAIServiceConfiguration config)
    {
        // Distinguish from other channel types.
        yield return typeof(AgentChannel<OpenAIAssistantAgent>).FullName!;

        // Distinguish between different Azure OpenAI endpoints or OpenAI services.
        yield return config.Endpoint != null ? config.Endpoint.ToString() : "openai";

        // Custom client receives dedicated channel.
        if (config.HttpClient is not null)
        {
            if (config.HttpClient.BaseAddress is not null)
            {
                yield return config.HttpClient.BaseAddress.AbsoluteUri;
            }

            foreach (string header in config.HttpClient.DefaultRequestHeaders.SelectMany(h => h.Value))
            {
                yield return header;
            }
        }
    }
}
