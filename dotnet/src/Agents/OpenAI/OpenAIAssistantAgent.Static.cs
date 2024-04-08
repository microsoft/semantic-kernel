// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.OpenAI.Assistants;
using Azure.Core.Pipeline;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on Open AI Assistant / GPT.
/// </summary>
public sealed partial class OpenAIAssistantAgent : KernelAgent
{
    /// <summary>
    /// Define a new <see cref="OpenAIAssistantAgent"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="options">Options for accessing the Assistants API service, such as the api-key.</param>
    /// <param name="definition">The assistant definition.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public static async Task<OpenAIAssistantAgent> CreateAsync(
        Kernel kernel,
        OpenAIAssistantServiceOptions options,
        OpenAIAssistantDefinition definition,
        CancellationToken cancellationToken = default)
    {
        // Validate input
        Verify.NotNull(options, nameof(options));
        VerifyOptions(options);

        // Create the client
        AssistantsClient client = CreateClient(options);

        // Create the assistant
        AssistantCreationOptions assistantCreationOptions = CreateAssistantCreationOptions(definition);
        Assistant model = await client.CreateAssistantAsync(assistantCreationOptions, cancellationToken).ConfigureAwait(false);

        // Instantiate the agent
        return new OpenAIAssistantAgent(kernel, client, model, options);

        // Local function to define assistant creation options
        static AssistantCreationOptions CreateAssistantCreationOptions(OpenAIAssistantDefinition definition)
        {
            AssistantCreationOptions assistantCreationOptions =
                new(definition.Model)
                {
                    Description = definition.Description,
                    Instructions = definition.Instructions,
                    Name = definition.Name,
                    Metadata = definition.Metadata,
                };

            foreach (var fileId in definition.FileIds ?? Array.Empty<string>())
            {
                assistantCreationOptions.FileIds.Add(fileId);
            }

            if (definition.EnableCodeIntepreter)
            {
                assistantCreationOptions.Tools.Add(new CodeInterpreterToolDefinition());
            }

            if (definition.EnableRetrieval)
            {
                assistantCreationOptions.Tools.Add(new RetrievalToolDefinition());
            }

            return assistantCreationOptions;
        }
    }

    /// <summary>
    /// Retrieve a list of assistant definitions: <see cref="OpenAIAssistantDefinition"/>.
    /// </summary>
    /// <param name="options">Options for accessing the Assistants API service, such as the api-key.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An list of <see cref="OpenAIAssistantDefinition"/> objects.</returns>
    public static async IAsyncEnumerable<OpenAIAssistantDefinition> ListAsync(
        OpenAIAssistantServiceOptions options,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // Create the client
        AssistantsClient client = CreateClient(options);

        // Retrieve the assistants
        PageableList<Assistant> assistants = await client.GetAssistantsAsync(limit: 100, ListSortOrder.Descending, after: null, before: null, cancellationToken).ConfigureAwait(false);
        foreach (Assistant assistant in assistants)
        {
            yield return
                new()
                {
                    //Id = assistant.Id, $$$
                    Name = assistant.Name,
                    Description = assistant.Description,
                    Instructions = assistant.Instructions,
                    EnableCodeIntepreter = assistant.Tools.Any(t => t is CodeInterpreterToolDefinition),
                    EnableRetrieval = assistant.Tools.Any(t => t is RetrievalToolDefinition),
                    FileIds = assistant.FileIds,
                    //Metadata = assistant.Metadata, $$$
                    Model = assistant.Model,
                };
        }
    }

    /// <summary>
    /// Retrieve a <see cref="OpenAIAssistantAgent"/> by identifier.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="options">Options for accessing the Assistants API service, such as the api-key.</param>
    /// <param name="id">The agent identifier</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public static async Task<OpenAIAssistantAgent> RestoreAsync(
        Kernel kernel,
        OpenAIAssistantServiceOptions options,
        string id,
        CancellationToken cancellationToken = default)
    {
        // Create the client
        AssistantsClient client = CreateClient(options);

        // Retrieve the assistant
        Assistant model = await client.GetAssistantAsync(id, cancellationToken).ConfigureAwait(false);

        // Instantiate the agent
        return new OpenAIAssistantAgent(kernel, client, model, options);
    }

    // $$$ LIST ASYNC

    private static AssistantsClient CreateClient(OpenAIAssistantServiceOptions options)
    {
        AssistantsClientOptions clientOptions = CreateClientOptions(options.HttpClient, options.Version);

        // Inspect options
        if (!string.IsNullOrWhiteSpace(options.Endpoint))
        {
            // Create client configured for Azure Open AI, if endpoint definition is present.
            return new AssistantsClient(new Uri(options.Endpoint), new AzureKeyCredential(options.ApiKey));
        }

        // Otherwise, create client configured for Open AI.
        return new AssistantsClient(options.ApiKey);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="serviceVersion">Optional API version.</param>
    /// <returns>An instance of <see cref="AssistantsClientOptions"/>.</returns>
    private static AssistantsClientOptions CreateClientOptions(HttpClient? httpClient, AssistantsClientOptions.ServiceVersion? serviceVersion)
    {
        AssistantsClientOptions options = serviceVersion is not null ?
            new(serviceVersion.Value) :
            new();

        options.Diagnostics.ApplicationId = HttpHeaderConstant.Values.UserAgent;
        //options.AddPolicy(new AddHeaderRequestPolicy(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(OpenAIAssistantAgent))), HttpPipelinePosition.PerCall); $$$ SCOPING

        if (httpClient is not null)
        {
            options.Transport = new HttpClientTransport(httpClient);
            options.RetryPolicy = new RetryPolicy(maxRetries: 0); // Disable Azure SDK retry policy if and only if a custom HttpClient is provided.
            options.Retry.NetworkTimeout = Timeout.InfiniteTimeSpan; // Disable Azure SDK default timeout
        }

        return options;
    }

    /// <summary>
    /// $$$
    /// </summary>
    private static void VerifyOptions(OpenAIAssistantServiceOptions options)
    {
        //Verify.NotNullOrWhiteSpace(deploymentName); $$$
        //Verify.NotNullOrWhiteSpace(endpoint);
        //Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");
        //Verify.NotNullOrWhiteSpace(apiKey);
    }
}
