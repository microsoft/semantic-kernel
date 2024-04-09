// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.OpenAI.Assistants;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.SemanticKernel.Agents.OpenAI.Azure;
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
    /// <param name="config">Configuration for accessing the Assistants API service, such as the api-key.</param>
    /// <param name="definition">The assistant definition.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public static async Task<OpenAIAssistantAgent> CreateAsync(
        Kernel kernel,
        OpenAIAssistantConfiguration config,
        OpenAIAssistantDefinition definition,
        CancellationToken cancellationToken = default)
    {
        // Validate input
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(config, nameof(config));
        Verify.NotNull(definition, nameof(definition));

        // Create the client
        AssistantsClient client = CreateClient(config);

        // Create the assistant
        AssistantCreationOptions assistantCreationOptions = CreateAssistantCreationOptions(definition);
        Assistant model = await client.CreateAssistantAsync(assistantCreationOptions, cancellationToken).ConfigureAwait(false);

        // Instantiate the agent
        return
            new OpenAIAssistantAgent(client, model, config)
            {
                Kernel = kernel,
            };

        // Local function to define assistant creation options
        static AssistantCreationOptions CreateAssistantCreationOptions(OpenAIAssistantDefinition definition)
        {
            AssistantCreationOptions assistantCreationOptions =
                new(definition.Model)
                {
                    Description = definition.Description,
                    Instructions = definition.Instructions,
                    Name = definition.Name,
                    Metadata = definition.Metadata?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value),
                };

            foreach (var fileId in definition.FileIds ?? Array.Empty<string>())
            {
                assistantCreationOptions.FileIds.Add(fileId);
            }

            if (definition.EnableCodeInterpreter)
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
    /// <param name="config">Configuration for accessing the Assistants API service, such as the api-key.</param>
    /// <param name="maxResults">The maximum number of assistant definitions to retrieve</param>
    /// <param name="lastId">The identifier of the assistant beyond which to begin selection.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An list of <see cref="OpenAIAssistantDefinition"/> objects.</returns>
    public static async IAsyncEnumerable<OpenAIAssistantDefinition> ListAsync(
        OpenAIAssistantConfiguration config,
        int maxResults = 100,
        string? lastId = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // Create the client
        AssistantsClient client = CreateClient(config);

        // Retrieve the assistants
        PageableList<Assistant> assistants;

        int resultCount = 0;
        do
        {
            assistants = await client.GetAssistantsAsync(limit: 100, ListSortOrder.Descending, after: null, before: null, cancellationToken).ConfigureAwait(false);
            foreach (Assistant assistant in assistants)
            {
                resultCount++;

                if (resultCount >= maxResults)
                {
                    break;
                }

                yield return
                    new()
                    {
                        Id = assistant.Id,
                        Name = assistant.Name,
                        Description = assistant.Description,
                        Instructions = assistant.Instructions,
                        EnableCodeInterpreter = assistant.Tools.Any(t => t is CodeInterpreterToolDefinition),
                        EnableRetrieval = assistant.Tools.Any(t => t is RetrievalToolDefinition),
                        FileIds = assistant.FileIds,
                        Metadata = assistant.Metadata,
                        Model = assistant.Model,
                    };

                lastId = assistant.Id;
            }
        }
        while (assistants.HasMore && resultCount < maxResults);
    }

    /// <summary>
    /// Retrieve a <see cref="OpenAIAssistantAgent"/> by identifier.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="config">Configuration for accessing the Assistants API service, such as the api-key.</param>
    /// <param name="id">The agent identifier</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="OpenAIAssistantAgent"/> instance</returns>
    public static async Task<OpenAIAssistantAgent> RestoreAsync(
        Kernel kernel,
        OpenAIAssistantConfiguration config,
        string id,
        CancellationToken cancellationToken = default)
    {
        // Create the client
        AssistantsClient client = CreateClient(config);

        // Retrieve the assistant
        Assistant model = await client.GetAssistantAsync(id, cancellationToken).ConfigureAwait(false);

        // Instantiate the agent
        return
            new OpenAIAssistantAgent(client, model, config)
            {
                Kernel = kernel,
            };
    }

    private static AssistantsClient CreateClient(OpenAIAssistantConfiguration config)
    {
        AssistantsClientOptions clientOptions = CreateClientOptions(config);

        // Inspect options
        if (!string.IsNullOrWhiteSpace(config.Endpoint))
        {
            // Create client configured for Azure Open AI, if endpoint definition is present.
            return new AssistantsClient(new Uri(config.Endpoint), new AzureKeyCredential(config.ApiKey));
        }

        // Otherwise, create client configured for Open AI.
        return new AssistantsClient(config.ApiKey);
    }

    private static AssistantsClientOptions CreateClientOptions(OpenAIAssistantConfiguration config)
    {
        AssistantsClientOptions options =
            config.Version.HasValue ?
                new(config.Version.Value) :
                new();

        options.Diagnostics.ApplicationId = HttpHeaderConstant.Values.UserAgent;
        options.AddPolicy(new AddHeaderRequestPolicy(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(OpenAIAssistantAgent))), HttpPipelinePosition.PerCall);

        if (config.HttpClient is not null)
        {
            options.Transport = new HttpClientTransport(config.HttpClient);
            options.RetryPolicy = new RetryPolicy(maxRetries: 0); // Disable Azure SDK retry policy if and only if a custom HttpClient is provided.
            options.Retry.NetworkTimeout = Timeout.InfiniteTimeSpan; // Disable Azure SDK default timeout
        }

        return options;
    }
}
