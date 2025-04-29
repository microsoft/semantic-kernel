// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
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
    [Obsolete("VectorStoreTextSearch with ITextEmbeddingGenerationService is obsolete")]
    public static async Task<VectorStoreTextSearch<DataModelWithRawEmbedding>> CreateVectorStoreTextSearchWithEmbeddingGenerationServiceAsync()
    {
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModelWithRawEmbedding>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();
        using var embeddingService = new MockTextEmbeddingGenerator();
        await AddRecordsAsync(vectorSearch, embeddingService);
        var sut = new VectorStoreTextSearch<DataModelWithRawEmbedding>(vectorSearch, embeddingService, stringMapper, resultMapper);
        return sut;
    }

    /// <summary>
    /// Create a <see cref="VectorStoreTextSearch{TRecord}"/> from a <see cref="IVectorizedSearch{TRecord}"/>.
    /// </summary>
    public static async Task<VectorStoreTextSearch<DataModel>> CreateVectorStoreTextSearchAsync()
    {
        using var embeddingGenerator = new MockTextEmbeddingGenerator();
        var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = embeddingGenerator });
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();
        await AddRecordsAsync(vectorSearch);
        var sut = new VectorStoreTextSearch<DataModel>(vectorSearch, stringMapper, resultMapper);
        return sut;
    }

    /// <summary>
    /// Add sample records to the vector store record collection.
    /// </summary>
    public static async Task AddRecordsAsync(
        IVectorStoreRecordCollection<Guid, DataModel> recordCollection,
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
                Embedding = $"Record {i}"
            };
            await recordCollection.UpsertAsync(dataModel);
        }
    }

    /// <summary>
    /// Add sample records to the vector store record collection.
    /// </summary>
    public static async Task AddRecordsAsync(
        IVectorStoreRecordCollection<Guid, DataModelWithRawEmbedding> recordCollection,
        ITextEmbeddingGenerationService embeddingService,
        int? count = 10)
    {
        await recordCollection.CreateCollectionIfNotExistsAsync();
        for (var i = 0; i < count; i++)
        {
            DataModelWithRawEmbedding dataModel = new()
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
            => result switch
            {
                DataModel dataModel => dataModel.Text,
                DataModelWithRawEmbedding dataModelWithRawEmbedding => dataModelWithRawEmbedding.Text,
                _ => throw new ArgumentException("Invalid result type.")
            };
    }

    /// <summary>
    /// Result mapper which converts a DataModel to a TextSearchResult.
    /// </summary>
    public sealed class DataModelTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
            => result switch
            {
                DataModel dataModel => new TextSearchResult(value: dataModel.Text) { Name = dataModel.Key.ToString() },
                DataModelWithRawEmbedding dataModelWithRawEmbedding => new TextSearchResult(value: dataModelWithRawEmbedding.Text) { Name = dataModelWithRawEmbedding.Key.ToString() },
                _ => throw new ArgumentException("Invalid result type.")
            };
    }

    /// <summary>
    /// Mock implementation of <see cref="ITextEmbeddingGenerationService"/>.
    /// </summary>
    public sealed class MockTextEmbeddingGenerator : IEmbeddingGenerator<string, Embedding<float>>, ITextEmbeddingGenerationService
    {
        public Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(IEnumerable<string> values, EmbeddingGenerationOptions? options = null, CancellationToken cancellationToken = default)
            => Task.FromResult(new GeneratedEmbeddings<Embedding<float>>([new(new float[] { 0, 1, 2, 3 })]));

        public void Dispose() { }

        public object? GetService(Type serviceType, object? serviceKey = null) => null;

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

        [VectorStoreRecordData(IsIndexed = true)]
        public required string Tag { get; init; }

        [VectorStoreRecordVector(1536)]
        public string? Embedding { get; init; }
    }

    /// <summary>
    /// Sample model class that represents a record entry.
    /// </summary>
    /// <remarks>
    /// Note that each property is decorated with an attribute that specifies how the property should be treated by the vector store.
    /// This allows us to create a collection in the vector store and upsert and retrieve instances of this class without any further configuration.
    /// </remarks>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    public sealed class DataModelWithRawEmbedding
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public Guid Key { get; init; }

        [VectorStoreRecordData]
        public required string Text { get; init; }

        [VectorStoreRecordData(IsIndexed = true)]
        public required string Tag { get; init; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> Embedding { get; init; }
    }
}
