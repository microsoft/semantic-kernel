// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Embeddings;
using Qdrant.Client;
using Qdrant.Client.Grpc;

namespace Memory;

/// <summary>
/// Example showing how to consume data that had previously been
/// ingested into a Qdrant instance using Langchain.
/// </summary>
/// <remarks>
/// To run this sample, you need to first create an instance of a
/// Qdrant collection using Langhain.
/// This sample assumes that you used the pets sample data set from this article:
/// https://python.langchain.com/docs/tutorials/retrievers/#documents
/// And the from_documents method to create the collection as shown here:
/// https://python.langchain.com/docs/tutorials/retrievers/#vector-stores
///
/// Since the source field is stored as a subfield on the metadata field, and
/// the default Qdrant mapper doesn't support complex types, we need to create a custom mapper.
/// </remarks>
public class VectorStore_Langchain_Interop_Qdrant(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ReadDataFromLangchainQdrantAsync()
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Get the collection.
        var qdrantClient = new QdrantClient("localhost");
        var collection = new QdrantVectorStoreRecordCollection<QdrantLangchainDocument>(
            qdrantClient,
            "pets",
            new() { PointStructCustomMapper = new LangchainInteropMapper() });

        // Search the data set.
        var searchString = "I'm looking for an animal that is loyal and will make a great companion";
        var searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);
        var searchResult = await collection.VectorizedSearchAsync(searchVector, new() { Top = 1 });
        var resultRecords = await searchResult.Results.ToListAsync();

        this.Output.WriteLine("Search string: " + searchString);
        this.Output.WriteLine("Source: " + resultRecords.First().Record.Source);
        this.Output.WriteLine("Text: " + resultRecords.First().Record.Content);
        this.Output.WriteLine();
    }

    /// <summary>
    /// Model class containing the fields we want to map from the Qdrant storage format.
    /// </summary>
    /// <remarks>
    /// Note that since we won't be using this data model to infer a schema from
    /// for creating a new collection or to do data model to storage model mapping with,
    /// we can just specify the most minimal of attributes.
    /// </remarks>
    private sealed class QdrantLangchainDocument
    {
        [VectorStoreRecordKey]
        public Guid Key { get; set; }

        public string Content { get; set; }

        public string Source { get; set; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }

    /// <summary>
    /// Custom mapper to map the metadata struct, since the default
    /// Qdrant mapper doesn't support complex types.
    /// </summary>
    private sealed class LangchainInteropMapper : IVectorStoreRecordMapper<QdrantLangchainDocument, PointStruct>
    {
        public PointStruct MapFromDataToStorageModel(QdrantLangchainDocument dataModel)
        {
            var metadataStruct = new Struct()
            {
                Fields = { ["source"] = dataModel.Source }
            };

            var pointStruct = new PointStruct()
            {
                Id = new PointId() { Uuid = dataModel.Key.ToString("D") },
                Vectors = new Vectors() { Vector = dataModel.Embedding.ToArray() },
                Payload =
                {
                    ["page_content"] = dataModel.Content,
                    ["metadata"] = new Value() { StructValue = metadataStruct }
                },
            };

            return pointStruct;
        }

        public QdrantLangchainDocument MapFromStorageToDataModel(PointStruct storageModel, StorageToDataModelMapperOptions options)
        {
            return new QdrantLangchainDocument()
            {
                Key = new Guid(storageModel.Id.Uuid),
                Content = storageModel.Payload["page_content"].StringValue,
                Source = storageModel.Payload["metadata"].StructValue.Fields["source"].StringValue,
                Embedding = options.IncludeVectors ? storageModel.Vectors.Vector.Data.ToArray() : null
            };
        }
    }
}
