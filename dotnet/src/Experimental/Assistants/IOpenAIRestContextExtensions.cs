// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Internal;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Context for interacting with OpenAI REST API.
/// </summary>
public static class IOpenAIRestContextExtensions
{
    /// <summary>
    /// Create a new thread.
    /// </summary>
    /// <param name="restContext">An context for accessing OpenAI REST endpoint</param>
    /// <returns>An <see cref="AssistantBuilder"> for definition.</see></returns>
    public static IAssistantBuilder CreateAssistant(this IOpenAIRestContext restContext)
    {
        return new AssistantBuilder(restContext);
    }

    /// <summary>
    /// Create a new thread.
    /// </summary>
    /// <param name="restContext">An context for accessing OpenAI REST endpoint</param>
    /// <param name="model">The assistant chat model (required)</param>
    /// <param name="instructions">The assistant instructions (required)</param>
    /// <param name="name">The assistant name (optional)</param>
    /// <param name="description">The assistant description(optional)</param>
    /// <returns>An <see cref="AssistantBuilder"> for definition.</see></returns>
    public static async Task<IAssistant> CreateAssistantAsync(
        this IOpenAIRestContext restContext,
        string model,
        string instructions,
        string? name = null,
        string? description = null)
    {
        return
            await new AssistantBuilder(restContext)
                .WithModel(model)
                .WithInstructions(instructions)
                .WithName(name)
                .WithDescription(description)
                .BuildAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Create a new thread.
    /// </summary>
    /// <param name="restContext">An context for accessing OpenAI REST endpoint</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="IChatThread"> instance.</see></returns>
    public static Task<IChatThread> CreateThreadAsync(this IOpenAIRestContext restContext, CancellationToken cancellationToken = default)
    {
        return ChatThread.CreateAsync(restContext, cancellationToken);
    }

    /// <summary>
    /// Retrieve an existing assisant, by identifier.
    /// </summary>
    /// <param name="restContext">An context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Assistant2"> instance.</see></returns>
    public static Task<IAssistant> GetAssistantAsync(this IOpenAIRestContext restContext, string assistantId, CancellationToken cancellationToken = default)
    {
        return Assistant2.GetAsync(restContext, assistantId, cancellationToken);
    }

    /// <summary>
    /// Retrieve an existing thread.
    /// </summary>
    /// <param name="restContext">An context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="ChatThread"> instance.</see></returns>
    public static Task<IChatThread> GetThreadAsync(this IOpenAIRestContext restContext, string threadId, CancellationToken cancellationToken = default)
    {
        return ChatThread.GetAsync(restContext, threadId, cancellationToken);
    }
}
