// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Supported OpenAI REST API actions for managing assistant files.
/// </summary>
internal static partial class OpenAIRestExtensions
{
    /// <summary>
    /// Associate uploaded file with the assistant, by identifier.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="fileId">The identifier of the uploaded file.</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An assistant definition</returns>
    public static async Task<string> AddAssistantFileAsync(
        this OpenAIRestContext context,
        string assistantId,
        string fileId,
        CancellationToken cancellationToken = default)
    {
        var payload =
            new
            {
                file_id = fileId
            };

        var result =
            await context.ExecutePostAsync<AssistantModel.FileModel>(
                context.GetAssistantFileUrl(assistantId),
                payload,
                cancellationToken).ConfigureAwait(false);

        return result.Id;
    }

    /// <summary>
    /// Disassociate uploaded file with from assistant, by identifier.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="fileId">The identifier of the uploaded file.</param>
    /// <param name="cancellationToken">A cancellation token</param>
    public static Task RemoveAssistantFileAsync(
        this OpenAIRestContext context,
        string assistantId,
        string fileId,
        CancellationToken cancellationToken = default)
    {
        return context.ExecuteDeleteAsync(context.GetAssistantFileUrl(assistantId, fileId), cancellationToken);
    }

    private static string GetAssistantFileUrl(this OpenAIRestContext context, string assistantId)
    {
        return $"{context.GetAssistantUrl(assistantId)}/files";
    }

    private static string GetAssistantFileUrl(this OpenAIRestContext context, string assistantId, string fileId)
    {
        return $"{context.GetAssistantUrl(assistantId)}/files/{fileId}";
    }
}
