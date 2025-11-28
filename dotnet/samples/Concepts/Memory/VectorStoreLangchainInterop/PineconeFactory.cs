// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Pinecone;

namespace Memory.VectorStoreLangchainInterop;

/// <summary>
/// Contains a factory method that can be used to create a Pinecone vector store that is compatible with datasets ingested using Langchain.
/// </summary>
/// <remarks>
/// This class is used with the <see cref="VectorStore_Langchain_Interop"/> sample.
/// </remarks>
public static class PineconeFactory
{
    /// <summary>
    /// Record definition that matches the storage format used by Langchain for Pinecone.
    /// </summary>
    private static readonly VectorStoreCollectionDefinition s_definition = new()
    {
        Properties =
        [
            new VectorStoreKeyProperty("Key", typeof(string)),
            new VectorStoreDataProperty("Content", typeof(string)) { StorageName = "text" },
            new VectorStoreDataProperty("Source", typeof(string)) { StorageName = "source" },
            new VectorStoreVectorProperty("Embedding", typeof(ReadOnlyMemory<float>), 1536) { StorageName = "embedding" }
        ]
    };

    /// <summary>
    /// Create a new Pinecone-backed <see cref="VectorStore"/> that can be used to read data that was ingested using Langchain.
    /// </summary>
    /// <param name="pineconeClient">Pinecone client that can be used to manage the collections and points in a Pinecone store.</param>
    /// <returns>The <see cref="VectorStore"/>.</returns>
    public static VectorStore CreatePineconeLangchainInteropVectorStore(PineconeClient pineconeClient)
        => new PineconeLangchainInteropVectorStore(new PineconeVectorStore(pineconeClient), pineconeClient);

    private sealed class PineconeLangchainInteropVectorStore(
        VectorStore innerStore,
        PineconeClient pineconeClient)
        : VectorStore
    {
        private readonly PineconeClient _pineconeClient = pineconeClient;

        public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
        {
            if (typeof(TKey) != typeof(string) || typeof(TRecord) != typeof(LangchainDocument<string>))
            {
                throw new NotSupportedException("This VectorStore is only usable with string keys and LangchainDocument<string> record types");
            }

            // Create a Pinecone collection and pass in our custom record definition that matches
            // the schema used by Langchain so that the default mapper can use the storage names
            // in it, to map to the storage scheme.
            return (new PineconeCollection<TKey, TRecord>(
                _pineconeClient,
                name,
                new()
                {
                    Definition = s_definition
                }) as VectorStoreCollection<TKey, TRecord>)!;
        }

        public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreCollectionDefinition? definition = null)
        {
            // Create a Pinecone collection and pass in our custom record definition that matches
            // the schema used by Langchain so that the default mapper can use the storage names
            // in it, to map to the storage scheme.
            return new PineconeDynamicCollection(
                _pineconeClient,
                name,
                new()
                {
                    Definition = s_definition
                });
        }

        public override object? GetService(Type serviceType, object? serviceKey = null) => innerStore.GetService(serviceType, serviceKey);

        public override IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default) => innerStore.ListCollectionNamesAsync(cancellationToken);

        public override Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default) => innerStore.CollectionExistsAsync(name, cancellationToken);

        public override Task EnsureCollectionDeletedAsync(string name, CancellationToken cancellationToken = default) => innerStore.EnsureCollectionDeletedAsync(name, cancellationToken);
    }
}
