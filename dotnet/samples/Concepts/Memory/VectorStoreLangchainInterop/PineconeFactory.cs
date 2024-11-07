﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Sdk = Pinecone;

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
    private static readonly VectorStoreRecordDefinition s_recordDefinition = new()
    {
        Properties = new List<VectorStoreRecordProperty>
        {
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Content", typeof(string)) { StoragePropertyName = "text" },
            new VectorStoreRecordDataProperty("Source", typeof(string)) { StoragePropertyName = "source" },
            new VectorStoreRecordVectorProperty("Embedding", typeof(ReadOnlyMemory<float>)) { StoragePropertyName = "embedding", Dimensions = 1536 }
        }
    };

    /// <summary>
    /// Create a new Pinecone-backed <see cref="IVectorStore"/> that can be used to read data that was ingested using Langchain.
    /// </summary>
    /// <param name="pineconeClient">Pinecone client that can be used to manage the collections and points in a Pinecone store.</param>
    /// <returns>The <see cref="IVectorStore"/>.</returns>
    public static IVectorStore CreatePineconeLangchainInteropVectorStore(Sdk.PineconeClient pineconeClient)
    {
        // Create a vector store that uses our custom factory for creating collections
        // so that the collection can be configured to be compatible with Langchain.
        return new PineconeVectorStore(
            pineconeClient,
            new()
            {
                VectorStoreCollectionFactory = new PineconeVectorStoreRecordCollectionFactory()
            });
    }

    /// <summary>
    /// Factory that is used to inject the appropriate <see cref="VectorStoreRecordDefinition"/> for Langchain interoperability.
    /// </summary>
    private sealed class PineconeVectorStoreRecordCollectionFactory : IPineconeVectorStoreRecordCollectionFactory
    {
        public IVectorStoreRecordCollection<TKey, TRecord> CreateVectorStoreRecordCollection<TKey, TRecord>(Sdk.PineconeClient pineconeClient, string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition) where TKey : notnull
        {
            if (typeof(TKey) != typeof(string) || typeof(TRecord) != typeof(LangchainDocument<string>))
            {
                throw new NotSupportedException("This VectorStore is only usable with string keys and LangchainDocument<string> record types");
            }

            // Create a Pinecone collection and pass in our custom record definition that matches
            // the schema used by Langchain so that the default mapper can use the storage names
            // in it, to map to the storage scheme.
            return (new PineconeVectorStoreRecordCollection<TRecord>(
                pineconeClient,
                name,
                new()
                {
                    VectorStoreRecordDefinition = s_recordDefinition
                }) as IVectorStoreRecordCollection<TKey, TRecord>)!;
        }
    }
}
