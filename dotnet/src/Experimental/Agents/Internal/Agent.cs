// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;
using Microsoft.SemanticKernel.Experimental.Agents.Models;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

namespace Microsoft.SemanticKernel.Experimental.Agents.Internal;

/// <summary>
/// Represents an agent that can call the model and use tools.
/// </summary>
internal sealed class Agent : IAgent
{
    public const string ToolCodeInterpreter = "code_interpreter";
    public const string ToolRetrieval = "retrieval";

    /// <inheritdoc/>
    public string Id => this._model.Id;

    /// <inheritdoc/>
    public Kernel Kernel { get; }

    /// <inheritdoc/>
    public KernelPluginCollection Plugins => this.Kernel.Plugins;

    /// <inheritdoc/>
    public AgentCapability Capabilities { get; }

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

    /// <inheritdoc/>
    public IEnumerable<ToolModel> Tools => this._tools;

    /// <inheritdoc/>
    public IEnumerable<string> FileIds => this._fileIds.AsEnumerable();

    private static readonly Regex s_removeInvalidCharsRegex = new("[^0-9A-Za-z-]");
    private static readonly Dictionary<string, IPromptTemplateFactory> s_templateFactories =
        new(StringComparer.OrdinalIgnoreCase)
        {
            { PromptTemplateConfig.SemanticKernelTemplateFormat, new KernelPromptTemplateFactory() },
            { HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat, new HandlebarsPromptTemplateFactory() },
        };

    private readonly OpenAIRestContext _restContext;
    private readonly AssistantModel _model;
    private readonly IPromptTemplate _promptTemplate;
    private readonly ToolModel[] _tools;
    private readonly HashSet<string> _fileIds;

    private AgentPlugin? _agentPlugin;
    private bool _isDeleted;

    /// <summary>
    /// Create a new agent.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantModel">The assistant definition</param>
    /// <param name="config">The template config</param>
    /// <param name="plugins">Plugins to initialize as agent tools</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Agent"> instance.</see></returns>
    public static async Task<IAgent> CreateAsync(
        OpenAIRestContext restContext,
        AssistantModel assistantModel,
        PromptTemplateConfig? config,
        IEnumerable<KernelPlugin>? plugins = null,
        CancellationToken cancellationToken = default)
    {
        var resultModel = await restContext.CreateAssistantModelAsync(assistantModel, cancellationToken).ConfigureAwait(false);

        return new Agent(resultModel, config, restContext, plugins);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Agent"/> class.
    /// </summary>
    internal Agent(
        AssistantModel assistantModel,
        PromptTemplateConfig? config,
        OpenAIRestContext restContext,
        IEnumerable<KernelPlugin>? plugins = null)
    {
        config ??=
            new PromptTemplateConfig
            {
                Name = assistantModel.Name,
                Description = assistantModel.Description,
                Template = assistantModel.Instructions,
            };

        this._model = assistantModel;
        this._restContext = restContext;
        this._promptTemplate = this.DefinePromptTemplate(config);
        this._fileIds = new HashSet<string>(assistantModel.FileIds, StringComparer.OrdinalIgnoreCase);

        IKernelBuilder builder = Kernel.CreateBuilder();

        this.Kernel =
            Kernel
                .CreateBuilder()
                .AddOpenAIChatCompletion(this._model.Model, this._restContext.ApiKey)
                .Build();

        if (plugins is not null)
        {
            this.Kernel.Plugins.AddRange(plugins);
        }

        this.Capabilities =
            (this.Kernel.Plugins.Count > 0 ? AgentCapability.Functions : AgentCapability.None) |
            (this._model.Tools.Any(t => string.Equals(t.Type, ToolRetrieval, StringComparison.OrdinalIgnoreCase)) ? AgentCapability.Retrieval : AgentCapability.None) |
            (this._model.Tools.Any(t => string.Equals(t.Type, ToolCodeInterpreter, StringComparison.OrdinalIgnoreCase)) ? AgentCapability.CodeInterpreter : AgentCapability.None);

        this._tools = this._model.Tools.Concat(this.Kernel.Plugins.SelectMany(p => p.Select(f => f.ToToolModel(p.Name)))).ToArray();
    }

    public AgentPlugin AsPlugin() => this._agentPlugin ??= this.DefinePlugin();

    public IPromptTemplate AsPromptTemplate() => this._promptTemplate;

    /// <inheritdoc/>
    public Task<IAgentThread> NewThreadAsync(CancellationToken cancellationToken = default)
    {
        this.ThrowIfDeleted();

        return ChatThread.CreateAsync(this._restContext, cancellationToken);
    }

    /// <inheritdoc/>
    public Task<IAgentThread> GetThreadAsync(string id, CancellationToken cancellationToken = default)
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
    public async Task AddFileAsync(string fileId, CancellationToken cancellationToken = default)
    {
        if (this._isDeleted)
        {
            return;
        }

        if (this._fileIds.Contains(fileId))
        {
            return;
        }

        await this._restContext.AddAssistantFileAsync(this.Id, fileId, cancellationToken).ConfigureAwait(false);

        this._fileIds.Add(fileId);
    }

    /// <inheritdoc/>
    public async Task RemoveFileAsync(string fileId, CancellationToken cancellationToken = default)
    {
        if (this._isDeleted)
        {
            return;
        }

        if (!this._fileIds.Contains(fileId))
        {
            return;
        }

        await this._restContext.RemoveAssistantFileAsync(this.Id, fileId, cancellationToken).ConfigureAwait(false);

        this._fileIds.Remove(fileId);
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
    /// <param name="arguments">Arguments for parameterized instructions</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>An agent response (<see cref="AgentResponse"/></returns>
    private async Task<AgentResponse> AskAsync(
        [Description("The user message provided to the agent.")]
        string input,
        KernelArguments arguments,
        CancellationToken cancellationToken = default)
    {
        var thread = await this.NewThreadAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            await thread.AddUserMessageAsync(input, cancellationToken).ConfigureAwait(false);

            var messages = await thread.InvokeAsync(this, input, arguments, cancellationToken).ToArrayAsync(cancellationToken).ConfigureAwait(false);
            var response =
                new AgentResponse
                {
                    ThreadId = thread.Id,
                    Message = string.Join(Environment.NewLine, messages.Select(m => m.Content)),
                };

            return response;
        }
        finally
        {
            await thread.DeleteAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    private AgentPluginImpl DefinePlugin()
    {
        var functionAsk = KernelFunctionFactory.CreateFromMethod(this.AskAsync, description: this.Description);

        return new AgentPluginImpl(this, functionAsk);
    }

    private IPromptTemplate DefinePromptTemplate(PromptTemplateConfig config)
    {
        if (!s_templateFactories.TryGetValue(config.TemplateFormat, out var factory))
        {
            factory = new KernelPromptTemplateFactory();
        }

        return factory.Create(config);
    }

    private void ThrowIfDeleted()
    {
        if (this._isDeleted)
        {
            throw new AgentException($"{nameof(Agent)}: {this.Id} has been deleted.");
        }
    }

    private sealed class AgentPluginImpl : AgentPlugin
    {
        public KernelFunction FunctionAsk { get; }

        internal override Agent Agent { get; }

        public override int FunctionCount => 1;

        private static readonly string s_functionName = nameof(Agent.AskAsync).Substring(0, nameof(AgentPluginImpl.Agent.AskAsync).Length - 5);

        public AgentPluginImpl(Agent agent, KernelFunction functionAsk)
            : base(s_removeInvalidCharsRegex.Replace(agent.Name ?? agent.Id, string.Empty),
                   agent.Description ?? agent.Instructions)
        {
            this.Agent = agent;
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
