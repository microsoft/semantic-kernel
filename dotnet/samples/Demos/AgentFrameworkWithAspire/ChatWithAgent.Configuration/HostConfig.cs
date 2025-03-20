// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using Microsoft.Extensions.Configuration;

namespace ChatWithAgent.Configuration;

/// <summary>
/// Helper class for loading host configuration settings.
/// </summary>
public sealed class HostConfig
{
    /// <summary>
    /// The AI services section name.
    /// </summary>
    public const string AIServicesSectionName = "AIServices";

    /// <summary>
    /// The Vector stores section name.
    /// </summary>
    public const string VectorStoresSectionName = "VectorStores";

    /// <summary>
    /// The name of the connection string of Azure OpenAI service.
    /// </summary>
    public const string AzureOpenAIConnectionStringName = "AzureOpenAI";

    /// <summary>
    /// The name of the connection string of OpenAI service.
    /// </summary>
    public const string OpenAIConnectionStringName = "OpenAI";

    private readonly ConfigurationManager _configurationManager;

    private readonly AzureOpenAIChatConfig _azureOpenAIChatConfig = new();

    private readonly AzureOpenAIEmbeddingsConfig _azureOpenAIEmbeddingsConfig = new();

    private readonly OpenAIChatConfig _openAIChatConfig = new();

    private readonly OpenAIEmbeddingsConfig _openAIEmbeddingsConfig = new();

    private readonly AzureAISearchConfig _azureAISearchConfig = new();

    private readonly RagConfig _ragConfig = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="HostConfig"/> class.
    /// </summary>
    /// <param name="configurationManager">The configuration manager.</param>
    public HostConfig(ConfigurationManager configurationManager)
    {
        configurationManager
            .GetSection($"{AIServicesSectionName}:{AzureOpenAIChatConfig.ConfigSectionName}")
            .Bind(this._azureOpenAIChatConfig);
        configurationManager
            .GetSection($"{AIServicesSectionName}:{AzureOpenAIEmbeddingsConfig.ConfigSectionName}")
            .Bind(this._azureOpenAIEmbeddingsConfig);
        configurationManager
            .GetSection($"{AIServicesSectionName}:{OpenAIChatConfig.ConfigSectionName}")
            .Bind(this._openAIChatConfig);
        configurationManager
            .GetSection($"{AIServicesSectionName}:{OpenAIEmbeddingsConfig.ConfigSectionName}")
            .Bind(this._openAIEmbeddingsConfig);
        configurationManager
            .GetSection($"{VectorStoresSectionName}:{AzureAISearchConfig.ConfigSectionName}")
            .Bind(this._azureAISearchConfig);
        configurationManager
            .GetSection($"{AIServicesSectionName}:{RagConfig.ConfigSectionName}")
            .Bind(this._ragConfig);
        configurationManager
            .Bind(this);

        this._configurationManager = configurationManager;
    }

    /// <summary>
    /// The AI chat service to use.
    /// </summary>
    [Required]
    public string AIChatService { get; set; } = string.Empty;

    /// <summary>
    /// The Azure OpenAI chat service configuration.
    /// </summary>
    public AzureOpenAIChatConfig AzureOpenAIChat => this._azureOpenAIChatConfig;

    /// <summary>
    /// The Azure OpenAI embeddings service configuration.
    /// </summary>
    public AzureOpenAIEmbeddingsConfig AzureOpenAIEmbeddings => this._azureOpenAIEmbeddingsConfig;

    /// <summary>
    /// The OpenAI chat service configuration.
    /// </summary>
    public OpenAIChatConfig OpenAIChat => this._openAIChatConfig;

    /// <summary>
    /// The OpenAI embeddings service configuration.
    /// </summary>
    public OpenAIEmbeddingsConfig OpenAIEmbeddings => this._openAIEmbeddingsConfig;

    /// <summary>
    /// The Azure AI search configuration.
    /// </summary>
    public AzureAISearchConfig AzureAISearch => this._azureAISearchConfig;

    /// <summary>
    /// The RAG configuration.
    /// </summary>
    public RagConfig Rag => this._ragConfig;
}
