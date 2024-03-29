// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.OpenAI.Assistants;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Experimental.Agents.Agents;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on Open AI Assistant / GPT.
/// </summary>
public sealed partial class GptAgent : KernelAgent
{
    private readonly Assistant _assistant;
    private readonly string _partitionKey;
    private readonly AssistantsClient _client;

    /// <inheritdoc/>
    public override string? Description => this._assistant.Description;

    /// <inheritdoc/>
    public override string Id => this._assistant.Id;

    /// <inheritdoc/>
    public override string? Name => this._assistant.Name;

    /// <summary>
    /// Expose predefined tools.
    /// </summary>
    internal IReadOnlyList<ToolDefinition> Tools => this._assistant.Tools;

    /// <inheritdoc/>
    protected internal override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(GptChannel).FullName;
        yield return this._partitionKey;
    }

    /// <inheritdoc/>
    protected internal override async Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        var thread = await this._client.CreateThreadAsync(cancellationToken).ConfigureAwait(false);

        return new GptChannel(this._client, thread.Value.Id);
    }

    private static AssistantsClient CreateClient(IChatCompletionService service, string apiKey, out string partitionKey)
    {
        if (service is AzureOpenAIChatCompletionService azureService)
        {
            partitionKey = azureService.GetEndpoint() ?? throw new AgentException("No endpoint defined");
            return new AssistantsClient(new Uri(partitionKey), new AzureKeyCredential(apiKey));
        }

        if (service is OpenAIChatCompletionService openaiService)
        {
            partitionKey = "openai";
            return new AssistantsClient(apiKey);
        }

        throw new AgentException("Missing IChatCompletionService");
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

        return model ?? throw new AgentException("Unable to determine model.");
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GptAgent"/> class.
    /// </summary>
    private GptAgent(AssistantsClient client, Assistant model, Kernel kernel, string partitionKey)
        : base(kernel, model.Instructions)
    {
        this._assistant = model;
        this._client = client;
        this._partitionKey = partitionKey;
    }
}
