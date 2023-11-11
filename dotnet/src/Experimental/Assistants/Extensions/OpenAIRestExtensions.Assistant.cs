// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static partial class OpenAIRestExtensions
{
    private const string BaseAssistantUrl = $"{BaseUrl}/assistants";

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="context"></param>
    /// <param name="model"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<AssistantModel?> CreateAssistantAsync(
        this IOpenAIRestContext context,
        AssistantModel model,
        CancellationToken cancellationToken = default)
    {
        return
            context.ExecutePostAsync<AssistantModel>(
                BaseAssistantUrl,
                model,
                cancellationToken);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="context"></param>
    /// <param name="assistantId"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<AssistantModel?> GetAssistantAsync(
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
    /// $$$
    /// </summary>
    /// <param name="context"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<IList<AssistantModel>?> GetAssistantsAsync(
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
