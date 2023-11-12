// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

/// <summary>
/// Supported OpenAI REST API actions for assistants.
/// </summary>
internal static partial class OpenAIRestExtensions
{
    private const string BaseAssistantUrl = $"{BaseUrl}/assistants";

    /// <summary>
    /// Create a new assistant.
    /// </summary>
    /// <param name="context">An context for accessing OpenAI REST endpoint</param>
    /// <param name="model">The assistant definition</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An assisant definition</returns>
    public static Task<AssistantModel> CreateAssistantModelAsync(
        this IOpenAIRestContext context,
        AssistantModel model,
        CancellationToken cancellationToken = default)
    {
        var payload =
            new
            {
                model = model.Model,
                name = model.Name,
                description = model.Description,
                instructions = model.Instructions,
                tools = model.Tools,
                file_ids = model.FileIds,
                metadata = model.Metadata,
            };

        return
            context.ExecutePostAsync<AssistantModel>(
                BaseAssistantUrl,
                payload,
                cancellationToken);
    }

    /// <summary>
    /// Retrieve an assistant by identifier.
    /// </summary>
    /// <param name="context">An context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An assisant definition</returns>
    public static Task<AssistantModel> GetAssistantModelAsync(
        this IOpenAIRestContext context,
        string assistantId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<AssistantModel>(
                GetAssistantUrl(assistantId),
                cancellationToken);
    }

    /// <summary>
    /// Retrieve all assistants.
    /// </summary>
    /// <param name="context">An context for accessing OpenAI REST endpoint</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An enumeration of assisant definitions</returns>
    public static Task<IList<AssistantModel>> GetAssistantsAsync(
        this IOpenAIRestContext context,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<IList<AssistantModel>>(
                BaseAssistantUrl,
                cancellationToken);
    }

    private static string GetAssistantUrl(string assistantId)
    {
        return $"{BaseAssistantUrl}/{assistantId}";
    }
}
