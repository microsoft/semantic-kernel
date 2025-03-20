// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Driver;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Integration tests of <see cref="AzureCosmosDBNoSQLMemoryStore"/>.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class AzureCosmosDBNoSQLMemoryStoreTests : IClassFixture<AzureCosmosDBNoSQLMemoryStoreTestsFixture>
{
    private const string? SkipReason = "Azure Cosmos DB Account with Vector indexing enabled required";

    private readonly AzureCosmosDBNoSQLMemoryStoreTestsFixture _fixture;

    public AzureCosmosDBNoSQLMemoryStoreTests(AzureCosmosDBNoSQLMemoryStoreTestsFixture fixture)
    {
        this._fixture = fixture;
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateGetCheckAndDeleteCollectionAsync()
    {
        var collectionName = this._fixture.CollectionName;
        var memoryStore = this._fixture.MemoryStore;

        await memoryStore.CreateCollectionAsync(collectionName);
        var collectionNames = memoryStore.GetCollectionsAsync();

        Assert.True(await collectionNames.ContainsAsync(collectionName));
        Assert.True(await memoryStore.DoesCollectionExistAsync(collectionName));

        await memoryStore.DeleteCollectionAsync(collectionName);
        Assert.False(await memoryStore.DoesCollectionExistAsync(collectionName));
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanBatchUpsertGetRemoveAsync(bool withEmbeddings)
    {
        const int Count = 10;
        var collectionName = this._fixture.CollectionName;
        var memoryStore = this._fixture.MemoryStore;
        var records = DataHelper.CreateBatchRecords(Count);

        await memoryStore.CreateCollectionAsync(collectionName);
        var keys = await memoryStore.UpsertBatchAsync(collectionName, records).ToListAsync();
        var actualRecords = await memoryStore
            .GetBatchAsync(collectionName, keys, withEmbeddings: withEmbeddings)
            .ToListAsync();

        Assert.NotNull(keys);
        Assert.NotNull(actualRecords);
        Assert.Equal(keys, actualRecords.Select(obj => obj.Key).ToList());
        Console.WriteLine(actualRecords);

        var actualRecordsOrdered = actualRecords.OrderBy(r => r.Key).ToArray();
        for (int i = 0; i < Count; i++)
        {
            AssertMemoryRecordEqual(
                records[i],
                actualRecordsOrdered[i],
                assertEmbeddingEqual: withEmbeddings
            );
        }

        await memoryStore.RemoveBatchAsync(collectionName, keys);
        var ids = await memoryStore.GetBatchAsync(collectionName, keys).ToListAsync();
        Assert.Empty(ids);

        await memoryStore.DeleteCollectionAsync(collectionName);
    }

    [Theory(Skip = SkipReason)]
    [InlineData(1, false)]
    [InlineData(1, true)]
    [InlineData(5, false)]
    [InlineData(8, false)]
    public async Task ItCanGetNearestMatchesAsync(int limit, bool withEmbeddings)
    {
        var collectionName = this._fixture.CollectionName;
        var memoryStore = this._fixture.MemoryStore;
        var searchEmbedding = DataHelper.VectorSearchTestEmbedding;
        var nearestMatchesExpected = DataHelper.VectorSearchExpectedResults;

        await memoryStore.CreateCollectionAsync(collectionName);
        var keys = await memoryStore.UpsertBatchAsync(collectionName, DataHelper.VectorSearchTestRecords).ToListAsync();

        var nearestMatchesActual = await memoryStore
            .GetNearestMatchesAsync(
                collectionName,
                searchEmbedding,
                limit,
                withEmbeddings: withEmbeddings
            )
            .ToListAsync();

        Assert.NotNull(nearestMatchesActual);
        Assert.Equal(limit, nearestMatchesActual.Count);

        for (int i = 0; i < limit; i++)
        {
            AssertMemoryRecordEqual(
                nearestMatchesExpected[i],
                nearestMatchesActual[i].Item1,
                withEmbeddings
            );
        }

        await memoryStore.DeleteCollectionAsync(collectionName);
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanSaveReferenceGetTextAndSearchTextAsync(bool withEmbedding)
    {
        var collectionName = this._fixture.CollectionName;
        var memoryStore = this._fixture.MemoryStore;
        var textMemory = new SemanticTextMemory(memoryStore, new MockTextEmbeddingGenerationService());
        var textToStore = "SampleText";
        var id = "MyExternalId";
        var source = "MyExternalSource";
        var refId = await textMemory.SaveReferenceAsync(collectionName, textToStore, id, source);
        Assert.NotNull(refId);

        var expectedQueryResult = new MemoryQueryResult(
            new MemoryRecordMetadata(isReference: true, id, text: "", description: "", source, additionalMetadata: ""),
            1.0,
            withEmbedding ? DataHelper.VectorSearchTestEmbedding : null);

        var queryResult = await textMemory.GetAsync(collectionName, refId, withEmbedding);
        AssertQueryResultEqual(expectedQueryResult, queryResult, withEmbedding);

        var searchResults = await textMemory.SearchAsync(collectionName, textToStore, withEmbeddings: withEmbedding).ToListAsync();
        Assert.Equal(1, searchResults?.Count);
        AssertQueryResultEqual(expectedQueryResult, searchResults?[0], compareEmbeddings: true);

        await textMemory.RemoveAsync(collectionName, refId);
    }

    private static void AssertQueryResultEqual(MemoryQueryResult expected, MemoryQueryResult? actual, bool compareEmbeddings)
    {
        Assert.NotNull(actual);
        Assert.Equal(expected.Relevance, actual.Relevance);
        Assert.Equal(expected.Metadata.Id, actual.Metadata.Id);
        Assert.Equal(expected.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(expected.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(expected.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(expected.Metadata.AdditionalMetadata, actual.Metadata.AdditionalMetadata);
        Assert.Equal(expected.Metadata.IsReference, actual.Metadata.IsReference);

        if (compareEmbeddings)
        {
            Assert.NotNull(expected.Embedding);
            Assert.NotNull(actual.Embedding);
            Assert.Equal(expected.Embedding.Value.Span, actual.Embedding.Value.Span);
        }
    }

    private static void AssertMemoryRecordEqual(
        MemoryRecord expectedRecord,
        MemoryRecord actualRecord,
        bool assertEmbeddingEqual = true
    )
    {
        Assert.Equal(expectedRecord.Key, actualRecord.Key);
        Assert.Equal(expectedRecord.Timestamp, actualRecord.Timestamp);
        Assert.Equal(expectedRecord.Metadata.Id, actualRecord.Metadata.Id);
        Assert.Equal(expectedRecord.Metadata.Text, actualRecord.Metadata.Text);
        Assert.Equal(expectedRecord.Metadata.Description, actualRecord.Metadata.Description);
        Assert.Equal(
            expectedRecord.Metadata.AdditionalMetadata,
            actualRecord.Metadata.AdditionalMetadata
        );
        Assert.Equal(expectedRecord.Metadata.IsReference, actualRecord.Metadata.IsReference);
        Assert.Equal(
            expectedRecord.Metadata.ExternalSourceName,
            actualRecord.Metadata.ExternalSourceName
        );

        if (assertEmbeddingEqual)
        {
            Assert.True(expectedRecord.Embedding.Span.SequenceEqual(actualRecord.Embedding.Span));
        }
        else
        {
            Assert.True(actualRecord.Embedding.Span.IsEmpty);
        }
    }

    private sealed class MockTextEmbeddingGenerationService : ITextEmbeddingGenerationService
    {
        public IReadOnlyDictionary<string, object?> Attributes { get; } = ReadOnlyDictionary<string, object?>.Empty;

        public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            IList<ReadOnlyMemory<float>> result = new List<ReadOnlyMemory<float>> { DataHelper.VectorSearchTestEmbedding };
            return Task.FromResult(result);
        }
    }
}
