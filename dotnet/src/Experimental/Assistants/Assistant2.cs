// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// $$$
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
    /// $$$
    /// </summary>
    public static async Task<Assistant2> CreateAsync(
        IOpenAIRestContext restContext,
        AssistantModel assistantModel,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await restContext.CreateAssistantAsync(assistantModel, cancellationToken).ConfigureAwait(false) ??
            throw new InvalidOperationException("$$$");

        return new Assistant2(resultModel, restContext);
    }

    /// <summary>
    /// $$$
    /// </summary>
    public static async Task<Assistant2> CreateAsync(
        IOpenAIRestContext restContext,
        string assistantId,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await restContext.GetAssistantAsync(assistantId, cancellationToken).ConfigureAwait(false) ??
            throw new InvalidOperationException("$$$");

        return new Assistant2(resultModel, restContext);
    }

    private Assistant2(AssistantModel model, IOpenAIRestContext restContext)
    {
        this._model = model;
        this._restContext = restContext;
    }
}
