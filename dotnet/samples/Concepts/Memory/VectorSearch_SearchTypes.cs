// Copyright (c) Microsoft. All rights reserved.

using Azure;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;

namespace Memory;

public class VectorSearch_SearchTypes(ITestOutputHelper output) : BaseTest(output)
{
    private static readonly IConfigurationRoot s_configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<VectorSearch_SearchTypes>()
        .Build();

    private static readonly string? s_azureAISearchServiceUrl = s_configuration.GetRequiredSection("AzureAISearch").GetValue<string>("ServiceUrl");
    private static readonly string? s_apiKey = s_configuration.GetRequiredSection("AzureAISearch").GetValue<string>("ApiKey");
    private const string IndexName = "skconceptssearchtypes";

    [Fact]
    public async Task DIExampleAsync()
    {
        // Create a kernel with the required services.
        var kernelBuilder = Kernel.CreateBuilder()
            .AddAzureOpenAITextEmbeddingGeneration(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                TestConfiguration.AzureOpenAIEmbeddings.ApiKey)
            .AddAzureAISearchVectorStore(new Uri(s_azureAISearchServiceUrl!), new AzureKeyCredential(s_apiKey!));

        kernelBuilder.Services.AddSingleton<RecordProcessor>();
        kernelBuilder.Services.AddSingleton<ITestOutputHelper>(this.Output);
        kernelBuilder.Services.AddSingleton<IVectorStoreRecordCollection<string, Glossary>>((sp) =>
        {
            var vectorStore = sp.GetRequiredService<IVectorStore>();
            return vectorStore.GetCollection<string, Glossary>(IndexName);
        });
        kernelBuilder.Services.AddSingleton<IVectorizableTextSearch<Glossary>>((sp) =>
        {
            var vectorStore = sp.GetRequiredService<IVectorStore>();
            return (IVectorizableTextSearch<Glossary>)sp.GetRequiredService<IVectorStoreRecordCollection<string, Glossary>>();
        });

        var kernel = kernelBuilder.Build();

        var recordProcessor = kernel.GetRequiredService<RecordProcessor>();

        await CreateIndexAsync();
        await recordProcessor.ExecuteProcessAsync();
    }

    [Fact]
    public async Task ExampleAsync()
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                TestConfiguration.AzureOpenAIEmbeddings.ApiKey);

        // Construct the vector store.
        var vectorStore = new AzureAISearchVectorStore(new SearchIndexClient(new Uri(s_azureAISearchServiceUrl!), new AzureKeyCredential(s_apiKey!)));
        var collection = vectorStore.GetCollection<string, Glossary>(IndexName);
        var recordProcessor = new RecordProcessor(
            this.Output,
            collection,
            (IVectorizableTextSearch<Glossary>)collection,
            textEmbeddingGenerationService);

        await CreateIndexAsync();
        await recordProcessor.ExecuteProcessAsync();
    }

    private sealed class RecordProcessor(
        ITestOutputHelper Console,
        IVectorStoreRecordCollection<string, Glossary> collection,
        IVectorizableTextSearch<Glossary> vectorizableTextSearch,
        ITextEmbeddingGenerationService textEmbeddingGenerationService)
    {
        public async Task ExecuteProcessAsync()
        {
            // Create glossary entries and generate embeddings for them.
            var glossaryEntries = CreateGlossaryEntries().ToList();
            var tasks = glossaryEntries.Select(entry => Task.Run(async () =>
            {
                entry.DefinitionEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(entry.Definition);
            }));
            await Task.WhenAll(tasks);

            // Upsert the glossary entries into the collection and return their keys.
            var upsertedKeysTasks = glossaryEntries.Select(x => collection.UpsertAsync(x));
            var upsertedKeys = await Task.WhenAll(upsertedKeysTasks);
            await Task.Delay(1000);

            // Search the collection using a vector search.
            var searchString = "What is an Application Programming Interface";
            var searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);
            var searchResult = await collection.VectorizedSearchAsync(searchVector, new() { Limit = 1 }).ToListAsync();

            Console.WriteLine("Vector Search 1");
            Console.WriteLine("Search string: " + searchString);
            Console.WriteLine("Result: " + searchResult.First().Record.Definition);
            Console.WriteLine();

            // Search the collection using a vector search.
            searchString = "What is Retrieval Augmented Generation";
            searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);
            searchResult = await collection.VectorizedSearchAsync(searchVector, new() { Limit = 1 }).ToListAsync();

            Console.WriteLine("Vector Search 2");
            Console.WriteLine("Search string: " + searchString);
            Console.WriteLine("Result: " + searchResult.First().Record.Definition);
            Console.WriteLine();

            // Search the collection using a vector search with pre-filtering.
            searchString = "What is Retrieval Augmented Generation";
            searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);
            var filter = new VectorSearchFilter().EqualTo(nameof(Glossary.Category), "External Definitions");
            searchResult = await collection.VectorizedSearchAsync(searchVector, new() { Limit = 3, Filter = filter }).ToListAsync();

            Console.WriteLine("Vector Search with pre-filtering");
            Console.WriteLine("Search string: " + searchString);
            Console.WriteLine("Number of results: " + searchResult.Count);
            Console.WriteLine("Result 1 Score: " + searchResult[0].Score);
            Console.WriteLine("Result 1: " + searchResult[0].Record.Definition);
            Console.WriteLine("Result 2 Score: " + searchResult[1].Score);
            Console.WriteLine("Result 2: " + searchResult[1].Record.Definition);
            Console.WriteLine();

            // Search the collection using a vectorizable search with pre-filtering.
            searchResult = await vectorizableTextSearch.VectorizableTextSearchAsync(searchString, new() { Limit = 3, Filter = filter }).ToListAsync();

            Console.WriteLine("Vectorizable text search with pre-filtering");
            Console.WriteLine("Search string: " + searchString);
            Console.WriteLine("Number of results: " + searchResult.Count);
            Console.WriteLine("Result 1 Score: " + searchResult[0].Score);
            Console.WriteLine("Result 1: " + searchResult[0].Record.Definition);
            Console.WriteLine("Result 2 Score: " + searchResult[1].Score);
            Console.WriteLine("Result 2: " + searchResult[1].Record.Definition);

            await collection.DeleteCollectionAsync();
        }
    }

    /// <summary>
    /// Sample model class that represents a glossary entry.
    /// </summary>
    /// <remarks>
    /// Note that each property is decorated with an attribute that specifies how the property should be treated by the vector store.
    /// This allows us to create a collection in the vector store and upsert and retrieve instances of this class without any further configuration.
    /// </remarks>
    private sealed class Glossary
    {
        [VectorStoreRecordKey]
        public string Key { get; set; }

        [VectorStoreRecordData(IsFilterable = true)]
        public string Category { get; set; }

        [VectorStoreRecordData]
        public string Term { get; set; }

        [VectorStoreRecordData]
        public string Definition { get; set; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> DefinitionEmbedding { get; set; }
    }

    /// <summary>
    /// Create some sample glossary entries.
    /// </summary>
    /// <returns>A list of sample glossary entries.</returns>
    private static IEnumerable<Glossary> CreateGlossaryEntries()
    {
        yield return new Glossary
        {
            Key = "1",
            Category = "External Definitions",
            Term = "API",
            Definition = "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data."
        };

        yield return new Glossary
        {
            Key = "2",
            Category = "Core Definitions",
            Term = "Connectors",
            Definition = "Connectors allow you to integrate with various services provide AI capabilities, including LLM, AudioToText, TextToAudio, Embedding generation, etc."
        };

        yield return new Glossary
        {
            Key = "3",
            Category = "External Definitions",
            Term = "RAG",
            Definition = "Retrieval Augmented Generation - a term that refers to the process of retrieving additional data to provide as context to an LLM to use when generating a response (completion) to a user’s question (prompt)."
        };
    }

    private static async Task CreateIndexAsync()
    {
        var indexName = VectorSearch_SearchTypes.IndexName;
        var searchIndexClient = new SearchIndexClient(new Uri(s_azureAISearchServiceUrl!), new AzureKeyCredential(s_apiKey!));

        // Build the list of fields from the model, and then replace the DescriptionEmbedding field with a vector field, to work around
        // issue where the field is not recognized as an array on parsing on the server side when apply the VectorSearchFieldAttribute.
        var searchFields = new List<SearchField>();
        searchFields.Add(new SimpleField("Key", SearchFieldDataType.String) { IsFilterable = true, IsKey = true });
        searchFields.Add(new SimpleField("Category", SearchFieldDataType.String) { IsFilterable = true });
        searchFields.Add(new SimpleField("Term", SearchFieldDataType.String) { IsFilterable = true });
        searchFields.Add(new SimpleField("Definition", SearchFieldDataType.String) { IsFilterable = true });
        searchFields.Add(new VectorSearchField("DefinitionEmbedding", 1536, "my-vector-profile"));

        // Create an index definition with a vectorizer to use when doing vector searches using text.
        var definition = new SearchIndex(indexName, searchFields);
        definition.VectorSearch = new VectorSearch();
        definition.VectorSearch.Vectorizers.Add(new AzureOpenAIVectorizer("text-embedding-vectorizer")
        {
            Parameters = new AzureOpenAIVectorizerParameters
            {
                ResourceUri = new Uri(TestConfiguration.AzureOpenAIEmbeddings.Endpoint),
                DeploymentName = TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                ApiKey = TestConfiguration.AzureOpenAIEmbeddings.ApiKey,
                ModelName = "text-embedding-ada-002"
            }
        });
        definition.VectorSearch.Algorithms.Add(new HnswAlgorithmConfiguration("my-hnsw-vector-config-1") { Parameters = new HnswParameters { Metric = VectorSearchAlgorithmMetric.Cosine } });
        definition.VectorSearch.Profiles.Add(new VectorSearchProfile("my-vector-profile", "my-hnsw-vector-config-1") { VectorizerName = "text-embedding-vectorizer" });

        await searchIndexClient.CreateOrUpdateIndexAsync(definition);
    }
}
