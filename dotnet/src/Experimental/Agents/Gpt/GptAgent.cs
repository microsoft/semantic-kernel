// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.OpenAI.Assistants;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Experimental.Agents.Gpt;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on Open AI Assistant / GPT.
/// </summary>
public sealed class GptAgent : KernelAgent<GptChannel>
{
    private readonly Assistant _assistant;
    private readonly AssistantsClient _client;

    /// <inheritdoc/>
    public override string? Description => this._assistant.Description;

    /// <inheritdoc/>
    public override string Id => this._assistant.Id;

    /// <inheritdoc/>
    public override string? Instructions => this._assistant.Instructions;

    /// <inheritdoc/>
    public override string? Name => this._assistant.Name;

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="apiKey"></param>
    /// <param name="instructions"></param>
    /// <param name="description"></param>
    /// <param name="name"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static async Task<GptAgent> CreateAsync(
        Kernel kernel,
        string apiKey,
        string? instructions,
        string? description,
        string? name,
        CancellationToken cancellationToken = default)
    {
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var model = GetModel(service);
        var client = CreateClient(service, apiKey);

        var options =
            new AssistantCreationOptions(model)
            {
                Description = description,
                Instructions = instructions,
                Name = name,
                // $$$ METADATA / FILEIDS
            };

        var response = await client.CreateAssistantAsync(options, cancellationToken).ConfigureAwait(false);

        return new GptAgent(client, response, kernel);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="apiKey"></param>
    /// <param name="id"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static async Task<GptAgent> RestoreAsync(Kernel kernel, string apiKey, string id, CancellationToken cancellationToken)
    {
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var client = CreateClient(service, apiKey);

        var response = await client.GetAssistantAsync(id, cancellationToken).ConfigureAwait(false);

        return new GptAgent(client, response, kernel);
    }

    /// <inheritdoc/>
    protected internal override async Task<AgentChannel> CreateChannelAsync(AgentNexus nexus, CancellationToken cancellationToken)
    {
        var thread = await this._client.CreateThreadAsync(cancellationToken).ConfigureAwait(false);

        return new GptChannel(this._client, thread.Value.Id);
    }

    private static AssistantsClient CreateClient(IChatCompletionService service, string apiKey)
    {
        if (service is AzureOpenAIChatCompletionService azureService)
        {
            return new AssistantsClient(new Uri(azureService.GetEndpoint()), new AzureKeyCredential(apiKey)); // $$$ OPTIONS
        }

        if (service is OpenAIChatCompletionService openaiService)
        {
            return new AssistantsClient(apiKey); // $$$ OPTIONS
        }

        throw new InvalidOperationException("$$$");
    }

    private static string GetModel(IChatCompletionService service)
    {
        string? model = null;

        if (service is AzureOpenAIChatCompletionService azureService)
        {
            model = azureService.GetDeploymentName();
        }

        if (service is OpenAIChatCompletionService openaiService)
        {
            model = openaiService.GetModelId();
        }

        return model ?? throw new InvalidOperationException("$$$");
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GptAgent"/> class.
    /// </summary>
    private GptAgent(AssistantsClient client, Assistant model, Kernel kernel)
        : base(kernel)
    {
        this._assistant = model;
        this._client = client;
    }
}
