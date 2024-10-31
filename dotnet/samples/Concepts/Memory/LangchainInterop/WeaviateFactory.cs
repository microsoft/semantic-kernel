// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Weaviate;

namespace Memory.VectorstoreLangchainInterop;

/// <summary>
/// Contains a factory method that can be used to create a Weaviate vector store that is compatible with datasets ingested using Langchain.
/// </summary>
/// <remarks>
/// This class is used with the <see cref="VectorStore_Langchain_Interop"/> sample.
/// </remarks>
public static class WeaviateFactory
{
    /// <summary>
    /// Create a new Weaviate-backed <see cref="IVectorStore"/> that can be used to read data that was ingested using Langchain.
    /// </summary>
    /// <param name="httpClient">The httpClient to use to connecto to Weaviate.</param>
    /// <returns>The <see cref="IVectorStore"/>.</returns>
    public static IVectorStore CreateWeaviateLangchainInteropVectorStore(HttpClient httpClient)
    {
        // Create a vector store that uses our custom factory for creating collections
        // so that the collection can be configured to be compatible with Langchain.
        return new WeaviateVectorStore(
            httpClient,
            new()
            {
                VectorStoreCollectionFactory = new WeaviateVectorStoreRecordCollectionFactory()
            });
    }

    /// <summary>
    /// Factory that is used to inject the appropriate <see cref="VectorStoreRecordDefinition"/> for Langchain interoperability.
    /// </summary>
    private sealed class WeaviateVectorStoreRecordCollectionFactory : IWeaviateVectorStoreRecordCollectionFactory
    {
        public IVectorStoreRecordCollection<TKey, TRecord> CreateVectorStoreRecordCollection<TKey, TRecord>(HttpClient httpClient, string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition) where TKey : notnull
        {
            // Create a Weaviate collection. To be compatible with Langchain
            // we need to use a custom data model that matches the
            // schema used by Langchain.
            var collection = new WeaviateVectorStoreRecordCollection<WeaviateLangchainDocument>(
                httpClient,
                name);

            // If the user asked for a guid key, we can return the collection with a simple mapper around it
            // to map from the internel data model to the common one.
            if (typeof(TKey) == typeof(Guid) && typeof(TRecord) == typeof(LangchainDocument<Guid>))
            {
                var stringKeyCollection = new MappingVectorStoreRecordCollection<Guid, Guid, LangchainDocument<Guid>, WeaviateLangchainDocument>(
                    collection,
                    p => p,
                    i => i,
                    p => new WeaviateLangchainDocument { Key = p.Key, Content = p.Content, Source = p.Source, Embedding = p.Embedding },
                    i => new LangchainDocument<Guid> { Key = i.Key, Content = i.Content, Source = i.Source, Embedding = i.Embedding });

                return (stringKeyCollection as IVectorStoreRecordCollection<TKey, TRecord>)!;
            }

            // If the user asked for a string key, we can add a decorator which converts back and forth between string and guid.
            // The string that the user provides will still need to contain a valid guid, since the Weaviate only supports
            // guid keys.
            // Supporting string keys like this is useful since it means you can work with the collection in the same way as with
            // collections from other vector stores that support string keys.
            if (typeof(TKey) == typeof(string) && typeof(TRecord) == typeof(LangchainDocument<string>))
            {
                var stringKeyCollection = new MappingVectorStoreRecordCollection<string, Guid, LangchainDocument<string>, WeaviateLangchainDocument>(
                    collection,
                    p => Guid.Parse(p),
                    i => i.ToString("D"),
                    p => new WeaviateLangchainDocument { Key = Guid.Parse(p.Key), Content = p.Content, Source = p.Source, Embedding = p.Embedding },
                    i => new LangchainDocument<string> { Key = i.Key.ToString("D"), Content = i.Content, Source = i.Source, Embedding = i.Embedding });

                return (stringKeyCollection as IVectorStoreRecordCollection<TKey, TRecord>)!;
            }

            throw new NotSupportedException("This VectorStore is only usable with Guid keys and LangchainDocument<Guid> record types or string keys and LangchainDocument<string> record types");
        }
    }

    /// <summary>
    /// Define an internal data model that is compatible with the way in which
    /// Langhchain stores data in Weaviate.
    /// </summary>
    public class WeaviateLangchainDocument
    {
        [VectorStoreRecordKey]
        public Guid Key { get; set; }

        [JsonPropertyName("text")]
        [VectorStoreRecordData]
        public string Content { get; set; }

        [JsonPropertyName("source")]
        [VectorStoreRecordData]
        public string Source { get; set; }

        [VectorStoreRecordVector(Dimensions: 1536)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
}
