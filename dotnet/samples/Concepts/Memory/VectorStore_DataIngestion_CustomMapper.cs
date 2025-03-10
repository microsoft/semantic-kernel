// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Azure.Identity;
using Memory.VectorStoreFixtures;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Embeddings;
using StackExchange.Redis;

namespace Memory;

/// <summary>
/// An example showing how to ingest data into a vector store using <see cref="RedisVectorStore"/> with a custom mapper.
/// In this example, the storage model differs significantly from the data model, so a custom mapper is used to map between the two.
/// A <see cref="VectorStoreRecordDefinition"/> is used to define the schema of the storage model, and this means that the connector
/// will not try and infer the schema from the data model.
/// In storage the data is stored as a JSON object that looks similar to this:
/// <code>
/// {
///   "Term": "API",
///   "Definition": "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data.",
///   "DefinitionEmbedding": [ ... ]
/// }
/// </code>
/// However, the data model is a class with a property for key and two dictionaries for the data (Term and Definition) and vector (DefinitionEmbedding).
///
/// The example shows the following steps:
/// 1. Create an embedding generator.
/// 2. Create a Redis Vector Store using a custom factory for creating collections.
///    When constructing a collection, the factory injects a custom mapper that maps between the data model and the storage model if required.
/// 3. Ingest some data into the vector store.
/// 4. Read the data back from the vector store.
///
/// You need a local instance of Docker running, since the associated fixture will try and start a Redis container in the local docker instance to run against.
/// </summary>
public class VectorStore_DataIngestion_CustomMapper(ITestOutputHelper output, VectorStoreRedisContainerFixture redisFixture) : BaseTest(output), IClassFixture<VectorStoreRedisContainerFixture>
{
    /// <summary>
    /// A record definition for the glossary entries that defines the storage schema of the record.
    /// </summary>
    private static readonly VectorStoreRecordDefinition s_glossaryDefinition = new()
    {
        Properties = new List<VectorStoreRecordProperty>
        {
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Term", typeof(string)),
            new VectorStoreRecordDataProperty("Definition", typeof(string)),
            new VectorStoreRecordVectorProperty("DefinitionEmbedding", typeof(ReadOnlyMemory<float>)) { Dimensions = 1536, DistanceFunction = DistanceFunction.DotProductSimilarity }
        }
    };

    [Fact]
    public async Task ExampleAsync()
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Initiate the docker container and construct the vector store using the custom factory for creating collections.
        await redisFixture.ManualInitializeAsync();
        ConnectionMultiplexer redis = ConnectionMultiplexer.Connect("localhost:6379");
        var vectorStore = new CustomRedisVectorStore(redis.GetDatabase());

        // Get and create collection if it doesn't exist, using the record definition containing the storage model.
        var collection = vectorStore.GetCollection<string, GenericDataModel>("skglossary", s_glossaryDefinition);
        await collection.CreateCollectionIfNotExistsAsync();

        // Create glossary entries and generate embeddings for them.
        var glossaryEntries = CreateGlossaryEntries().ToList();
        var tasks = glossaryEntries.Select(entry => Task.Run(async () =>
        {
            entry.Vectors["DefinitionEmbedding"] = await textEmbeddingGenerationService.GenerateEmbeddingAsync((string)entry.Data["Definition"]);
        }));
        await Task.WhenAll(tasks);

        // Upsert the glossary entries into the collection and return their keys.
        var upsertedKeysTasks = glossaryEntries.Select(x => collection.UpsertAsync(x));
        var upsertedKeys = await Task.WhenAll(upsertedKeysTasks);

        // Retrieve one of the upserted records from the collection.
        var upsertedRecord = await collection.GetAsync(upsertedKeys.First(), new() { IncludeVectors = true });

        // Write upserted keys and one of the upserted records to the console.
        Console.WriteLine($"Upserted keys: {string.Join(", ", upsertedKeys)}");
        Console.WriteLine($"Upserted record: {JsonSerializer.Serialize(upsertedRecord)}");
    }

    /// <summary>
    /// A custom mapper that maps between the data model and the storage model.
    /// </summary>
    private sealed class Mapper : IVectorStoreRecordMapper<GenericDataModel, (string Key, JsonNode Node)>
    {
        public (string Key, JsonNode Node) MapFromDataToStorageModel(GenericDataModel dataModel)
        {
            var jsonObject = new JsonObject();

            jsonObject.Add("Term", dataModel.Data["Term"].ToString());
            jsonObject.Add("Definition", dataModel.Data["Definition"].ToString());

            var vector = (ReadOnlyMemory<float>)dataModel.Vectors["DefinitionEmbedding"];
            var jsonArray = new JsonArray(vector.ToArray().Select(x => JsonValue.Create(x)).ToArray());
            jsonObject.Add("DefinitionEmbedding", jsonArray);

            return (dataModel.Key, jsonObject);
        }

        public GenericDataModel MapFromStorageToDataModel((string Key, JsonNode Node) storageModel, StorageToDataModelMapperOptions options)
        {
            var dataModel = new GenericDataModel
            {
                Key = storageModel.Key,
                Data = new Dictionary<string, object>
                {
                    { "Term", (string)storageModel.Node["Term"]! },
                    { "Definition", (string)storageModel.Node["Definition"]! }
                },
                Vectors = new Dictionary<string, object>
                {
                    { "DefinitionEmbedding", new ReadOnlyMemory<float>(storageModel.Node["DefinitionEmbedding"]!.AsArray().Select(x => (float)x!).ToArray()) }
                }
            };

            return dataModel;
        }
    }

    private sealed class CustomRedisVectorStore(IDatabase database, RedisVectorStoreOptions? options = default)
        : RedisVectorStore(database, options)
    {
        private readonly IDatabase _database = database;

        public override IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        {
            // If the record definition is the glossary definition and the record type is the generic data model, inject the custom mapper into the collection options.
            if (vectorStoreRecordDefinition == s_glossaryDefinition && typeof(TRecord) == typeof(GenericDataModel))
            {
                var customCollection = new RedisJsonVectorStoreRecordCollection<GenericDataModel>(_database, name, new() { VectorStoreRecordDefinition = vectorStoreRecordDefinition, JsonNodeCustomMapper = new Mapper() }) as IVectorStoreRecordCollection<TKey, TRecord>;
                return customCollection!;
            }

            // Otherwise, just create a standard collection with the default mapper.
            var collection = new RedisJsonVectorStoreRecordCollection<TRecord>(_database, name, new() { VectorStoreRecordDefinition = vectorStoreRecordDefinition }) as IVectorStoreRecordCollection<TKey, TRecord>;
            return collection!;
        }
    }

    /// <summary>
    /// Sample generic data model class that can store any data.
    /// </summary>
    private sealed class GenericDataModel
    {
        public string Key { get; set; }

        public Dictionary<string, object> Data { get; set; }

        public Dictionary<string, object> Vectors { get; set; }
    }

    /// <summary>
    /// Create some sample glossary entries using the generic data model.
    /// </summary>
    /// <returns>A list of sample glossary entries.</returns>
    private static IEnumerable<GenericDataModel> CreateGlossaryEntries()
    {
        yield return new GenericDataModel
        {
            Key = "1",
            Data = new()
            {
                { "Term", "API" },
                { "Definition", "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data." }
            },
            Vectors = new()
        };

        yield return new GenericDataModel
        {
            Key = "2",
            Data = new()
            {
                { "Term", "Connectors" },
                { "Definition", "Connectors allow you to integrate with various services provide AI capabilities, including LLM, AudioToText, TextToAudio, Embedding generation, etc." }
            },
            Vectors = new()
        };

        yield return new GenericDataModel
        {
            Key = "3",
            Data = new()
            {
                { "Term", "RAG" },
                { "Definition", "Retrieval Augmented Generation - a term that refers to the process of retrieving additional data to provide as context to an LLM to use when generating a response (completion) to a user’s question (prompt)." }
            },
            Vectors = new()
        };
    }
}
