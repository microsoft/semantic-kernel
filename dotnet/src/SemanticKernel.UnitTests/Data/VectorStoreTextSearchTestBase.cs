// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;

namespace SemanticKernel.UnitTests.Data;

#pragma warning disable CA1052 // Static holder types should be Static or NotInheritable
#pragma warning disable RCS1102 // Make class static
public class VectorStoreTextSearchTestBase
#pragma warning restore RCS1102 // Make class static
#pragma warning restore CA1052 // Static holder types should be Static or NotInheritable
{
    /// <summary>
    /// Create a <see cref="VectorStoreTextSearch{TRecord}"/> from a <see cref="IVectorizedSearch{TRecord}"/>.
    /// </summary>
    public static async Task<VectorStoreTextSearch<DataModel>> CreateVectorStoreTextSearchFromVectorizedSearchAsync()
    {
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();
        var embeddingService = new MockTextEmbeddingGenerationService();
        await AddRecordsAsync(vectorSearch, embeddingService);
        var sut = new VectorStoreTextSearch<DataModel>(vectorSearch, embeddingService, stringMapper, resultMapper);
        return sut;
    }

    /// <summary>
    /// Create a <see cref="VectorStoreTextSearch{TRecord}"/> from a <see cref="IVectorizedSearch{TRecord}"/>.
    /// </summary>
    public static async Task<VectorStoreTextSearch<DataModel>> CreateVectorStoreTextSearchFromVectorizableTextSearchAsync()
    {
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();
        var embeddingService = new MockTextEmbeddingGenerationService();
        await AddRecordsAsync(vectorSearch, embeddingService);
        var vectorizableTextSearch = new VectorizedSearchWrapper<DataModel>(vectorSearch, new MockTextEmbeddingGenerationService());
        var sut = new VectorStoreTextSearch<DataModel>(vectorizableTextSearch, stringMapper, resultMapper);
        return sut;
    }

    /// <summary>
    /// Add sample records to the vector store record collection.
    /// </summary>
    public static async Task AddRecordsAsync(
        IVectorStoreRecordCollection<Guid, DataModel> recordCollection,
        ITextEmbeddingGenerationService embeddingService,
        int? count = 10)
    {
        await recordCollection.CreateCollectionIfNotExistsAsync();
        for (var i = 0; i < count; i++)
        {
            DataModel dataModel = new()
            {
                Key = Guid.NewGuid(),
                Text = $"Record {i}",
                Tag = i % 2 == 0 ? "Even" : "Odd",
                Embedding = await embeddingService.GenerateEmbeddingAsync($"Record {i}")
            };
            await recordCollection.UpsertAsync(dataModel);
        }
    }

    /// <summary>
    /// String mapper which converts a DataModel to a string.
    /// </summary>
    public sealed class DataModelTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            if (result is DataModel dataModel)
            {
                return dataModel.Text;
            }
            throw new ArgumentException("Invalid result type.");
        }
    }

    /// <summary>
    /// Result mapper which converts a DataModel to a TextSearchResult.
    /// </summary>
    public sealed class DataModelTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is DataModel dataModel)
            {
                return new TextSearchResult(value: dataModel.Text) { Name = dataModel.Key.ToString() };
            }
            throw new ArgumentException("Invalid result type.");
        }
    }

    /// <summary>
    /// Mock implementation of <see cref="ITextEmbeddingGenerationService"/>.
    /// </summary>
    public sealed class MockTextEmbeddingGenerationService : ITextEmbeddingGenerationService
    {
        /// <inheritdoc />
        public IReadOnlyDictionary<string, object?> Attributes { get; } = ReadOnlyDictionary<string, object?>.Empty;

        /// <inheritdoc />
        public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            IList<ReadOnlyMemory<float>> result = [new float[] { 0, 1, 2, 3 }];
            return Task.FromResult(result);
        }
    }

    /// <summary>
    /// Decorator for a <see cref="IVectorizedSearch{TRecord}"/> that generates embeddings for text search queries.
    /// </summary>
    public sealed class VectorizedSearchWrapper<TRecord>(IVectorizedSearch<TRecord> vectorizedSearch, ITextEmbeddingGenerationService textEmbeddingGeneration) : IVectorizableTextSearch<TRecord>
    {
        /// <inheritdoc/>
        public async Task<VectorSearchResults<TRecord>> VectorizableTextSearchAsync(string searchText, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
        {
            var vectorizedQuery = await textEmbeddingGeneration!.GenerateEmbeddingAsync(searchText, cancellationToken: cancellationToken).ConfigureAwait(false);
            return await vectorizedSearch.VectorizedSearchAsync(vectorizedQuery, options, cancellationToken);
        }
    }

    /// <summary>
    /// Sample model class that represents a record entry.
    /// </summary>
    /// <remarks>
    /// Note that each property is decorated with an attribute that specifies how the property should be treated by the vector store.
    /// This allows us to create a collection in the vector store and upsert and retrieve instances of this class without any further configuration.
    /// </remarks>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    public sealed class DataModel
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public Guid Key { get; init; }

        [VectorStoreRecordData]
        public required string Text { get; init; }

        [VectorStoreRecordData(IsFilterable = true)]
        public required string Tag { get; init; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> Embedding { get; init; }
    }
}
