// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Represents an assistant that can call the model and use tools.
/// </summary>
public sealed class Assistant2 : IAssistant
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
    public string Name => this._model.Name;

    /// <inheritdoc/>
    public string Description => this._model.Description;

    /// <inheritdoc/>
    public string Model => this._model.Model;

    /// <inheritdoc/>
    public string Instructions => this._model.Instructions;

    private readonly IOpenAIRestContext _restContext;
    private readonly AssistantModel _model;

    /// <summary>
    /// Create a new assistant.
    /// </summary>
    /// <param name="restContext">An context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantModel">The assistant definition</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Assistant2"> instance.</see></returns>
    public static async Task<Assistant2> CreateAsync(
        IOpenAIRestContext restContext,
        AssistantModel assistantModel,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await restContext.CreateAssistantAsync(assistantModel, cancellationToken).ConfigureAwait(false) ??
            throw new SKException("Unexpected failure creating assisant: no result.");

        return new Assistant2(resultModel, restContext);
    }

    /// <summary>
    /// Retrieve an existing assisant, by identifier.
    /// </summary>
    /// <param name="restContext">An context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId"></param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Assistant2"> instance.</see></returns>
    public static async Task<Assistant2> GetAsync(
        IOpenAIRestContext restContext,
        string assistantId,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await restContext.GetAssistantAsync(assistantId, cancellationToken).ConfigureAwait(false) ??
            throw new SKException("Unexpected failure retrieving assisant: no result.");

        return new Assistant2(resultModel, restContext);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Assistant2"/> class.
    /// </summary>
    private Assistant2(AssistantModel model, IOpenAIRestContext restContext)
    {
        this._model = model;
        this._restContext = restContext;
    }
}
