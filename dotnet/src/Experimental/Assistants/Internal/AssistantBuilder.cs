// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Internal;

/// <summary>
/// Fluent builder for initializing an <see cref="IAssistant"/> instance.
/// </summary>
internal sealed class AssistantBuilder : IAssistantBuilder
{
    private readonly IOpenAIRestContext _context;
    private readonly AssistantModel _model;

    /// <summary>
    /// Initializes a new instance of the <see cref="AssistantBuilder"/> class.
    /// </summary>
    public AssistantBuilder(IOpenAIRestContext restContext)
    {
        this._context = restContext;
        this._model = new AssistantModel();
    }

    /// <inheritdoc/>
    public async Task<IAssistant> BuildAsync(CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(this._model.Model))
        {
            throw new SKException("Model must be defined for assistant.");
        }

        if (string.IsNullOrWhiteSpace(this._model.Instructions))
        {
            throw new SKException("Instructions must be defined for assistant.");
        }

        return await Assistant.CreateAsync(this._context, this._model, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithDescription(string? description)
    {
        this._model.Description = description;

        return this;
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithInstructions(string instructions)
    {
        this._model.Instructions = instructions;

        return this;
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithModel(string model)
    {
        this._model.Model = model;

        return this;
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithName(string? name)
    {
        this._model.Name = name;

        return this;
    }
}
