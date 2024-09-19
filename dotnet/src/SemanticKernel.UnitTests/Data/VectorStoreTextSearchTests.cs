// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;

namespace SemanticKernel.UnitTests.Data;
public class VectorStoreTextSearchTests
{
    [Fact]
    public void CanCreateVectorStoreTextSearchWithIVectorizedSearch()
    {
        // Arrange.
        var vectorStore = new VolatileVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();

        // Act.
        var sut = new VectorStoreTextSearch<DataModel>(vectorSearch, new MockTextEmbeddingGenerationService(), stringMapper, resultMapper);

        // Assert.
        Assert.NotNull(sut);
    }

    [Fact]
    public void CanCreateVectorStoreTextSearchWithIVectorizableTextSearch()
    {
        // Arrange.
        var vectorStore = new VolatileVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var vectorizableTextSearch = new VectorizedSearchWrapper<DataModel>(vectorSearch, new MockTextEmbeddingGenerationService());
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();

        // Act.
        var sut = new VectorStoreTextSearch<DataModel>(vectorizableTextSearch, stringMapper, resultMapper);

        // Assert.
        Assert.NotNull(sut);
    }

    [Fact]
    public async Task CanSearchWithVectorizedSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizedSearchAsync();

        // Act.
        KernelSearchResults<string> searchResults = await sut.SearchAsync("What is the Semantic Kernel?", new() { Count = 2, Offset = 0 });
        var results = await ToListAsync(searchResults.Results);

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetTextSearchResultsWithVectorizedSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizedSearchAsync();

        // Act.
        KernelSearchResults<TextSearchResult> searchResults = await sut.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Count = 2, Offset = 0 });
        var results = await ToListAsync(searchResults.Results);

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetSearchResultsWithVectorizedSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizedSearchAsync();

        // Act.
        KernelSearchResults<object> searchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new() { Count = 2, Offset = 0 });
        var results = await ToListAsync(searchResults.Results);

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanSearchWithVectorizableTextSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizableTextSearchAsync();

        // Act.
        KernelSearchResults<string> searchResults = await sut.SearchAsync("What is the Semantic Kernel?", new() { Count = 2, Offset = 0 });
        var results = await ToListAsync(searchResults.Results);

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetTextSearchResultsWithVectorizableTextSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizableTextSearchAsync();

        // Act.
        KernelSearchResults<TextSearchResult> searchResults = await sut.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Count = 2, Offset = 0 });
        var results = await ToListAsync(searchResults.Results);

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetSearchResultsWithVectorizableTextSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizableTextSearchAsync();

        // Act.
        KernelSearchResults<object> searchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new() { Count = 2, Offset = 0 });
        var results = await ToListAsync(searchResults.Results);

        Assert.Equal(2, results.Count);
    }

    /// <summary>
    /// Create a <see cref="VectorStoreTextSearch{TRecord}"/> from a <see cref="IVectorizedSearch{TRecord}"/>.
    /// </summary>
    private static async Task<VectorStoreTextSearch<DataModel>> CreateVectorStoreTextSearchFromVectorizedSearchAsync()
    {
        var vectorStore = new VolatileVectorStore();
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
    private static async Task<VectorStoreTextSearch<DataModel>> CreateVectorStoreTextSearchFromVectorizableTextSearchAsync()
    {
        var vectorStore = new VolatileVectorStore();
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
    /// Convert an <see cref="IAsyncEnumerable{T}"/> to a <see cref="List{T}"/>.
    /// </summary>
    private static async ValueTask<List<T>> ToListAsync<T>(IAsyncEnumerable<T> source, CancellationToken cancellationToken = default)
    {
        var result = new List<T>();

        await foreach (var item in source.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            result.Add(item);
        }

        return result;
    }

    /// <summary>
    /// Add sample records to the vector store record collection.
    /// </summary>
    private static async Task AddRecordsAsync(
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
                Embedding = await embeddingService.GenerateEmbeddingAsync($"Record {i}")
            };
            await recordCollection.UpsertAsync(dataModel);
        }
    }

    /// <summary>
    /// String mapper which converts a DataModel to a string.
    /// </summary>
    private sealed class DataModelTextSearchStringMapper : ITextSearchStringMapper
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
    private sealed class DataModelTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is DataModel dataModel)
            {
                return new TextSearchResult(name: dataModel.Key.ToString(), value: dataModel.Text);
            }
            throw new ArgumentException("Invalid result type.");
        }
    }

    /// <summary>
    /// Mock implementation of <see cref="ITextEmbeddingGenerationService"/>.
    /// </summary>
    private sealed class MockTextEmbeddingGenerationService : ITextEmbeddingGenerationService
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
    private sealed class VectorizedSearchWrapper<TRecord>(IVectorizedSearch<TRecord> vectorizedSearch, ITextEmbeddingGenerationService textEmbeddingGeneration) : IVectorizableTextSearch<TRecord>
        where TRecord : class
    {
        /// <inheritdoc/>
        public async IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizableTextSearchAsync(string searchText, VectorSearchOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            var vectorizedQuery = await textEmbeddingGeneration!.GenerateEmbeddingAsync(searchText, cancellationToken: cancellationToken).ConfigureAwait(false);

            await foreach (var result in vectorizedSearch.VectorizedSearchAsync(vectorizedQuery, options, cancellationToken))
            {
                yield return result;
            }
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
    private sealed class DataModel
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public Guid Key { get; init; }

        [VectorStoreRecordData]
        public required string Text { get; init; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> Embedding { get; init; }
    }
}
