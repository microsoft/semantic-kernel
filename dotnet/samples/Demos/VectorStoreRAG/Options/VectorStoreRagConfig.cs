// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace VectorStoreRAG.Options;

internal class VectorStoreRagConfig
{
    private readonly AzureOpenAIConfig _azureOpenAIConfig;
    private readonly AzureOpenAIEmbeddingsConfig _azureOpenAIEmbeddingsConfig = new();
    private readonly RagConfig _ragConfig = new();
    private readonly QdrantConfig _qdrantConfig = new();
    private readonly AzureAISearchConfig _azureAISearchConfig = new();

    public VectorStoreRagConfig(ConfigurationManager configurationManager)
    {
        this._azureOpenAIConfig = new();
        configurationManager
            .GetRequiredSection($"AIServices:{AzureOpenAIConfig.ConfigSectionName}")
            .Bind(this._azureOpenAIConfig);
        configurationManager
            .GetRequiredSection($"AIServices:{AzureOpenAIEmbeddingsConfig.ConfigSectionName}")
            .Bind(this._azureOpenAIEmbeddingsConfig);
        configurationManager
            .GetRequiredSection(RagConfig.ConfigSectionName)
            .Bind(this._ragConfig);
        configurationManager
            .GetRequiredSection($"VectorStores:{QdrantConfig.ConfigSectionName}")
            .Bind(this._qdrantConfig);
        configurationManager
            .GetRequiredSection($"VectorStores:{AzureAISearchConfig.ConfigSectionName}")
            .Bind(this._azureAISearchConfig);
    }

    public AzureOpenAIConfig AzureOpenAIConfig => this._azureOpenAIConfig;

    public AzureOpenAIEmbeddingsConfig AzureOpenAIEmbeddingsConfig => this._azureOpenAIEmbeddingsConfig;

    public RagConfig RagConfig => this._ragConfig;

    public QdrantConfig QdrantConfig => this._qdrantConfig;

    public AzureAISearchConfig AzureAISearchConfig => this._azureAISearchConfig;
}
