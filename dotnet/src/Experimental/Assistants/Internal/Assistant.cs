// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using Microsoft.SemanticKernel.Http;

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
    private readonly IKernel _kernel;

    /// <summary>
    /// Create a new assistant.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantModel">The assistant definition</param>
    /// <param name="functions">$$$</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Assistant"> instance.</see></returns>
    public static async Task<IAssistant> CreateAsync(
        IOpenAIRestContext restContext,
        AssistantModel assistantModel,
        IEnumerable<ISKFunction>? functions = null,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await restContext.CreateAssistantModelAsync(assistantModel, cancellationToken).ConfigureAwait(false) ??
            throw new SKException("Unexpected failure creating assistant: no result.");

        return new Assistant(resultModel, restContext, functions);
    }

    /// <summary>
    /// Modify an existing Assistant
    /// </summary>
    /// <param name="openAiRestContext">Context to make calls to OpenAI</param>
    /// <param name="assistantModel">New properties for our instance</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>The modified <see cref="Assistant"> instance.</see></returns>
    public static async Task<IAssistant> ModifyAsync( // TODO: @gil - NEEDED ???
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
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="functions">$$$</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Assistant"> instance.</see></returns>
    public static async Task<IAssistant> GetAsync(
        IOpenAIRestContext restContext,
        string assistantId,
        IEnumerable<ISKFunction>? functions = null,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await restContext.GetAssistantModelAsync(assistantId, cancellationToken).ConfigureAwait(false) ??
            throw new SKException($"Unexpected failure retrieving assistant: no result. ({assistantId})");

        return new Assistant(resultModel, restContext, functions);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Assistant"/> class.
    /// </summary>
    internal Assistant(
        AssistantModel model,
        IOpenAIRestContext restContext,
        IEnumerable<ISKFunction>? functions = null)
    {
        this._model = model;
        this._restContext = restContext;

        var functionCollection = new FunctionCollection();
        foreach (var function in functions ?? Array.Empty<ISKFunction>())
        {
            this.DefineTool(function);
            functionCollection.AddFunction(function);
        }

        this._kernel =
            new Kernel(
                functionCollection,
                aiServiceProvider: null!,
                memory: null!,
                NullHttpHandlerFactory.Instance,
                loggerFactory: null);
    }

    private void DefineTool(ISKFunction tool)
    {
        var view = tool.Describe();
        var required = new List<string>(view.Parameters.Count);
        var parameters =
            view.Parameters.ToDictionary(
                p => p.Name,
                p =>
                {
                    if (p.IsRequired ?? false)
                    {
                        required.Add(p.Name);
                    }

                    return
                        new OpenAIParameter
                        {
                            Type = p.Type?.Name ?? nameof(System.String),
                            Description = p.Description,
                        };
                });

        var payload =
            new AssistantModel.ToolModel
            {
                Type = "function",
                Function =
                    new()
                    {
                        Name = tool.GetQualifiedName(),
                        Description = tool.Description,
                        Parameters =
                        {
                            Properties = parameters,
                            Required = required,
                        }
                    },
            };

        this._model.Tools.Add(payload);
    }
}
