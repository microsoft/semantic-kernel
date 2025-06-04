// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace VectorStoreRAG.Options;

/// <summary>
/// Helper class to load all configuration settings for the VectorStoreRAG project.
/// </summary>
internal sealed class ApplicationConfig
{
    private readonly AzureOpenAIConfig _azureOpenAIConfig;
    private readonly AzureOpenAIEmbeddingsConfig _azureOpenAIEmbeddingsConfig = new();
    private readonly OpenAIConfig _openAIConfig = new();
    private readonly OpenAIEmbeddingsConfig _openAIEmbeddingsConfig = new();
    private readonly RagConfig _ragConfig = new();
    private readonly AzureAISearchConfig _azureAISearchConfig = new();
    private readonly CosmosConfig _cosmosMongoConfig = new();
    private readonly CosmosConfig _cosmosNoSqlConfig = new();
    private readonly QdrantConfig _qdrantConfig = new();
    private readonly RedisConfig _redisConfig = new();
    private readonly WeaviateConfig _weaviateConfig = new();

    public ApplicationConfig(ConfigurationManager configurationManager)
    {
        this._azureOpenAIConfig = new();
        configurationManager
            .GetRequiredSection($"AIServices:{AzureOpenAIConfig.ConfigSectionName}")
            .Bind(this._azureOpenAIConfig);
        configurationManager
            .GetRequiredSection($"AIServices:{AzureOpenAIEmbeddingsConfig.ConfigSectionName}")
            .Bind(this._azureOpenAIEmbeddingsConfig);
        configurationManager
            .GetRequiredSection($"AIServices:{OpenAIConfig.ConfigSectionName}")
            .Bind(this._openAIConfig);
        configurationManager
            .GetRequiredSection($"AIServices:{OpenAIEmbeddingsConfig.ConfigSectionName}")
            .Bind(this._openAIEmbeddingsConfig);
        configurationManager
            .GetRequiredSection(RagConfig.ConfigSectionName)
            .Bind(this._ragConfig);
        configurationManager
            .GetRequiredSection($"VectorStores:{AzureAISearchConfig.ConfigSectionName}")
            .Bind(this._azureAISearchConfig);
        configurationManager
            .GetRequiredSection($"VectorStores:{CosmosConfig.MongoConfigSectionName}")
            .Bind(this._cosmosMongoConfig);
        configurationManager
            .GetRequiredSection($"VectorStores:{CosmosConfig.NoSqlConfigSectionName}")
            .Bind(this._cosmosNoSqlConfig);
        configurationManager
            .GetRequiredSection($"VectorStores:{QdrantConfig.ConfigSectionName}")
            .Bind(this._qdrantConfig);
        configurationManager
            .GetRequiredSection($"VectorStores:{RedisConfig.ConfigSectionName}")
            .Bind(this._redisConfig);
        configurationManager
            .GetRequiredSection($"VectorStores:{WeaviateConfig.ConfigSectionName}")
            .Bind(this._weaviateConfig);
    }

    public AzureOpenAIConfig AzureOpenAIConfig => this._azureOpenAIConfig;

    public AzureOpenAIEmbeddingsConfig AzureOpenAIEmbeddingsConfig => this._azureOpenAIEmbeddingsConfig;

    public OpenAIConfig OpenAIConfig => this._openAIConfig;

    public OpenAIEmbeddingsConfig OpenAIEmbeddingsConfig => this._openAIEmbeddingsConfig;

    public RagConfig RagConfig => this._ragConfig;

    public AzureAISearchConfig AzureAISearchConfig => this._azureAISearchConfig;

    public CosmosConfig CosmosMongoConfig => this._cosmosMongoConfig;

    public CosmosConfig CosmosNoSqlConfig => this._cosmosNoSqlConfig;

    public QdrantConfig QdrantConfig => this._qdrantConfig;

    public RedisConfig RedisConfig => this._redisConfig;

    public WeaviateConfig WeaviateConfig => this._weaviateConfig;
}
