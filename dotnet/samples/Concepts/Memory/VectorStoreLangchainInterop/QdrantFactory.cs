// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;
using Qdrant.Client.Grpc;

namespace Memory.VectorStoreLangchainInterop;

/// <summary>
/// Contains a factory method that can be used to create a Qdrant vector store that is compatible with datasets ingested using Langchain.
/// </summary>
/// <remarks>
/// This class is used with the <see cref="VectorStore_Langchain_Interop"/> sample.
/// </remarks>
public static class QdrantFactory
{
    /// <summary>
    /// Record definition that matches the storage format used by Langchain for Qdrant.
    /// There is no need to list the data fields, since they have no indexing requirements and Qdrant
    /// doesn't require individual fields to be defined on index creation.
    /// </summary>
    private static readonly VectorStoreRecordDefinition s_recordDefinition = new()
    {
        Properties = new List<VectorStoreRecordProperty>
        {
            new VectorStoreRecordKeyProperty("Key", typeof(Guid)),
            new VectorStoreRecordVectorProperty("Embedding", typeof(ReadOnlyMemory<float>)) { StoragePropertyName = "embedding", Dimensions = 1536 }
        }
    };

    /// <summary>
    /// Create a new Qdrant-backed <see cref="IVectorStore"/> that can be used to read data that was ingested using Langchain.
    /// </summary>
    /// <param name="qdrantClient">Qdrant client that can be used to manage the collections and points in a Qdrant store.</param>
    /// <returns>The <see cref="IVectorStore"/>.</returns>
    public static IVectorStore CreateQdrantLangchainInteropVectorStore(QdrantClient qdrantClient)
        => new QdrantLangchainInteropVectorStore(qdrantClient);

    private sealed class QdrantLangchainInteropVectorStore(QdrantClient qdrantClient)
        : QdrantVectorStore(qdrantClient)
    {
        private readonly QdrantClient _qdrantClient = qdrantClient;

        public override IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        {
            // Create a Qdrant collection. To be compatible with Langchain
            // we need to use a custom record definition that matches the
            // schema used by Langchain. We also need to use a custom mapper
            // since the Langchain schema includes a metadata field that is
            // a struct and this isn't supported by the default mapper.
            // Since langchain creates collections without named vector support
            // we should set HasNamedVectors to false.
            var collection = new QdrantVectorStoreRecordCollection<LangchainDocument<Guid>>(
                _qdrantClient,
                name,
                new()
                {
                    HasNamedVectors = false,
                    VectorStoreRecordDefinition = s_recordDefinition,
                    PointStructCustomMapper = new LangchainInteropMapper()
                });

            // If the user asked for a guid key, we can return the collection as is.
            if (typeof(TKey) == typeof(Guid) && typeof(TRecord) == typeof(LangchainDocument<Guid>))
            {
                return (collection as IVectorStoreRecordCollection<TKey, TRecord>)!;
            }

#if DISABLED_FOR_NOW // TODO: See note on MappingVectorStoreRecordCollection
            // If the user asked for a string key, we can add a decorator which converts back and forth between string and guid.
            // The string that the user provides will still need to contain a valid guid, since the Langchain created collection
            // uses guid keys.
            // Supporting string keys like this is useful since it means you can work with the collection in the same way as with
            // collections from other vector stores that support string keys.
            if (typeof(TKey) == typeof(string) && typeof(TRecord) == typeof(LangchainDocument<string>))
            {
                var stringKeyCollection = new MappingVectorStoreRecordCollection<string, Guid, LangchainDocument<string>, LangchainDocument<Guid>>(
                    collection,
                    p => Guid.Parse(p),
                    i => i.ToString("D"),
                    p => new LangchainDocument<Guid> { Key = Guid.Parse(p.Key), Content = p.Content, Source = p.Source, Embedding = p.Embedding },
                    i => new LangchainDocument<string> { Key = i.Key.ToString("D"), Content = i.Content, Source = i.Source, Embedding = i.Embedding });

                return (stringKeyCollection as IVectorStoreRecordCollection<TKey, TRecord>)!;
            }
#endif

            throw new NotSupportedException("This VectorStore is only usable with Guid keys and LangchainDocument<Guid> record types or string keys and LangchainDocument<string> record types");
        }
    }

    /// <summary>
    /// A custom mapper that is required to map the metadata struct. While the other
    /// fields in the record can be mapped by the default Qdrant mapper, the default
    /// mapper doesn't support complex types like metadata, which is a Qdrant struct
    /// containing a source field.
    /// </summary>
    private sealed class LangchainInteropMapper : IVectorStoreRecordMapper<LangchainDocument<Guid>, PointStruct>
    {
        public PointStruct MapFromDataToStorageModel(LangchainDocument<Guid> dataModel)
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

        public LangchainDocument<Guid> MapFromStorageToDataModel(PointStruct storageModel, StorageToDataModelMapperOptions options)
        {
            return new LangchainDocument<Guid>()
            {
                Key = new Guid(storageModel.Id.Uuid),
                Content = storageModel.Payload["page_content"].StringValue,
                Source = storageModel.Payload["metadata"].StructValue.Fields["source"].StringValue,
                Embedding = options.IncludeVectors ? storageModel.Vectors.Vector.Data.ToArray() : null
            };
        }
    }
}
