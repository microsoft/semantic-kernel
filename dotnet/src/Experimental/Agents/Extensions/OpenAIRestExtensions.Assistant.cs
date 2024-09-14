// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Globalization;
using System.Threading;
using System.Threading.Tasks;
using System.Web;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Supported OpenAI REST API actions for assistants.
/// </summary>
internal static partial class OpenAIRestExtensions
{
    /// <summary>
    /// Create a new assistant.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="model">The assistant definition</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An assistant definition</returns>
    public static Task<AssistantModel> CreateAssistantModelAsync(
        this OpenAIRestContext context,
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
                context.GetAssistantsUrl(),
                payload,
                cancellationToken);
    }

    /// <summary>
    /// Retrieve an assistant by identifier.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An assistant definition</returns>
    public static Task<AssistantModel> GetAssistantModelAsync(
        this OpenAIRestContext context,
        string assistantId,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecuteGetAsync<AssistantModel>(
                context.GetAssistantUrl(assistantId),
                cancellationToken);
    }

    /// <summary>
    /// Retrieve all assistants.
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="limit">A limit on the number of objects to be returned.
    /// Limit can range between 1 and 100, and the default is 20.</param>
    /// <param name="ascending">Set to true to sort by ascending created_at timestamp
    /// instead of descending.</param>
    /// <param name="after">A cursor for use in pagination. This is an object ID that defines
    /// your place in the list. For instance, if you make a list request and receive 100 objects,
    /// ending with obj_foo, your subsequent call can include after=obj_foo in order to
    /// fetch the next page of the list.</param>
    /// <param name="before">A cursor for use in pagination. This is an object ID that defines
    /// your place in the list. For instance, if you make a list request and receive 100 objects,
    /// ending with obj_foo, your subsequent call can include before=obj_foo in order to
    /// fetch the previous page of the list.</param>
    /// <returns>List of retrieved Assistants</returns>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An enumeration of assistant definitions</returns>
    public static async Task<IList<AssistantModel>> ListAssistantModelsAsync(
        this OpenAIRestContext context,
        int limit = 20,
        bool ascending = false,
        string? after = null,
        string? before = null,
        CancellationToken cancellationToken = default)
    {
        var query = HttpUtility.ParseQueryString(string.Empty);
        query["limit"] = limit.ToString(CultureInfo.InvariantCulture);
        query["order"] = ascending ? "asc" : "desc";
        if (!string.IsNullOrWhiteSpace(after))
        {
            query["after"] = after;
        }
        if (!string.IsNullOrWhiteSpace(before))
        {
            query["before"] = before;
        }

        var result =
            await context.ExecuteGetAsync<AssistantListModel>(
                context.GetAssistantsUrl(),
                query.ToString(),
                cancellationToken).ConfigureAwait(false);

        return result.Data;
    }

    /// <summary>
    /// Delete an existing assistant
    /// </summary>
    /// <param name="context">A context for accessing OpenAI REST endpoint</param>
    /// <param name="id">Identifier of assistant to delete</param>
    /// <param name="cancellationToken">A cancellation token</param>
    public static Task DeleteAssistantModelAsync(
        this OpenAIRestContext context,
        string id,
        CancellationToken cancellationToken = default)
    {
        return context.ExecuteDeleteAsync(context.GetAssistantUrl(id), cancellationToken);
    }

    internal static string GetAssistantsUrl(this OpenAIRestContext context) => $"{context.Endpoint}/assistants";

    internal static string GetAssistantUrl(this OpenAIRestContext context, string assistantId) => $"{context.Endpoint}/assistants/{assistantId}";
}
