// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Exceptions;
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
    public Kernel Kernel { get; }

    /// <inheritdoc/>
    public KernelPluginCollection Plugins => this.Kernel.Plugins;

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

    private readonly OpenAIRestContext _restContext;
    private readonly AssistantModel _model;
    private KernelPlugin? _assistantPlugin;
    private bool _isDeleted;

    /// <summary>
    /// Create a new assistant.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantModel">The assistant definition</param>
    /// <param name="plugins">Plugins to initialize as assistant tools</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Assistant"> instance.</see></returns>
    public static async Task<IAssistant> CreateAsync(
        OpenAIRestContext restContext,
        AssistantModel assistantModel,
        IEnumerable<KernelPlugin>? plugins = null,
        CancellationToken cancellationToken = default)
    {
        var resultModel = await restContext.CreateAssistantModelAsync(assistantModel, cancellationToken).ConfigureAwait(false);

        return new Assistant(resultModel, restContext, plugins);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Assistant"/> class.
    /// </summary>
    internal Assistant(
        AssistantModel model,
        OpenAIRestContext restContext,
        IEnumerable<KernelPlugin>? plugins = null)
    {
        this._model = model;
        this._restContext = restContext;

        KernelBuilder builder = new();
        builder.AddOpenAIChatCompletion(this._model.Model, this._restContext.ApiKey);
        this.Kernel = builder.Build();

        if (plugins is not null)
        {
            this.Kernel.Plugins.AddRange(plugins);
        }
    }

    public KernelPlugin AsPlugin() => this._assistantPlugin ?? this.DefinePlugin();

    /// <inheritdoc/>
    public Task<IChatThread> NewThreadAsync(CancellationToken cancellationToken = default)
    {
        this.ThrowIfDeleted();

        return ChatThread.CreateAsync(this._restContext, cancellationToken);
    }

    /// <inheritdoc/>
    public Task<IChatThread> GetThreadAsync(string id, CancellationToken cancellationToken = default)
    {
        this.ThrowIfDeleted();

        return ChatThread.GetAsync(this._restContext, id, cancellationToken);
    }

    /// <inheritdoc/>
    public async Task DeleteThreadAsync(string? id, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            return;
        }

        await this._restContext.DeleteThreadModelAsync(id!, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteAsync(CancellationToken cancellationToken = default)
    {
        if (this._isDeleted)
        {
            return;
        }

        await this._restContext.DeleteAssistantModelAsync(this.Id, cancellationToken).ConfigureAwait(false);
        this._isDeleted = true;
    }

    /// <summary>
    /// Marshal thread run through <see cref="KernelFunction"/> interface.
    /// </summary>
    /// <param name="input">The user input</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>An assistant response (<see cref="AssistantResponse"/></returns>
    private async Task<AssistantResponse> AskAsync(
        [Description("The user message provided to the assistant.")]
        string input,
        CancellationToken cancellationToken = default)
    {
        var thread = await this.NewThreadAsync(cancellationToken).ConfigureAwait(false);

        await thread.AddUserMessageAsync(input, cancellationToken).ConfigureAwait(false);
        var message = await thread.InvokeAsync(this, cancellationToken).ConfigureAwait(false);
        var response =
            new AssistantResponse
            {
                ThreadId = thread.Id,
                Message = string.Concat(message.Select(m => m.Content)),
            };

        return response;
    }

    private KernelPlugin DefinePlugin()
    {
        var functionAsk = KernelFunctionFactory.CreateFromMethod(this.AskAsync, description: this.Description);
        var assistantPlugin = KernelPluginFactory.CreateFromFunctions(this.Name ?? this.Id, this.Description, new[] { functionAsk });

        return this._assistantPlugin = assistantPlugin;
    }

    private void ThrowIfDeleted()
    {
        if (this._isDeleted)
        {
            throw new AssistantException($"{nameof(Assistant)}: {this.Id} has been deleted.");
        }
    }
}
