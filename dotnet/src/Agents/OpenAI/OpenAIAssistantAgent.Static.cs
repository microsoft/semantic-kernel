// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Net.Http;
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
    /// <param name="apiKey">The Assistants API Key</param>
    /// <param name="definition">$$$</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An agent instance</returns>
    public static async Task<OpenAIAssistantAgent> CreateAsync(
        Kernel kernel,
        string apiKey,
        OpenAIAssistantDefinition definition,
        CancellationToken cancellationToken = default)
    {
        //Verify.NotNullOrWhiteSpace(deploymentName); $$$
        //Verify.NotNullOrWhiteSpace(endpoint);
        //Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");
        //Verify.NotNullOrWhiteSpace(apiKey);

        AssistantsClient client = CreateClient(apiKey, endpoint: null, out var partitionKey); // $$$ ENDPOINT

        AssistantCreationOptions options =
            new(definition.Model)
            {
                Description = definition.Description,
                Instructions = definition.Instructions,
                Name = definition.Name,
                Metadata = definition.Metadata,
            };

        foreach (var fileId in definition.FileIds ?? Array.Empty<string>())
        {
            options.FileIds.Add(fileId);
        }

        if (definition.EnableCodeIntepreter)
        {
            options.Tools.Add(new CodeInterpreterToolDefinition());
        }

        if (definition.EnableRetrieval)
        {
            options.Tools.Add(new RetrievalToolDefinition());
        }

        Assistant model = await client.CreateAssistantAsync(options, cancellationToken).ConfigureAwait(false);

        return new OpenAIAssistantAgent(client, model, kernel, partitionKey);
    }

    /// <summary>
    /// Retrieve a <see cref="OpenAIAssistantAgent"/> by identifier.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="apiKey">The Assistants API Key</param>
    /// <param name="id">The agent identifier</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An agent instance</returns>
    public static async Task<OpenAIAssistantAgent> RestoreAsync(Kernel kernel, string apiKey, string id, CancellationToken cancellationToken)
    {
        AssistantsClient client = CreateClient(apiKey, endpoint: null, out var partitionKey); // $$$ ENDPOINT, VERSION, HTTPPIPELINETRANSPORT, RETRYOPTIONS

        Assistant model = await client.GetAssistantAsync(id, cancellationToken).ConfigureAwait(false);

        return new OpenAIAssistantAgent(client, model, kernel, partitionKey);
    }

    private static AssistantsClient CreateClient(string apiKey, string? endpoint, out string partitionKey)
    {
        if (!string.IsNullOrWhiteSpace(endpoint))
        {
            partitionKey = endpoint!;
            return new AssistantsClient(new Uri(endpoint), new AzureKeyCredential(apiKey), CreateClientOptions(null, null)); // $$$ OPTIONS PARAMS
        }

        partitionKey = "openai";
        return new AssistantsClient(apiKey);
    }

    /// <summary>Gets options to use for an OpenAIClient</summary>
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
}
