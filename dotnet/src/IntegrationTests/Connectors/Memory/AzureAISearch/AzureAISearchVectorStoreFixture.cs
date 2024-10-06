<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Azure;
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
using Azure.Identity;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using Azure.Identity;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
using Azure.Identity;
>>>>>>> main
>>>>>>> Stashed changes
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using Azure.Search.Documents.Models;
using Microsoft.Extensions.Configuration;
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using Microsoft.SemanticKernel.Data;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using Microsoft.SemanticKernel.Data;
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
using Microsoft.SemanticKernel.Data;
=======
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;
using SemanticKernel.IntegrationTests.TestSettings;
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
using SemanticKernel.IntegrationTests.TestSettings.Memory;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch;

/// <summary>
/// Helper class for setting up and tearing down Azure AI Search indexes for testing purposes.
/// </summary>
public class AzureAISearchVectorStoreFixture : IAsyncLifetime
{
    /// <summary>
    /// Test index name which consists out of "hotels-" and the machine name with any non-alphanumeric characters removed.
    /// </summary>
#pragma warning disable CA1308 // Normalize strings to uppercase
    private readonly string _testIndexName = "hotels-" + new Regex("[^a-zA-Z0-9]").Replace(Environment.MachineName.ToLowerInvariant(), "");
#pragma warning restore CA1308 // Normalize strings to uppercase

    /// <summary>
    /// Test Configuration setup.
    /// </summary>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    private static readonly IConfigurationRoot s_configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureAISearchVectorStoreFixture>()
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureAISearchVectorStoreRecordCollectionTests>()
        .Build();

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAISearchVectorStoreFixture"/> class.
    /// </summary>
    public AzureAISearchVectorStoreFixture()
    {
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        var config = s_configuration.GetRequiredSection("AzureAISearch").Get<AzureAISearchConfiguration>();
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        var config = s_configuration.GetRequiredSection("AzureAISearch").Get<AzureAISearchConfiguration>();
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
        var config = s_configuration.GetRequiredSection("AzureAISearch").Get<AzureAISearchConfiguration>();
>>>>>>> main
>>>>>>> Stashed changes
        var config = this._configuration.GetRequiredSection("AzureAISearch").Get<AzureAISearchConfiguration>();
        Assert.NotNull(config);
        this.Config = config;
        this.SearchIndexClient = new SearchIndexClient(new Uri(config.ServiceUrl), new AzureKeyCredential(config.ApiKey));
        this.VectorStoreRecordDefinition = new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("HotelId", typeof(string)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsFilterable = true, IsFullTextSearchable = true },
                new VectorStoreRecordDataProperty("Description", typeof(string)),
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 4 },
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 4 },
=======
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 1536 },
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 1536 },
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
                new VectorStoreRecordDataProperty("Tags", typeof(string[])) { IsFilterable = true },
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool?)) { IsFilterable = true, StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("LastRenovationDate", typeof(DateTimeOffset?)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("Rating", typeof(double?))
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            }
        };
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            }
        };
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
            }
        };
=======
>>>>>>> Stashed changes
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 4 },
                new VectorStoreRecordDataProperty("Tags", typeof(string[])) { IsFilterable = true },
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool?)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("LastRenovationDate", typeof(DateTimeOffset?)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("Rating", typeof(float?))
            }
        };
        AzureOpenAIConfiguration? embeddingsConfig = s_configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(embeddingsConfig);
        Assert.NotEmpty(embeddingsConfig.DeploymentName);
        Assert.NotEmpty(embeddingsConfig.Endpoint);
        this.EmbeddingGenerator = new AzureOpenAITextEmbeddingGenerationService(
            deploymentName: embeddingsConfig.DeploymentName,
            endpoint: embeddingsConfig.Endpoint,
            credential: new AzureCliCredential());
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    }

    /// <summary>
    /// Gets the Search Index Client to use for connecting to the Azure AI Search service.
    /// </summary>
    public SearchIndexClient SearchIndexClient { get; private set; }

    /// <summary>
    /// Gets the name of the index that this fixture sets up and tears down.
    /// </summary>
    public string TestIndexName { get => this._testIndexName; }

    /// <summary>
    /// Gets the manually created vector store record definition for our test model.
    /// </summary>
    public VectorStoreRecordDefinition VectorStoreRecordDefinition { get; private set; }

    /// <summary>
    /// Gets the configuration for the Azure AI Search service.
    /// </summary>
    public AzureAISearchConfiguration Config { get; private set; }

    /// <summary>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// Gets the embedding generator to use for generating embeddings for text.
    /// </summary>
    public ITextEmbeddingGenerationService EmbeddingGenerator { get; private set; }

    /// <summary>
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    /// Create / Recreate index and upload documents before test run.
    /// </summary>
    /// <returns>An async task.</returns>
    public async Task InitializeAsync()
    {
        await AzureAISearchVectorStoreFixture.DeleteIndexIfExistsAsync(this._testIndexName, this.SearchIndexClient);
        await AzureAISearchVectorStoreFixture.CreateIndexAsync(this._testIndexName, this.SearchIndexClient);
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        AzureAISearchVectorStoreFixture.UploadDocuments(this.SearchIndexClient.GetSearchClient(this._testIndexName));
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        AzureAISearchVectorStoreFixture.UploadDocuments(this.SearchIndexClient.GetSearchClient(this._testIndexName));
=======
        await AzureAISearchVectorStoreFixture.UploadDocumentsAsync(this.SearchIndexClient.GetSearchClient(this._testIndexName));
        AzureAISearchVectorStoreFixture.UploadDocuments(this.SearchIndexClient.GetSearchClient(this._testIndexName));
        await AzureAISearchVectorStoreFixture.UploadDocumentsAsync(this.SearchIndexClient.GetSearchClient(this._testIndexName), this.EmbeddingGenerator);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        await AzureAISearchVectorStoreFixture.UploadDocumentsAsync(this.SearchIndexClient.GetSearchClient(this._testIndexName));
        AzureAISearchVectorStoreFixture.UploadDocuments(this.SearchIndexClient.GetSearchClient(this._testIndexName));
        await AzureAISearchVectorStoreFixture.UploadDocumentsAsync(this.SearchIndexClient.GetSearchClient(this._testIndexName), this.EmbeddingGenerator);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
    }

    /// <summary>
    /// Delete the index after the test run.
    /// </summary>
    /// <returns>An async task.</returns>
    public async Task DisposeAsync()
    {
        await AzureAISearchVectorStoreFixture.DeleteIndexIfExistsAsync(this._testIndexName, this.SearchIndexClient);
    }

    /// <summary>
    /// Delete the index if it exists.
    /// </summary>
    /// <param name="indexName">The name of the index to delete.</param>
    /// <param name="adminClient">The search index client to use for deleting the index.</param>
    /// <returns>An async task.</returns>
    public static async Task DeleteIndexIfExistsAsync(string indexName, SearchIndexClient adminClient)
    {
        adminClient.GetIndexNames();
        {
            await adminClient.DeleteIndexAsync(indexName);
        }
    }

    /// <summary>
    /// Create an index with the given name.
    /// </summary>
    /// <param name="indexName">The name of the index to create.</param>
    /// <param name="adminClient">The search index client to use for creating the index.</param>
    /// <returns>An async task.</returns>
    public static async Task CreateIndexAsync(string indexName, SearchIndexClient adminClient)
    {
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
        AzureOpenAIConfiguration openAIConfiguration = s_configuration.GetRequiredSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>()!;

        // Build the list of fields from the model, and then replace the DescriptionEmbedding field with a vector field, to work around
        // issue where the field is not recognized as an array on parsing on the server side when apply the VectorSearchFieldAttribute.
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        FieldBuilder fieldBuilder = new();
        var searchFields = fieldBuilder.Build(typeof(Hotel));
        var embeddingfield = searchFields.First(x => x.Name == "DescriptionEmbedding");
        searchFields.Remove(embeddingfield);
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
        searchFields.Add(new VectorSearchField("DescriptionEmbedding", 1536, "my-vector-profile"));

        // Create an index definition with a vectorizer to use when doing vector searches using text.
        var definition = new SearchIndex(indexName, searchFields);
        definition.VectorSearch = new VectorSearch();
        definition.VectorSearch.Vectorizers.Add(new AzureOpenAIVectorizer("text-embedding-vectorizer")
        {
            Parameters = new AzureOpenAIVectorizerParameters
            {
                ResourceUri = new Uri(openAIConfiguration.Endpoint),
                DeploymentName = openAIConfiguration.DeploymentName,
                ApiKey = openAIConfiguration.ApiKey,
                ModelName = openAIConfiguration.EmbeddingModelId
            }
        });
        definition.VectorSearch.Algorithms.Add(new HnswAlgorithmConfiguration("my-hnsw-vector-config-1") { Parameters = new HnswParameters { Metric = VectorSearchAlgorithmMetric.Cosine } });
        definition.VectorSearch.Profiles.Add(new VectorSearchProfile("my-vector-profile", "my-hnsw-vector-config-1") { VectorizerName = "text-embedding-vectorizer" });
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        searchFields.Add(new VectorSearchField("DescriptionEmbedding", 4, "my-vector-profile"));

        var definition = new SearchIndex(indexName, searchFields);
        definition.VectorSearch = new VectorSearch();
        definition.VectorSearch.Algorithms.Add(new HnswAlgorithmConfiguration("my-hnsw-vector-config-1") { Parameters = new HnswParameters { Metric = VectorSearchAlgorithmMetric.Cosine } });
        definition.VectorSearch.Profiles.Add(new VectorSearchProfile("my-vector-profile", "my-hnsw-vector-config-1"));

        var suggester = new SearchSuggester("sg", new[] { "HotelName" });
        definition.Suggesters.Add(suggester);

        await adminClient.CreateOrUpdateIndexAsync(definition);
    }

    /// <summary>
    /// Upload test documents to the index.
    /// </summary>
    /// <param name="searchClient">The client to use for uploading the documents.</param>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    public static async Task UploadDocumentsAsync(SearchClient searchClient)
    /// <param name="embeddingGenerator">An instance of <see cref="ITextEmbeddingGenerationService"/> to generate embeddings.</param>
    public static async Task UploadDocumentsAsync(SearchClient searchClient, ITextEmbeddingGenerationService embeddingGenerator)
    {
        var embedding = await embeddingGenerator.GenerateEmbeddingAsync("This is a great hotel");

<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    public static void UploadDocuments(SearchClient searchClient)
    {
        IndexDocumentsBatch<Hotel> batch = IndexDocumentsBatch.Create(
            IndexDocumentsAction.Upload(
                new Hotel()
                {
                    HotelId = "BaseSet-1",
                    HotelName = "Hotel 1",
                    Description = "This is a great hotel",
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
                    DescriptionEmbedding = embedding,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                    DescriptionEmbedding = embedding,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
                    DescriptionEmbedding = embedding,
>>>>>>> main
>>>>>>> Stashed changes
                    DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
                    Tags = new[] { "pool", "air conditioning", "concierge" },
                    ParkingIncluded = false,
                    LastRenovationDate = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
                    Rating = 3.6
                }),
            IndexDocumentsAction.Upload(
                new Hotel()
                {
                    HotelId = "BaseSet-2",
                    HotelName = "Hotel 2",
                    Description = "This is a great hotel",
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
                    DescriptionEmbedding = embedding,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                    DescriptionEmbedding = embedding,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
                    DescriptionEmbedding = embedding,
>>>>>>> main
>>>>>>> Stashed changes
                    DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
                    Tags = new[] { "pool", "free wifi", "concierge" },
                    ParkingIncluded = false,
                    LastRenovationDate = new DateTimeOffset(1979, 2, 18, 0, 0, 0, TimeSpan.Zero),
                    Rating = 3.60
                }),
            IndexDocumentsAction.Upload(
                new Hotel()
                {
                    HotelId = "BaseSet-3",
                    HotelName = "Hotel 3",
                    Description = "This is a great hotel",
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
                    DescriptionEmbedding = embedding,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                    DescriptionEmbedding = embedding,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
                    DescriptionEmbedding = embedding,
>>>>>>> main
>>>>>>> Stashed changes
                    DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
                    Tags = new[] { "air conditioning", "bar", "continental breakfast" },
                    ParkingIncluded = true,
                    LastRenovationDate = new DateTimeOffset(2015, 9, 20, 0, 0, 0, TimeSpan.Zero),
                    Rating = 4.80
                }),
            IndexDocumentsAction.Upload(
                new Hotel()
                {
                    HotelId = "BaseSet-4",
                    HotelName = "Hotel 4",
                    Description = "This is a great hotel",
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
                    DescriptionEmbedding = embedding,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                    DescriptionEmbedding = embedding,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
                    DescriptionEmbedding = embedding,
>>>>>>> main
>>>>>>> Stashed changes
                    DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
                    Tags = new[] { "concierge", "view", "24-hour front desk service" },
                    ParkingIncluded = true,
                    LastRenovationDate = new DateTimeOffset(1960, 2, 06, 0, 0, 0, TimeSpan.Zero),
                    Rating = 4.60
                })
            );

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
        await searchClient.IndexDocumentsAsync(batch);

        // Add some delay to allow time for the documents to get indexed and show up in search.
        await Task.Delay(5000);
    }

    /// <summary>
    /// Create a test embedding.
    /// </summary>
    /// <returns>The test embedding.</returns>
    public static float[] CreateTestEmbedding()
    {
        return Enumerable.Range(1, 1536).Select(x => (float)x).ToArray();
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        searchClient.IndexDocuments(batch);
    }

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
    public class Hotel
    {
        [SimpleField(IsKey = true, IsFilterable = true)]
        [VectorStoreRecordKey]
        public string HotelId { get; set; }

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        [SearchableField(IsFilterable = true, IsSortable = true)]
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        [SearchableField(IsFilterable = true, IsSortable = true)]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
        [SearchableField(IsFilterable = true, IsSortable = true)]
>>>>>>> main
>>>>>>> Stashed changes
        [SearchableField(IsSortable = true)]
        [VectorStoreRecordData(IsFilterable = true, IsFullTextSearchable = true)]
        public string HotelName { get; set; }

        [SearchableField(AnalyzerName = LexicalAnalyzerName.Values.EnLucene)]
        [VectorStoreRecordData]
        public string Description { get; set; }

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        [VectorStoreRecordVector(1536)]
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        [VectorStoreRecordVector(1536)]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
        [VectorStoreRecordVector(1536)]
>>>>>>> main
>>>>>>> Stashed changes
        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }

        [SearchableField(IsFilterable = true, IsFacetable = true)]
        [VectorStoreRecordData(IsFilterable = true)]
#pragma warning disable CA1819 // Properties should not return arrays
        public string[] Tags { get; set; }
#pragma warning restore CA1819 // Properties should not return arrays

        [JsonPropertyName("parking_is_included")]
        [SimpleField(IsFilterable = true, IsSortable = true, IsFacetable = true)]
        [VectorStoreRecordData(IsFilterable = true)]
        public bool? ParkingIncluded { get; set; }

        [SimpleField(IsFilterable = true, IsSortable = true, IsFacetable = true)]
        [VectorStoreRecordData(IsFilterable = true)]
        public DateTimeOffset? LastRenovationDate { get; set; }

        [SimpleField(IsFilterable = true, IsSortable = true, IsFacetable = true)]
        [VectorStoreRecordData]
        public double? Rating { get; set; }
    }
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
}
