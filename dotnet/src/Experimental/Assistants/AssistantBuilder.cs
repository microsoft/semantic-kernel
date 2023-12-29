// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Exceptions;
using Microsoft.SemanticKernel.Experimental.Assistants.Internal;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Fluent builder for initializing an <see cref="IAssistant"/> instance.
/// </summary>
public partial class AssistantBuilder
{
    private readonly AssistantModel _model;
    private readonly KernelPluginCollection _plugins;

    private string? _apiKey;
    private Func<HttpClient>? _httpClientProvider;

    /// <summary>
    /// Initializes a new instance of the <see cref="AssistantBuilder"/> class.
    /// </summary>
    public AssistantBuilder()
    {
        this._model = new AssistantModel();
        this._plugins = new KernelPluginCollection();
    }

    /// <summary>
    /// Create a <see cref="IAssistant"/> instance.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A new <see cref="IAssistant"/> instance.</returns>
    public async Task<IAssistant> BuildAsync(CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(this._model.Model))
        {
            throw new AssistantException("Model must be defined for assistant.");
        }

        if (string.IsNullOrWhiteSpace(this._apiKey))
        {
            throw new AssistantException("ApiKey must be provided for assistant.");
        }

        return
            await Assistant.CreateAsync(
                new OpenAIRestContext(this._apiKey!, this._httpClientProvider),
                this._model,
                this._plugins,
                cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Define the OpenAI chat completion service (required).
    /// </summary>
    /// <returns><see cref="AssistantBuilder"/> instance for fluid expression.</returns>
    public AssistantBuilder WithOpenAIChatCompletion(string model, string apiKey)
    {
        this._apiKey = apiKey;
        this._model.Model = model;

        return this;
    }

    /// <summary>
    /// Create a new assistant from a yaml formatted string.
    /// </summary>
    /// <param name="template">YAML assistant definition.</param>
    /// <returns><see cref="AssistantBuilder"/> instance for fluid expression.</returns>
    public AssistantBuilder FromTemplate(string template)
    {
        var deserializer = new DeserializerBuilder().Build();

        var assistantKernelModel = deserializer.Deserialize<AssistantConfigurationModel>(template);

        return
            this
                .WithInstructions(assistantKernelModel.Instructions.Trim())
                .WithName(assistantKernelModel.Name.Trim())
                .WithDescription(assistantKernelModel.Description.Trim());
    }

    /// <summary>
    /// Create a new assistant from a yaml template.
    /// </summary>
    /// <param name="templatePath">Path to a configuration file.</param>
    /// <returns><see cref="AssistantBuilder"/> instance for fluid expression.</returns>
    public AssistantBuilder FromTemplatePath(string templatePath)
    {
        var yamlContent = File.ReadAllText(templatePath);

        return this.FromTemplate(yamlContent);
    }

    /// <summary>
    /// Provide an httpclient (optional).
    /// </summary>
    /// <returns><see cref="AssistantBuilder"/> instance for fluid expression.</returns>
    public AssistantBuilder WithHttpClient(HttpClient httpClient)
    {
        this._httpClientProvider ??= () => httpClient;

        return this;
    }

    /// <summary>
    /// Define the assistant description (optional).
    /// </summary>
    /// <returns><see cref="AssistantBuilder"/> instance for fluid expression.</returns>
    public AssistantBuilder WithDescription(string? description)
    {
        this._model.Description = description;

        return this;
    }

    /// <summary>
    /// Define the assistant instructions (optional).
    /// </summary>
    /// <returns><see cref="AssistantBuilder"/> instance for fluid expression.</returns>
    public AssistantBuilder WithInstructions(string instructions)
    {
        this._model.Instructions = instructions;

        return this;
    }

    /// <summary>
    /// Define the assistant metadata (optional).
    /// </summary>
    /// <returns><see cref="AssistantBuilder"/> instance for fluid expression.</returns>
    public AssistantBuilder WithMetadata(string key, object value)
    {
        this._model.Metadata[key] = value;

        return this;
    }

    /// <summary>
    /// Define the assistant metadata (optional).
    /// </summary>
    /// <returns><see cref="AssistantBuilder"/> instance for fluid expression.</returns>
    public AssistantBuilder WithMetadata(IDictionary<string, object> metadata)
    {
        foreach (var kvp in metadata)
        {
            this._model.Metadata[kvp.Key] = kvp.Value;
        }

        return this;
    }

    /// <summary>
    /// Define the assistant name (optional).
    /// </summary>
    /// <returns><see cref="AssistantBuilder"/> instance for fluid expression.</returns>
    public AssistantBuilder WithName(string? name)
    {
        this._model.Name = name;

        return this;
    }

    /// <summary>
    /// Define functions associated with assistant instance (optional).
    /// </summary>
    /// <returns><see cref="AssistantBuilder"/> instance for fluid expression.</returns>
    public AssistantBuilder WithPlugin(KernelPlugin? plugin)
    {
        if (plugin != null)
        {
            this._plugins.Add(plugin);
        }

        return this;
    }

    /// <summary>
    /// Define functions associated with assistant instance (optional).
    /// </summary>
    /// <returns><see cref="AssistantBuilder"/> instance for fluid expression.</returns>
    public AssistantBuilder WithPlugins(IEnumerable<KernelPlugin> plugins)
    {
        this._plugins.AddRange(plugins);

        return this;
    }
}
