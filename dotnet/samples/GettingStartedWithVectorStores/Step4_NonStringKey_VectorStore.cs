// Copyright (c) Microsoft. All rights reserved.

#if DISABLED_FOR_NOW // TODO: See note in MappingVectorStoreRecordCollection

using System.Runtime.CompilerServices;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;

namespace GettingStartedWithVectorStores;


/// <summary>
/// Example that shows that you can switch between different vector stores with the same code, in this case
/// with a vector store that doesn't use string keys.
/// This sample demonstrates one possible approach, however it is also possible to use generics
/// in the common code to achieve code reuse.
/// </summary>
public class Step4_NonStringKey_VectorStore(ITestOutputHelper output, VectorStoresFixture fixture) : BaseTest(output), IClassFixture<VectorStoresFixture>
{
    /// <summary>
    /// Here we are going to use the same code that we used in <see cref="Step1_Ingest_Data"/> and <see cref="Step2_Vector_Search"/>
    /// but now with an <see cref="QdrantVectorStore"/>.
    /// Qdrant uses Guid or ulong as the key type, but the common code works with a string key. The string keys of the records created
    /// in <see cref="Step1_Ingest_Data"/> contain numbers though, so it's possible for us to convert them to ulong.
    /// In this example, we'll demonstrate how to do that.
    ///
    /// This example requires a Qdrant server up and running. To run a Qdrant server in a Docker container, use the following command:
    /// docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest
    /// </summary>
    [Fact]
    public async Task UseAQdrantVectorStoreAsync()
    {
        // Construct a Qdrant vector store collection.
        var collection = new QdrantVectorStoreRecordCollection<UlongGlossary>(new QdrantClient("localhost"), "skglossary");

        // Wrap the collection using a decorator that allows us to expose a version that uses string keys, but internally
        // we convert to and from ulong.
        var stringKeyCollection = new MappingVectorStoreRecordCollection<string, ulong, Glossary, UlongGlossary>(
            collection,
            p => ulong.Parse(p),
            i => i.ToString(),
            p => new UlongGlossary { Key = ulong.Parse(p.Key), Category = p.Category, Term = p.Term, Definition = p.Definition, DefinitionEmbedding = p.DefinitionEmbedding },
            i => new Glossary { Key = i.Key.ToString("D"), Category = i.Category, Term = i.Term, Definition = i.Definition, DefinitionEmbedding = i.DefinitionEmbedding });

        // Ingest data into the collection using the same code as we used in Step1 with the InMemory Vector Store.
        await Step1_Ingest_Data.IngestDataIntoVectorStoreAsync(stringKeyCollection, fixture.TextEmbeddingGenerationService);

        // Search the vector store using the same code as we used in Step2 with the InMemory Vector Store.
        var searchResultItem = await Step2_Vector_Search.SearchVectorStoreAsync(
            stringKeyCollection,
            "What is an Application Programming Interface?",
            fixture.TextEmbeddingGenerationService);

        // Write the search result with its score to the console.
        Console.WriteLine(searchResultItem.Record.Definition);
        Console.WriteLine(searchResultItem.Score);
    }

    /// <summary>
    /// Data model that uses a ulong as the key type instead of a string.
    /// </summary>
    private sealed class UlongGlossary
    {
        [VectorStoreRecordKey]
        public ulong Key { get; set; }

        [VectorStoreRecordData(IsFilterable = true)]
        public string Category { get; set; }

        [VectorStoreRecordData]
        public string Term { get; set; }

        [VectorStoreRecordData]
        public string Definition { get; set; }

        [VectorStoreRecordVector(Dimensions: 1536)]
        public ReadOnlyMemory<float> DefinitionEmbedding { get; set; }
    }

    /// <summary>
    /// Simple decorator class that allows conversion of keys and records from one type to another.
    /// </summary>
    private sealed class MappingVectorStoreRecordCollection<TPublicKey, TInternalKey, TPublicRecord, TInternalRecord> : IVectorStoreRecordCollection<TPublicKey, TPublicRecord>
        where TPublicKey : notnull
        where TInternalKey : notnull
    {
        private readonly IVectorStoreRecordCollection<TInternalKey, TInternalRecord> _collection;
        private readonly Func<TPublicKey, TInternalKey> _publicToInternalKeyMapper;
        private readonly Func<TInternalKey, TPublicKey> _internalToPublicKeyMapper;
        private readonly Func<TPublicRecord, TInternalRecord> _publicToInternalRecordMapper;
        private readonly Func<TInternalRecord, TPublicRecord> _internalToPublicRecordMapper;

        public MappingVectorStoreRecordCollection(
            IVectorStoreRecordCollection<TInternalKey, TInternalRecord> collection,
            Func<TPublicKey, TInternalKey> publicToInternalKeyMapper,
            Func<TInternalKey, TPublicKey> internalToPublicKeyMapper,
            Func<TPublicRecord, TInternalRecord> publicToInternalRecordMapper,
            Func<TInternalRecord, TPublicRecord> internalToPublicRecordMapper)
        {
            this._collection = collection;
            this._publicToInternalKeyMapper = publicToInternalKeyMapper;
            this._internalToPublicKeyMapper = internalToPublicKeyMapper;
            this._publicToInternalRecordMapper = publicToInternalRecordMapper;
            this._internalToPublicRecordMapper = internalToPublicRecordMapper;
        }

        /// <inheritdoc />
        public string CollectionName => this._collection.CollectionName;

        /// <inheritdoc />
        public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
        {
            return this._collection.CollectionExistsAsync(cancellationToken);
        }

        /// <inheritdoc />
        public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
        {
            return this._collection.CreateCollectionAsync(cancellationToken);
        }

        /// <inheritdoc />
        public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
        {
            return this._collection.CreateCollectionIfNotExistsAsync(cancellationToken);
        }

        /// <inheritdoc />
        public Task DeleteAsync(TPublicKey key, CancellationToken cancellationToken = default)
        {
            return this._collection.DeleteAsync(this._publicToInternalKeyMapper(key), cancellationToken);
        }

        /// <inheritdoc />
        public Task DeleteBatchAsync(IEnumerable<TPublicKey> keys, CancellationToken cancellationToken = default)
        {
            return this._collection.DeleteBatchAsync(keys.Select(this._publicToInternalKeyMapper), cancellationToken);
        }

        /// <inheritdoc />
        public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
        {
            return this._collection.DeleteCollectionAsync(cancellationToken);
        }

        /// <inheritdoc />
        public async Task<TPublicRecord?> GetAsync(TPublicKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
        {
            var internalRecord = await this._collection.GetAsync(this._publicToInternalKeyMapper(key), options, cancellationToken).ConfigureAwait(false);
            if (internalRecord == null)
            {
                return default;
            }

            return this._internalToPublicRecordMapper(internalRecord);
        }

        /// <inheritdoc />
        public IAsyncEnumerable<TPublicRecord> GetBatchAsync(IEnumerable<TPublicKey> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
        {
            var internalRecords = this._collection.GetBatchAsync(keys.Select(this._publicToInternalKeyMapper), options, cancellationToken);
            return internalRecords.Select(this._internalToPublicRecordMapper);
        }

        /// <inheritdoc />
        public async Task<TPublicKey> UpsertAsync(TPublicRecord record, CancellationToken cancellationToken = default)
        {
            var internalRecord = this._publicToInternalRecordMapper(record);
            var internalKey = await this._collection.UpsertAsync(internalRecord, cancellationToken).ConfigureAwait(false);
            return this._internalToPublicKeyMapper(internalKey);
        }

        /// <inheritdoc />
        public async IAsyncEnumerable<TPublicKey> UpsertBatchAsync(IEnumerable<TPublicRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            var internalRecords = records.Select(this._publicToInternalRecordMapper);
            var internalKeys = this._collection.UpsertBatchAsync(internalRecords, cancellationToken);
            await foreach (var internalKey in internalKeys.ConfigureAwait(false))
            {
                yield return this._internalToPublicKeyMapper(internalKey);
            }
        }

        /// <inheritdoc />
        public async Task<VectorSearchResults<TPublicRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions? options = null, CancellationToken cancellationToken = default)
        {
            var searchResults = await this._collection.VectorizedSearchAsync(vector, options, cancellationToken).ConfigureAwait(false);
            var publicResultRecords = searchResults.Results.Select(result => new VectorSearchResult<TPublicRecord>(this._internalToPublicRecordMapper(result.Record), result.Score));

            return new VectorSearchResults<TPublicRecord>(publicResultRecords)
            {
                TotalCount = searchResults.TotalCount,
                Metadata = searchResults.Metadata,
            };
        }
    }
}

#endif
