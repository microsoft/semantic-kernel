// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Internal;

/// <summary>
/// Represents an assistant that can call the model and use tools.
/// </summary>
internal sealed class Assistant : IAssistant
{
    /// <inheritdoc/>
    public string Id => this._model.Id;

    /// <inheritdoc/>
#pragma warning disable CA1720 // Identifier contains type name - We don't control the schema
#pragma warning disable CA1716 // Identifiers should not match keywords
    public string Object => this._model.Object;
#pragma warning restore CA1720 // Identifier contains type name - We don't control the schema
#pragma warning restore CA1716 // Identifiers should not match keywords

    /// <inheritdoc/>
    public long CreatedAt => this._model.CreatedAt;

    /// <inheritdoc/>
    public string? Name => this._model.Name;

    /// <inheritdoc/>
    public string? Description => this._model.Description;

    /// <inheritdoc/>
    public string Model => this._model.Model;

    /// <inheritdoc/>
    public string Instructions => this._model.Instructions;

    private readonly IOpenAIRestContext _restContext;
    private readonly AssistantModel _model;

    /// <summary>
    /// Create a new assistant.
    /// </summary>
    /// <param name="openAiRestContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantModel">The assistant definition</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Assistant"> instance.</see></returns>
    public static async Task<IAssistant> CreateAsync(
        IOpenAIRestContext openAiRestContext,
        AssistantModel assistantModel,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await openAiRestContext.CreateAssistantModelAsync(assistantModel, cancellationToken).ConfigureAwait(false) ??
            throw new SKException("Unexpected failure creating assistant: no result.");

        return new Assistant(resultModel, openAiRestContext);
    }

    /// <summary>
    /// Modify an existing Assistant
    /// </summary>
    /// <param name="openAiRestContext">Context to make calls to OpenAI</param>
    /// <param name="assistantModel">New properties for our instance</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>The modified <see cref="Assistant"> instance.</see></returns>
    public static async Task<IAssistant> ModifyAsync(
        IOpenAIRestContext openAiRestContext,
        AssistantModel assistantModel,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await openAiRestContext.ModifyAssistantModelAsync(assistantModel, cancellationToken).ConfigureAwait(false) ??
            throw new SKException("Unexpected failure modifying assistant: no result.");

        return new Assistant(resultModel, openAiRestContext);
    }

    /// <summary>
    /// Retrieve an existing assistant, by identifier.
    /// </summary>
    /// <param name="openAiRestContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Assistant"> instance.</see></returns>
    public static async Task<IAssistant> GetAsync(
        IOpenAIRestContext openAiRestContext,
        string assistantId,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await openAiRestContext.GetAssistantModelAsync(assistantId, cancellationToken).ConfigureAwait(false) ??
            throw new SKException($"Unexpected failure retrieving assistant: no result. ({assistantId})");

        return new Assistant(resultModel, openAiRestContext);
    }

    /// <summary>
    /// List existing Assistant instances from OpenAI
    /// </summary>
    /// <param name="openAiRestContext">Context to make calls to OpenAI</param>
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
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>List of retrieved Assistants</returns>
    public static async IAsyncEnumerable<IAssistant> ListAsync(
        IOpenAIRestContext openAiRestContext,
        int limit = 20,
        bool ascending = false,
        string? after = null,
        string? before = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (IAssistant assistant in await openAiRestContext
            .GetAssistantsModelsAsync(limit, ascending, after, before, cancellationToken: cancellationToken)
            .ConfigureAwait(false))
        {
            cancellationToken.ThrowIfCancellationRequested();

            yield return assistant;
        }
    }

    /// <summary>
    /// Delete an existing Assistant
    /// </summary>
    /// <param name="openAiRestContext">Context to make calls to OpenAI</param>
    /// <param name="id">Identifier of Assistant to retrieve</param>
    /// <param name="cancellationToken">A cancellation token</param>
    public static async Task DeleteAsync(
        IOpenAIRestContext openAiRestContext,
        string id,
        CancellationToken cancellationToken = default)
    {
        await openAiRestContext.DeleteAssistantsModelAsync(id, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Assistant"/> class.
    /// </summary>
    internal Assistant(AssistantModel model, IOpenAIRestContext restContext)
    {
        this._model = model;
        this._restContext = restContext;
    }
}
