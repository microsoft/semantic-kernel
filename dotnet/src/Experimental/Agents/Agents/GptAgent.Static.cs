// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI.Assistants;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents.Agents;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on Open AI Assistant / GPT.
/// </summary>
public sealed partial class GptAgent : KernelAgent
{
    /// <summary>
    /// Define a new <see cref="GptAgent"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="apiKey">The Assistants API Key</param>
    /// <param name="instructions">The agent instructions</param>
    /// <param name="description">The agent description (optional)</param>
    /// <param name="name">The agent name</param>
    /// <param name="enableCodeIntepreter">Enable code-intepreter tool</param>
    /// <param name="enableRetrieval">Enable retrieval tool</param>
    /// <param name="fileIds">$$$</param>
    /// <param name="metadata">Agent metadata</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An agent instance</returns>
    public static async Task<GptAgent> CreateAsync(
        Kernel kernel,
        string apiKey,
        string? instructions,
        string? description,
        string? name,
        bool enableCodeIntepreter = false,
        bool enableRetrieval = false,
        IEnumerable<string>? fileIds = null,
        IDictionary<string, string>? metadata = null,
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
                Metadata = metadata,
            };

        foreach (var fileId in fileIds ?? Array.Empty<string>())
        {
            options.FileIds.Add(fileId);
        }

        if (enableCodeIntepreter)
        {
            options.Tools.Add(new CodeInterpreterToolDefinition());
        }

        if (enableRetrieval)
        {
            options.Tools.Add(new RetrievalToolDefinition());
        }

        var response = await client.CreateAssistantAsync(options, cancellationToken).ConfigureAwait(false);

        return new GptAgent(client, response, kernel);
    }

    /// <summary>
    /// Retrieve a <see cref="GptAgent"/> by identifier.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="apiKey">The Assistants API Key</param>
    /// <param name="id">The agent identifier</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An agent instance</returns>
    public static async Task<GptAgent> RestoreAsync(Kernel kernel, string apiKey, string id, CancellationToken cancellationToken)
    {
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var client = CreateClient(service, apiKey);

        var response = await client.GetAssistantAsync(id, cancellationToken).ConfigureAwait(false);

        return new GptAgent(client, response, kernel);
    }
}
