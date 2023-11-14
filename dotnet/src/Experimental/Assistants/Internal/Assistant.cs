// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
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
    public IKernel? Kernel { get; }

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
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantModel">The assistant definition</param>
    /// <param name="kernel">A semantic-kernel instance (for tool/function execution)</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Assistant"> instance.</see></returns>
    public static async Task<IAssistant> CreateAsync(
        IOpenAIRestContext restContext,
        AssistantModel assistantModel,
        IKernel? kernel,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await restContext.CreateAssistantModelAsync(assistantModel, cancellationToken).ConfigureAwait(false) ??
            throw new SKException("Unexpected failure creating assisant: no result.");

        return new Assistant(resultModel, restContext, kernel);
    }

    /// <summary>
    /// Modify an existing Assistant
    /// </summary>
    /// <param name="restContext">Context to make calls to OpenAI</param>
    /// <param name="assistantId">ID of assistant to modify</param>
    /// <param name="model">New model, if not null</param>
    /// <param name="instructions">New instructions, if not null</param>
    /// <param name="name">New name, if not null</param>
    /// <param name="description">New description, if not null</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>The modified <see cref="Assistant"> instance.</see></returns>
    public static async Task<IAssistant> ModifyAsync(
        IOpenAIRestContext restContext,
        string assistantId,
        string? model = null,
        string? instructions = null,
        string? name = null,
        string? description = null,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await restContext.ModifyAssistantModelAsync(assistantId, model, instructions, name, description, cancellationToken).ConfigureAwait(false) ??
            throw new SKException("Unexpected failure modifying assistant: no result.");

        return new Assistant(resultModel, restContext, null); // TODO: find way to preserve kernel
    }

    /// <summary>
    /// Retrieve an existing assistant, by identifier.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="kernel">A semantic-kernel instance (for tool/function execution)</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Assistant"> instance.</see></returns>
    public static async Task<IAssistant> GetAsync(
        IOpenAIRestContext restContext,
        string assistantId,
        IKernel? kernel,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await restContext.GetAssistantModelAsync(assistantId, cancellationToken).ConfigureAwait(false) ??
            throw new SKException($"Unexpected failure retrieving assisant: no result. ({assistantId})");

        return new Assistant(resultModel, restContext, kernel);
    }

    /// <summary>
    /// Delete an existing assistant
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">Identifier of assistant to delete</param>
    /// <param name="cancellationToken">A cancellation token</param>
    public static Task DeleteAsync(
        IOpenAIRestContext restContext,
        string assistantId,
        CancellationToken cancellationToken = default)
    {
        return restContext.DeleteAssistantModelAsync(assistantId, cancellationToken);
    }

    /// <summary>
    /// Retrieve all assistants.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
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
    public static async Task<IList<IAssistant>> ListAsync(
        IOpenAIRestContext restContext,
        int limit = 20,
        bool ascending = false,
        string? after = null,
        string? before = null,
        CancellationToken cancellationToken = default)
    {
        List<AssistantModel> models = new(await restContext.ListAssistantsModelsAsync(limit, ascending, after, before, cancellationToken: cancellationToken).ConfigureAwait(false));

        return models.Select(a => (IAssistant)a).ToList();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Assistant"/> class.
    /// </summary>
    internal Assistant(AssistantModel model, IOpenAIRestContext restContext, IKernel? kernel)
    {
        this._model = model;
        this._restContext = restContext;
        this.Kernel = kernel;
    }
}
