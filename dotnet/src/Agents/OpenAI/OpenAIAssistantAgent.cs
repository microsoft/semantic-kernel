// Copyright (c) Microsoft. All rights reserved.
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
<<<<<<< main
using System.ClientModel;
=======
using System;
>>>>>>> origin/PR
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
>>>>>>> Stashed changes
=======
using System.ClientModel;
using System;
>>>>>>> main
<<<<<<< Updated upstream
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
using System.ClientModel;
using System;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using OpenAI;
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
using OpenAI;
=======
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
using OpenAI;
=======
>>>>>>> main
>>>>>>> Stashed changes
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
    internal const string TemplateMetadataKey = "__template_format";
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
    internal const string TemplateMetadataKey = "__template_format";
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
    internal const string TemplateMetadataKey = "__template_format";
>>>>>>> main
>>>>>>> Stashed changes

    private readonly OpenAIClientProvider _provider;
    private readonly Assistant _assistant;
    private readonly AssistantClient _client;
    private readonly string[] _channelKeys;

    /// <summary>
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
    /// Optional arguments for the agent.
    /// </summary>
    /// <remarks>
    /// This property is not currently used by the agent, but is provided for future extensibility.
    /// </remarks>
    public KernelArguments? Arguments { get; init; }

    /// <summary>
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
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< HEAD
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
>>>>>>> main
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// Define a new <see cref="OpenAIAssistantAgent"/>.
    /// </summary>
    /// <param name="clientProvider">OpenAI client provider for accessing the API service.</param>
    /// <param name="capabilities">Defines the assistant's capabilities.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="defaultArguments">Optional default arguments, including any <see cref="PromptExecutionSettings"/>.</param>
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
        AssistantCreationOptions assistantCreationOptions = templateConfig.CreateAssistantCreationOptions(capabilities);
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
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
    /// Expose predefined tools for run-processing.
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
    /// Expose predefined tools for run-processing.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
    /// Expose predefined tools for run-processing.
>>>>>>> Stashed changes
    /// </summary>
    internal IReadOnlyList<ToolDefinition> Tools => this._assistant.Tools;

    /// <summary>
    /// Define a new <see cref="OpenAIAssistantAgent"/>.
    /// </summary>
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
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="clientProvider">OpenAI client provider for accessing the API service.</param>
    /// <param name="definition">The assistant definition.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public static async Task<OpenAIAssistantAgent> CreateAsync(
        Kernel kernel,
        OpenAIClientProvider clientProvider,
        OpenAIAssistantDefinition definition,
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
        CancellationToken cancellationToken = default)
    {
        // Validate input
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(clientProvider, nameof(clientProvider));
        Verify.NotNull(definition, nameof(definition));

        // Create the client
        AssistantClient client = CreateClient(clientProvider);

        // Create the assistant
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        AssistantCreationOptions assistantCreationOptions = CreateAssistantCreationOptions(definition);
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
        AssistantCreationOptions assistantCreationOptions = CreateAssistantCreationOptions(definition);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        AssistantCreationOptions assistantCreationOptions = CreateAssistantCreationOptions(definition);
=======
>>>>>>> Stashed changes
        AssistantCreationOptions assistantCreationOptions = definition.CreateAssistantCreationOptions();
        AssistantCreationOptions assistantCreationOptions = definition.CreateAssistantOptions();
        AssistantCreationOptions assistantCreationOptions = CreateAssistantCreationOptions(definition);
        AssistantCreationOptions assistantCreationOptions = definition.CreateAssistantOptions();
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
        Assistant model = await client.CreateAssistantAsync(definition.ModelId, assistantCreationOptions, cancellationToken).ConfigureAwait(false);

        // Instantiate the agent
        return
            new OpenAIAssistantAgent(model, clientProvider, client)
            {
                Kernel = kernel,
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
                Arguments = defaultArguments
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
                Arguments = defaultArguments
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
                Arguments = defaultArguments
>>>>>>> main
>>>>>>> Stashed changes
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
        await foreach (var page in client.GetAssistantsAsync(new AssistantCollectionOptions() { Order = ListOrder.NewestFirst }, cancellationToken).ConfigureAwait(false))
        await foreach (PageResult<Assistant> page in client.GetAssistantsAsync(new AssistantCollectionOptions() { Order = ListOrder.NewestFirst }, cancellationToken).ConfigureAwait(false))
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
        {
            foreach (Assistant model in page.Values)
            {
                yield return CreateAssistantDefinition(model);
            }
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
>>>>>>> Stashed changes
=======
        await foreach (Assistant model in client.GetAssistantsAsync(new AssistantCollectionOptions() { Order = AssistantCollectionOrder.Descending }, cancellationToken).ConfigureAwait(false))
        {
            yield return CreateAssistantDefinition(model);
>>>>>>> main
<<<<<<< Updated upstream
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
        await foreach (Assistant model in client.GetAssistantsAsync(new AssistantCollectionOptions() { Order = AssistantCollectionOrder.Descending }, cancellationToken).ConfigureAwait(false))
        {
            yield return CreateAssistantDefinition(model);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        }
    }

    /// <summary>
    /// Retrieve a <see cref="OpenAIAssistantAgent"/> by identifier.
    /// </summary>
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
    /// <param name="clientProvider">Configuration for accessing the API service.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="provider">Configuration for accessing the API service.</param>
    /// <param name="id">The agent identifier</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="defaultArguments">Optional default arguments, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="templateFactory">An optional factory to produce the <see cref="IPromptTemplate"/> for the agent</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public static async Task<OpenAIAssistantAgent> RetrieveAsync(
        OpenAIClientProvider clientProvider,
        Kernel kernel,
        OpenAIClientProvider provider,
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
        AssistantClient client = CreateClient(provider);

        // Retrieve the assistant
        Assistant model = await client.GetAssistantAsync(id, cancellationToken).ConfigureAwait(false);

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
        // Instantiate the agent
        return
            new OpenAIAssistantAgent(model, provider, client)
            {
                Kernel = kernel,
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
        // Ensure template is valid (avoid failure after posting assistant creation)
        IPromptTemplate? template =
            !string.IsNullOrWhiteSpace(model.Instructions) ?
                templateFactory?.Create(new PromptTemplateConfig(model.Instructions!)) :
                null;

        // Instantiate the agent
        return
            new OpenAIAssistantAgent(model, clientProvider, client)
            new OpenAIAssistantAgent(model, provider, client)
            {
                Kernel = kernel,
                Arguments = defaultArguments,
                Template = template,
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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        return await this._client.DeleteThreadAsync(threadId, cancellationToken).ConfigureAwait(false);
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
>>>>>>> Stashed changes
        return await this._client.DeleteThreadAsync(threadId, cancellationToken).ConfigureAwait(false);
=======
        ThreadDeletionResult result = await this._client.DeleteThreadAsync(threadId, cancellationToken).ConfigureAwait(false);

        return result.Deleted;
>>>>>>> main
<<<<<<< Updated upstream
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
        ThreadDeletionResult result = await this._client.DeleteThreadAsync(threadId, cancellationToken).ConfigureAwait(false);

        return result.Deleted;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
    }

    /// <summary>
    /// Uploads an file for the purpose of using with assistant.
    /// </summary>
    /// <param name="stream">The content to upload</param>
    /// <param name="name">The name of the file</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The file identifier</returns>
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
    /// Use the <see cref="FileClient"/> directly for more advanced file operations.
    /// </remarks>
    public async Task<string> UploadFileAsync(Stream stream, string name, CancellationToken cancellationToken = default)
    {
        FileClient client = this._provider.Client.GetFileClient();

        OpenAIFileInfo fileInfo = await client.UploadFileAsync(stream, name, FileUploadPurpose.Assistants, cancellationToken).ConfigureAwait(false);
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
    /// Use the <see cref="OpenAIFileClient"/> directly for more advanced file operations.
    /// </remarks>
    public async Task<string> UploadFileAsync(Stream stream, string name, CancellationToken cancellationToken = default)
    {
        OpenAIFileClient client = this._provider.Client.GetOpenAIFileClient();

        OpenAIFile fileInfo = await client.UploadFileAsync(stream, name, FileUploadPurpose.Assistants, cancellationToken).ConfigureAwait(false);
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            this.IsDeleted = (await this._client.DeleteAssistantAsync(this.Id, cancellationToken).ConfigureAwait(false)).Value;
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
>>>>>>> Stashed changes
            this.IsDeleted = (await this._client.DeleteAssistantAsync(this.Id, cancellationToken).ConfigureAwait(false)).Value;
=======
            AssistantDeletionResult result = await this._client.DeleteAssistantAsync(this.Id, cancellationToken).ConfigureAwait(false);
            this.IsDeleted = result.Deleted;
>>>>>>> main
<<<<<<< Updated upstream
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
            AssistantDeletionResult result = await this._client.DeleteAssistantAsync(this.Id, cancellationToken).ConfigureAwait(false);
            this.IsDeleted = result.Deleted;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <returns>Asynchronous enumeration of messages.</returns>
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
    /// <returns>Asynchronous enumeration of messages.</returns>
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
    /// <returns>Asynchronous enumeration of messages.</returns>
=======
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <returns>Asynchronous enumeration of messages.</returns>
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
>>>>>>> Stashed changes
    /// <returns>Asynchronous enumeration of messages.</returns>
=======
    /// <returns>Asynchronous enumeration of response messages.</returns>
>>>>>>> main
<<<<<<< Updated upstream
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
    /// <returns>Asynchronous enumeration of response messages.</returns>
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        arguments ??= this.Arguments;
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
>>>>>>> Stashed changes
        arguments ??= this.Arguments;
=======
        arguments = this.MergeArguments(arguments);
>>>>>>> main
<<<<<<< Updated upstream
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
        arguments = this.MergeArguments(arguments);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

        await foreach ((bool isVisible, ChatMessageContent message) in AssistantThreadActions.InvokeAsync(this, this._client, threadId, options, this.Logger, kernel, arguments, cancellationToken).ConfigureAwait(false))
        {
            if (isVisible)
            {
                yield return message;
            }
        }
    }

    /// <summary>
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
    /// Invoke the assistant on the specified thread.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="messages">The receiver for the completed messages generated</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
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
    /// Invoke the assistant on the specified thread with streaming response.
    /// </summary>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="messages">Optional receiver of the completed messages generated</param>
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
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// The `arguments` parameter is not currently used by the agent, but is provided for future extensibility.
    /// </remarks>
    public IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        string threadId,
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
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// The `arguments` parameter is not currently used by the agent, but is provided for future extensibility.
    /// </remarks>
    public IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        string threadId,
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
        ChatHistory messages,
        OpenAIAssistantInvocationOptions? options,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
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
        OpenAIAssistantInvocationOptions? options,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        ChatHistory? messages = null,
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
        CancellationToken cancellationToken = default)
    {
        this.ThrowIfDeleted();

        kernel ??= this.Kernel;
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        arguments ??= this.Arguments;
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
>>>>>>> Stashed changes
        arguments ??= this.Arguments;
=======
        arguments = this.MergeArguments(arguments);
>>>>>>> main
<<<<<<< Updated upstream
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
        arguments = this.MergeArguments(arguments);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

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
        this.Logger.LogDebug("[{MethodName}] Creating assistant thread", nameof(CreateChannelAsync));

        AssistantThread thread = await this._client.CreateThreadAsync(cancellationToken).ConfigureAwait(false);

        this.Logger.LogInformation("[{MethodName}] Created assistant thread: {ThreadId}", nameof(CreateChannelAsync), thread.Id);

    internal void ThrowIfDeleted()
    {
        if (this.IsDeleted)
        {
            throw new KernelException($"Agent Failure - {nameof(OpenAIAssistantAgent)} agent is deleted: {this.Id}.");
        }
    }

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
    internal Task<string?> GetInstructionsAsync(Kernel kernel, KernelArguments? arguments, CancellationToken cancellationToken) =>
        this.FormatInstructionsAsync(kernel, arguments, cancellationToken);
    /// <inheritdoc/>
    protected override async Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        string threadId = channelState;

        this.Logger.LogOpenAIAssistantAgentRestoringChannel(nameof(RestoreChannelAsync), nameof(OpenAIAssistantChannel), threadId);

        AssistantThread thread = await this._client.GetThreadAsync(threadId, cancellationToken).ConfigureAwait(false);

        this.Logger.LogOpenAIAssistantAgentRestoredChannel(nameof(RestoreChannelAsync), nameof(OpenAIAssistantChannel), threadId);

        return new OpenAIAssistantChannel(this._client, thread.Id, this._config.Polling);
    }

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
>>>>>>> Stashed changes
=======
    {
        OpenAIAssistantExecutionOptions? options = null;
>>>>>>> main
<<<<<<< Updated upstream
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
    {
        OpenAIAssistantExecutionOptions? options = null;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        if (definition.EnableCodeInterpreter)
        {
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
        if (definition.EnableCodeInterpreter)
        {
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        if (definition.EnableCodeInterpreter)
        {
=======
>>>>>>> Stashed changes
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

    private static IEnumerable<string> DefineChannelKeys(OpenAIClientProvider config)
    {
        // Distinguish from other channel types.
        yield return typeof(AgentChannel<OpenAIAssistantAgent>).FullName!;

        foreach (string key in config.ConfigurationKeys)
        {
            yield return key;
        }
    }
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
}
