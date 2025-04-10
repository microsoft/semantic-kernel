// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Azure;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Embeddings;

namespace GettingStartedWithVectorStores;

#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete

/// <summary>
/// Example that shows how you can use custom mappers if you wish the data model and storage schema to differ.
/// </summary>
public class Step6_Use_CustomMapper(ITestOutputHelper output, VectorStoresFixture fixture) : BaseTest(output), IClassFixture<VectorStoresFixture>
{
    /// <summary>
    /// Example showing how to upsert and query records when using a custom mapper if you wish
    /// the data model and storage schema to differ.
    ///
    /// This example requires an Azure AI Search service to be available.
    /// </summary>
    [Fact]
    public async Task UseCustomMapperAsync()
    {
        // When using a custom mapper, we still have to describe the storage schema to the vector store
        // using a record definition. Since the storage schema does not match the data model
        // it won't make sense for the vector store to infer the schema from the data model.
        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("Category", typeof(string)),
                new VectorStoreRecordDataProperty("Term", typeof(string)),
                new VectorStoreRecordDataProperty("Definition", typeof(string)),
                new VectorStoreRecordVectorProperty("DefinitionEmbedding", typeof(ReadOnlyMemory<float>)) { Dimensions = 1536 },
            }
        };

        // Construct an Azure AI Search vector store collection and
        // pass in the custom mapper and record definition.
        var collection = new AzureAISearchVectorStoreRecordCollection<string, ComplexGlossary>(
            new SearchIndexClient(
                new Uri(TestConfiguration.AzureAISearch.Endpoint),
                new AzureKeyCredential(TestConfiguration.AzureAISearch.ApiKey)),
            "skglossary",
            new()
            {
                JsonObjectCustomMapper = new CustomMapper(),
                VectorStoreRecordDefinition = recordDefinition
            });

        // Create the collection if it doesn't exist.
        // This call will use the schena defined by the record definition
        // above for creating the collection.
        await collection.CreateCollectionIfNotExistsAsync();

        // Now we can upsert a record using
        // the data model, even though it doesn't match the storage schema.
        var definition = "A set of rules and protocols that allows one software application to interact with another.";
        await collection.UpsertAsync(new ComplexGlossary
        {
            Key = "1",
            Metadata = new Metadata
            {
                Category = "API",
                Term = "Application Programming Interface"
            },
            Definition = definition,
            DefinitionEmbedding = await fixture.TextEmbeddingGenerationService.GenerateEmbeddingAsync(definition)
        });

        // Generate an embedding from the search string.
        var searchVector = await fixture.TextEmbeddingGenerationService.GenerateEmbeddingAsync("How do two software applications interact with another?");

        // Search the vector store.
        var searchResult = collection.VectorizedSearchAsync(
            searchVector,
            top: 1);
        var searchResultItem = await searchResult.FirstAsync();

        // Write the search result with its score to the console.
        Console.WriteLine(searchResultItem.Record.Metadata.Term);
        Console.WriteLine(searchResultItem.Record.Definition);
        Console.WriteLine(searchResultItem.Score);
    }

    /// <summary>
    /// Sample mapper class that maps between the <see cref="ComplexGlossary"/> custom data model
    /// and the <see cref="JsonObject"/> that should match the storage schema.
    /// </summary>
    private sealed class CustomMapper : IVectorStoreRecordMapper<ComplexGlossary, JsonObject>
    {
        public JsonObject MapFromDataToStorageModel(ComplexGlossary dataModel)
        {
            return new JsonObject
            {
                ["Key"] = dataModel.Key,
                ["Category"] = dataModel.Metadata.Category,
                ["Term"] = dataModel.Metadata.Term,
                ["Definition"] = dataModel.Definition,
                ["DefinitionEmbedding"] = JsonSerializer.SerializeToNode(dataModel.DefinitionEmbedding.ToArray())
            };
        }

        public ComplexGlossary MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
        {
            return new ComplexGlossary
            {
                Key = storageModel["Key"]!.ToString(),
                Metadata = new Metadata
                {
                    Category = storageModel["Category"]!.ToString(),
                    Term = storageModel["Term"]!.ToString()
                },
                Definition = storageModel["Definition"]!.ToString(),
                DefinitionEmbedding = JsonSerializer.Deserialize<ReadOnlyMemory<float>>(storageModel["DefinitionEmbedding"])
            };
        }
    }

    /// <summary>
    /// Sample model class that represents a glossary entry.
    /// This model differs from the model used in previous steps by having a complex property
    /// <see cref="Metadata"/> that contains the category and term.
    /// </summary>
    private sealed class ComplexGlossary
    {
        public string Key { get; set; }

        public Metadata Metadata { get; set; }

        public string Definition { get; set; }

        public ReadOnlyMemory<float> DefinitionEmbedding { get; set; }
    }

    private sealed class Metadata
    {
        public string Category { get; set; }

        public string Term { get; set; }
    }
}
