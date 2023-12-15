// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;
using Microsoft.SemanticKernel.Experimental.Agents.Models;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Fluent builder for initializing an <see cref="IAgent"/> instance.
/// </summary>
public partial class AgentBuilder
{
    private readonly AssistantModel _model;
    private readonly KernelPluginCollection _plugins;

    private string? _apiKey;
    private Func<HttpClient>? _httpClientProvider;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentBuilder"/> class.
    /// </summary>
    public AgentBuilder()
    {
        this._model = new AssistantModel();
        this._plugins = new KernelPluginCollection();
    }

    /// <summary>
    /// Create a <see cref="IAgent"/> instance.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A new <see cref="IAgent"/> instance.</returns>
    public async Task<IAgent> BuildAsync(CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(this._model.Model))
        {
            throw new AgentException("Model must be defined for agent.");
        }

        if (string.IsNullOrWhiteSpace(this._apiKey))
        {
            throw new AgentException("ApiKey must be provided for agent.");
        }

        return
            await Agent.CreateAsync(
                new OpenAIRestContext(this._apiKey!, this._httpClientProvider),
                this._model,
                this._plugins,
                cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Define the OpenAI chat completion service (required).
    /// </summary>
    /// <returns><see cref="AgentBuilder"/> instance for fluid expression.</returns>
    public AgentBuilder WithOpenAIChatCompletion(string model, string apiKey)
    {
        this._apiKey = apiKey;
        this._model.Model = model;

        return this;
    }

    /// <summary>
    /// Create a new agent from a yaml formatted string.
    /// </summary>
    /// <param name="template">YAML agent definition.</param>
    /// <returns><see cref="AgentBuilder"/> instance for fluid expression.</returns>
    public AgentBuilder FromTemplate(string template)
    {
        var deserializer = new DeserializerBuilder().Build();

        var agentKernelModel = deserializer.Deserialize<AgentConfigurationModel>(template);

        return
            this
                .WithInstructions(agentKernelModel.Instructions.Trim())
                .WithName(agentKernelModel.Name.Trim())
                .WithDescription(agentKernelModel.Description.Trim());
    }

    /// <summary>
    /// Create a new agent from a yaml template.
    /// </summary>
    /// <param name="templatePath">Path to a configuration file.</param>
    /// <returns><see cref="AgentBuilder"/> instance for fluid expression.</returns>
    public AgentBuilder FromTemplatePath(string templatePath)
    {
        var yamlContent = File.ReadAllText(templatePath);

        return this.FromTemplate(yamlContent);
    }

    /// <summary>
    /// Provide an httpclient (optional).
    /// </summary>
    /// <returns><see cref="AgentBuilder"/> instance for fluid expression.</returns>
    public AgentBuilder WithHttpClient(HttpClient httpClient)
    {
        this._httpClientProvider ??= () => httpClient;

        return this;
    }

    /// <summary>
    /// Define the agent description (optional).
    /// </summary>
    /// <returns><see cref="AgentBuilder"/> instance for fluid expression.</returns>
    public AgentBuilder WithDescription(string? description)
    {
        this._model.Description = description;

        return this;
    }

    /// <summary>
    /// Define the agent instructions (optional).
    /// </summary>
    /// <returns><see cref="AgentBuilder"/> instance for fluid expression.</returns>
    public AgentBuilder WithInstructions(string instructions)
    {
        this._model.Instructions = instructions;

        return this;
    }

    /// <summary>
    /// Define the agent metadata (optional).
    /// </summary>
    /// <returns><see cref="AgentBuilder"/> instance for fluid expression.</returns>
    public AgentBuilder WithMetadata(string key, object value)
    {
        this._model.Metadata[key] = value;

        return this;
    }

    /// <summary>
    /// Define the agent metadata (optional).
    /// </summary>
    /// <returns><see cref="AgentBuilder"/> instance for fluid expression.</returns>
    public AgentBuilder WithMetadata(IDictionary<string, object> metadata)
    {
        foreach (var kvp in metadata)
        {
            this._model.Metadata[kvp.Key] = kvp.Value;
        }

        return this;
    }

    /// <summary>
    /// Define the agent name (optional).
    /// </summary>
    /// <returns><see cref="AgentBuilder"/> instance for fluid expression.</returns>
    public AgentBuilder WithName(string? name)
    {
        this._model.Name = name;

        return this;
    }

    /// <summary>
    /// Define functions associated with agent instance (optional).
    /// </summary>
    /// <returns><see cref="AgentBuilder"/> instance for fluid expression.</returns>
    public AgentBuilder WithPlugin(KernelPlugin? plugin)
    {
        if (plugin != null)
        {
            this._plugins.Add(plugin);
        }

        return this;
    }

    /// <summary>
    /// Define functions associated with agent instance (optional).
    /// </summary>
    /// <returns><see cref="AgentBuilder"/> instance for fluid expression.</returns>
    public AgentBuilder WithPlugins(IEnumerable<KernelPlugin> plugins)
    {
        this._plugins.AddRange(plugins);

        return this;
    }
}
