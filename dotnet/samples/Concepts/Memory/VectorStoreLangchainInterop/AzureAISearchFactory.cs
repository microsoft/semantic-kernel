// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;

namespace Memory.VectorStoreLangchainInterop;

/// <summary>
/// Contains a factory method that can be used to create an Azure AI Search vector store that is compatible with datasets ingested using Langchain.
/// </summary>
/// <remarks>
/// This class is used with the <see cref="VectorStore_Langchain_Interop"/> sample.
/// </remarks>
public static class AzureAISearchFactory
{
    /// <summary>
    /// Record definition that matches the storage format used by Langchain for Azure AI Search.
    /// </summary>
    private static readonly VectorStoreRecordDefinition s_recordDefinition = new()
    {
        Properties = new List<VectorStoreRecordProperty>
        {
            new VectorStoreRecordKeyProperty("id", typeof(string)),
            new VectorStoreRecordDataProperty("content", typeof(string)),
            new VectorStoreRecordDataProperty("metadata", typeof(string)),
            new VectorStoreRecordVectorProperty("content_vector", typeof(ReadOnlyMemory<float>)) { Dimensions = 1536 }
        }
    };

    /// <summary>
    /// Create a new Azure AI Search-backed <see cref="IVectorStore"/> that can be used to read data that was ingested using Langchain.
    /// </summary>
    /// <param name="searchIndexClient">Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</param>
    /// <returns>The <see cref="IVectorStore"/>.</returns>
    public static IVectorStore CreateQdrantLangchainInteropVectorStore(SearchIndexClient searchIndexClient)
        => new AzureAISearchLangchainInteropVectorStore(searchIndexClient);

    private sealed class AzureAISearchLangchainInteropVectorStore(SearchIndexClient searchIndexClient, AzureAISearchVectorStoreOptions? options = default)
        : AzureAISearchVectorStore(searchIndexClient, options)
    {
        private readonly SearchIndexClient _searchIndexClient = searchIndexClient;

        public override IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        {
            if (typeof(TKey) != typeof(string) || typeof(TRecord) != typeof(LangchainDocument<string>))
            {
                throw new NotSupportedException("This VectorStore is only usable with string keys and LangchainDocument<string> record types");
            }

            // Create an Azure AI Search collection. To be compatible with Langchain
            // we need to use a custom record definition that matches the
            // schema used by Langchain. We also need to use a custom mapper
            // since the Langchain schema includes a metadata field that is
            // a JSON string containing the source property. Parsing this
            // string and extracting the source is not supported by the default mapper.
            return (new AzureAISearchVectorStoreRecordCollection<TRecord>(
                _searchIndexClient,
                name,
                new()
                {
                    VectorStoreRecordDefinition = s_recordDefinition,
                    JsonObjectCustomMapper = new LangchainInteropMapper() as IVectorStoreRecordMapper<TRecord, JsonObject>
                }) as IVectorStoreRecordCollection<TKey, TRecord>)!;
        }
    }

    /// <summary>
    /// Custom mapper to map the metadata string field, since it contains JSON as a string and this is not supported
    /// automatically by the built in mapper.
    /// </summary>
    private sealed class LangchainInteropMapper : IVectorStoreRecordMapper<LangchainDocument<string>, JsonObject>
    {
        public JsonObject MapFromDataToStorageModel(LangchainDocument<string> dataModel)
        {
            var storageDocument = new AzureAISearchLangchainDocument()
            {
                Key = dataModel.Key,
                Content = dataModel.Content,
                Metadata = $"{{\"source\": \"{dataModel.Source}\"}}",
                Embedding = dataModel.Embedding
            };

            return JsonSerializer.SerializeToNode(storageDocument)!.AsObject();
        }

        public LangchainDocument<string> MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
        {
            var storageDocument = JsonSerializer.Deserialize<AzureAISearchLangchainDocument>(storageModel)!;
            var metadataDocument = JsonSerializer.Deserialize<JsonObject>(storageDocument.Metadata);
            var source = metadataDocument?["source"]?.AsValue()?.ToString();

            return new LangchainDocument<string>()
            {
                Key = storageDocument.Key,
                Content = storageDocument.Content,
                Source = source!,
                Embedding = storageDocument.Embedding
            };
        }
    }

    /// <summary>
    /// Model class that matches the storage format used by Langchain for Azure AI Search.
    /// </summary>
    private sealed class AzureAISearchLangchainDocument
    {
        [JsonPropertyName("id")]
        public string Key { get; set; }

        [JsonPropertyName("content")]
        public string Content { get; set; }

        /// <summary>
        /// The storage format used by Langchain stores the source information
        /// in the metadata field as a JSON string.
        /// E.g. {"source": "my-doc"}
        /// </summary>
        [JsonPropertyName("metadata")]
        public string Metadata { get; set; }

        [JsonPropertyName("content_vector")]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
}
