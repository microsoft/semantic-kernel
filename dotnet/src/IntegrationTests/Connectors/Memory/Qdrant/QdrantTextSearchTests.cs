﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Data;
using SemanticKernel.IntegrationTests.Data;
using Xunit;
using static SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant.QdrantVectorStoreFixture;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant;

/// <summary>
/// Integration tests for using <see cref="QdrantVectorStore"/> with <see cref="ITextSearch"/>.
/// </summary>
[Collection("QdrantVectorStoreCollection")]
public class QdrantTextSearchTests(QdrantVectorStoreFixture fixture) : BaseVectorStoreTextSearchTests
{
    // If null, all tests will be enabled
    private const string SkipReason = "Failing in integration test pipeline so disabling while investigating a fix (Issue 9168)";

    [Fact(Skip = SkipReason)]
    public override async Task CanSearchAsync()
    {
        await base.CanSearchAsync();
    }

    [Fact(Skip = SkipReason)]
    public override async Task CanGetTextSearchResultsAsync()
    {
        await base.CanGetTextSearchResultsAsync();
    }

    [Fact(Skip = SkipReason)]
    public override async Task CanGetSearchResultsAsync()
    {
        await base.CanGetSearchResultsAsync();
    }

    [Fact(Skip = SkipReason)]
    public override async Task UsingTextSearchWithAFilterAsync()
    {
        await base.UsingTextSearchWithAFilterAsync();
    }

    [Fact(Skip = SkipReason)]
    public override async Task FunctionCallingUsingCreateWithSearchAsync()
    {
        await base.FunctionCallingUsingCreateWithSearchAsync();
    }

    [Fact(Skip = SkipReason)]
    public override async Task FunctionCallingUsingCreateWithGetSearchResultsAsync()
    {
        await base.FunctionCallingUsingCreateWithGetSearchResultsAsync();
    }

    [Fact(Skip = SkipReason)]
    public override async Task FunctionCallingUsingGetTextSearchResultsAsync()
    {
        await base.FunctionCallingUsingGetTextSearchResultsAsync();
    }

    /// <inheritdoc/>
    public override Task<ITextSearch> CreateTextSearchAsync()
    {
        if (this.VectorStore is null)
        {
            this.EmbeddingGenerator = fixture.EmbeddingGenerator;
            this.VectorStore = new QdrantVectorStore(fixture.QdrantClient);
        }

        var options = new QdrantVectorStoreRecordCollectionOptions<HotelInfo>
        {
            HasNamedVectors = true,
            VectorStoreRecordDefinition = fixture.HotelVectorStoreRecordDefinition,
        };
        var vectorSearch = new QdrantVectorStoreRecordCollection<HotelInfo>(fixture.QdrantClient, "namedVectorsHotels", options);
        var stringMapper = new HotelInfoTextSearchStringMapper();
        var resultMapper = new HotelInfoTextSearchResultMapper();

        var result = new VectorStoreTextSearch<HotelInfo>(vectorSearch, this.EmbeddingGenerator!, stringMapper, resultMapper);
        return Task.FromResult<ITextSearch>(result);
    }

    /// <inheritdoc/>
    public override string GetQuery() => "Find a great hotel";

    /// <inheritdoc/>
    public override TextSearchFilter GetTextSearchFilter() => new TextSearchFilter().Equality("HotelName", "My Hotel 11");

    /// <inheritdoc/>
    public override bool VerifySearchResults(object[] results, string query, TextSearchFilter? filter = null)
    {
        Assert.NotNull(results);
        Assert.NotEmpty(results);
        Assert.Equal(filter is null ? 4 : 1, results.Length);
        foreach (var result in results)
        {
            Assert.NotNull(result);
            Assert.IsType<HotelInfo>(result);
        }

        return true;
    }

    /// <summary>
    /// String mapper which converts a Hotel to a string.
    /// </summary>
    protected sealed class HotelInfoTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            if (result is HotelInfo hotel)
            {
                return $"{hotel.HotelName} {hotel.Description}";
            }
            throw new ArgumentException("Invalid result type.");
        }
    }

    /// <summary>
    /// Result mapper which converts a Hotel to a TextSearchResult.
    /// </summary>
    protected sealed class HotelInfoTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is HotelInfo hotel)
            {
                return new TextSearchResult(value: hotel.Description) { Name = hotel.HotelName, Link = $"id://{hotel.HotelId}" };
            }
            throw new ArgumentException("Invalid result type.");
        }
    }
}
