// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // ITextSearch is obsolete

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
    /// <inheritdoc/>
    public override Task<ITextSearch> CreateTextSearchAsync()
    {
        if (this.VectorStore is null)
        {
            this.EmbeddingGenerator = fixture.EmbeddingGenerator;
            this.VectorStore = new QdrantVectorStore(fixture.QdrantClient, ownsClient: false, new QdrantVectorStoreOptions { EmbeddingGenerator = fixture.EmbeddingGenerator });
        }

        var options = new QdrantCollectionOptions
        {
            HasNamedVectors = true,
            Definition = fixture.HotelVectorStoreRecordDefinition,
        };
        using var collection = new QdrantCollection<ulong, HotelInfo>(fixture.QdrantClient, "namedVectorsHotels", ownsClient: false, options);
        var stringMapper = new HotelInfoTextSearchStringMapper();
        var resultMapper = new HotelInfoTextSearchResultMapper();

        var result = new VectorStoreTextSearch<HotelInfo>(collection, this.EmbeddingGenerator!, stringMapper, resultMapper);

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
