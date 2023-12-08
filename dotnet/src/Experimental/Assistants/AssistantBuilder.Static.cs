// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Internal;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Context for interacting with OpenAI REST API.
/// </summary>
public partial class AssistantBuilder
{
    /// <summary>
    /// Create a new assistant.
    /// </summary>
    /// <param name="apiKey">The OpenAI API key</param>
    /// <param name="model">The assistant chat model (required)</param>
    /// <param name="instructions">The assistant instructions (required)</param>
    /// <param name="name">The assistant name (optional)</param>
    /// <param name="description">The assistant description(optional)</param>
    /// <returns>The requested <see cref="IAssistant">.</see></returns>
    public static async Task<IAssistant> NewAsync(
        string apiKey,
        string model,
        string instructions,
        string? name = null,
        string? description = null)
    {
        return
            await new AssistantBuilder()
                .WithOpenAIChatCompletion(model, apiKey)
                .WithInstructions(instructions)
                .WithName(name)
                .WithDescription(description)
                .BuildAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Retrieve an existing assistant, by identifier.
    /// </summary>
    /// <param name="apiKey">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="plugins">Plugins to initialize as assistant tools</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Assistant"> instance.</see></returns>
    public static async Task<IAssistant> GetAssistantAsync(
        string apiKey,
        string assistantId,
        IEnumerable<KernelPlugin>? plugins = null,
        CancellationToken cancellationToken = default)
    {
        var restContext = new OpenAIRestContext(apiKey);
        var resultModel = await restContext.GetAssistantModelAsync(assistantId, cancellationToken).ConfigureAwait(false);

        return new Assistant(resultModel, restContext, plugins);
    }
}
