// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.RegularExpressions;
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

    private static readonly Regex s_removeInvalidCharsRegex = new("[^0-9A-Za-z-]");

    private readonly OpenAIRestContext _restContext;
    private readonly AssistantModel _model;

    private AssistantPlugin? _assistantPlugin;
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

        IKernelBuilder builder = Kernel.CreateBuilder();
        ;
        this.Kernel =
            Kernel
                .CreateBuilder()
                .AddOpenAIChatCompletion(this._model.Model, this._restContext.ApiKey)
                .Build();

        if (plugins is not null)
        {
            this.Kernel.Plugins.AddRange(plugins);
        }
    }

    public AssistantPlugin AsPlugin() => this._assistantPlugin ??= this.DefinePlugin();

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
        try
        {
            await thread.AddUserMessageAsync(input, cancellationToken).ConfigureAwait(false);

            var messages = await thread.InvokeAsync(this, cancellationToken).ToArrayAsync(cancellationToken).ConfigureAwait(false);
            var response =
                new AssistantResponse
                {
                    ThreadId = thread.Id,
                    Message = string.Concat(messages.Select(m => m.Content)),
                };

            return response;
        }
        finally
        {
            await thread.DeleteAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    private AssistantPluginImpl DefinePlugin()
    {
        var functionAsk = KernelFunctionFactory.CreateFromMethod(this.AskAsync, description: this.Description);

        return new AssistantPluginImpl(this, functionAsk);
    }

    private void ThrowIfDeleted()
    {
        if (this._isDeleted)
        {
            throw new AssistantException($"{nameof(Assistant)}: {this.Id} has been deleted.");
        }
    }

    private sealed class AssistantPluginImpl : AssistantPlugin
    {
        public KernelFunction FunctionAsk { get; }

        internal override Assistant Assistant { get; }

        public override int FunctionCount => 1;

        private static readonly string s_functionName = nameof(Assistant.AskAsync).Substring(0, nameof(Assistant.AskAsync).Length - 5);

        public AssistantPluginImpl(Assistant assistant, KernelFunction functionAsk)
            : base(s_removeInvalidCharsRegex.Replace(assistant.Name ?? assistant.Id, string.Empty),
                   assistant.Description ?? assistant.Instructions)
        {
            this.Assistant = assistant;
            this.FunctionAsk = functionAsk;
        }

        public override IEnumerator<KernelFunction> GetEnumerator()
        {
            yield return this.FunctionAsk;
        }

        public override bool TryGetFunction(string name, [NotNullWhen(true)] out KernelFunction? function)
        {
            function = null;

            if (s_functionName.Equals(name, StringComparison.OrdinalIgnoreCase))
            {
                function = this.FunctionAsk;
            }

            return function != null;
        }
    }
}
