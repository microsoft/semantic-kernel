// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using NRedisStack.RedisStackCommands;
using NRedisStack.Search;
using StackExchange.Redis;
using Xunit;
using Xunit.Abstractions;
using static SemanticKernel.IntegrationTests.Connectors.Memory.Redis.RedisVectorStoreFixture;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Redis;

/// <summary>
/// Contains tests for the <see cref="RedisHashSetVectorStoreRecordCollection{TRecord}"/> class.
/// </summary>
/// <param name="output">Used for logging.</param>
/// <param name="fixture">Redis setup and teardown.</param>
[Collection("RedisVectorStoreCollection")]
public sealed class RedisHashSetVectorStoreRecordCollectionTests(ITestOutputHelper output, RedisVectorStoreFixture fixture)
{
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    // If null, all tests will be enabled
    private const string SkipReason = "Requires Redis docker container up and running";

    private const string TestCollectionName = "hashhotels";

    [Theory(Skip = SkipReason)]
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
    private const string TestCollectionName = "hashhotels";

    [Theory]
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    [InlineData(TestCollectionName, true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange.
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, collectionName);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, collectionName);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, collectionName);
=======
>>>>>>> Stashed changes
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, collectionName);
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, collectionName);
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, collectionName);
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, collectionName);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

        // Act.
        var actual = await sut.CollectionExistsAsync();

        // Assert.
        Assert.Equal(expectedExists, actual);
    }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
<<<<<<< main
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanCreateACollectionUpsertGetAndSearchAsync(bool useRecordDefinition)
    {
        // Arrange
        var record = CreateTestHotel("HUpsert-1", 1);
        var collectionNamePostfix = useRecordDefinition ? "WithDefinition" : "WithType";
        var testCollectionName = $"hashsetcreatetest{collectionNamePostfix}";

        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel>
=======
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    public async Task ItCanCreateACollectionUpsertAndGetAsync(bool useRecordDefinition)
=======
    public async Task ItCanCreateACollectionUpsertGetAndSearchAsync(bool useRecordDefinition)
>>>>>>> upstream/main
    {
        // Arrange
        var record = CreateTestHotel("HUpsert-1", 1);
        var collectionNamePostfix = useRecordDefinition ? "WithDefinition" : "WithType";
        var testCollectionName = $"hashsetcreatetest{collectionNamePostfix}";

<<<<<<< main
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel>
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, testCollectionName, options);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, testCollectionName, options);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, testCollectionName, options);
=======
>>>>>>> Stashed changes
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, testCollectionName, options);
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, testCollectionName, options);
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, testCollectionName, options);
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, testCollectionName, options);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

        // Act
        await sut.CreateCollectionAsync();
        var upsertResult = await sut.UpsertAsync(record);
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var getResult = await sut.GetAsync("Upsert-1", new GetRecordOptions { IncludeVectors = true });
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var getResult = await sut.GetAsync("Upsert-1", new GetRecordOptions { IncludeVectors = true });
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        var getResult = await sut.GetAsync("Upsert-1", new GetRecordOptions { IncludeVectors = true });
=======
>>>>>>> Stashed changes
=======
        var getResult = await sut.GetAsync("Upsert-1", new GetRecordOptions { IncludeVectors = true });
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var getResult = await sut.GetAsync("HUpsert-1", new GetRecordOptions { IncludeVectors = true });
        var searchResult = await sut
            .VectorizedSearchAsync(
                new ReadOnlyMemory<float>(new[] { 30f, 31f, 32f, 33f }),
                new VectorSearchOptions { Filter = new VectorSearchFilter().EqualTo("HotelCode", 1), IncludeVectors = true }).ToListAsync();
=======
        var getResult = await sut.GetAsync("Upsert-1", new GetRecordOptions { IncludeVectors = true });
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var getResult = await sut.GetAsync("HUpsert-1", new GetRecordOptions { IncludeVectors = true });
        var actual = await sut
            .VectorizedSearchAsync(
                new ReadOnlyMemory<float>(new[] { 30f, 31f, 32f, 33f }),
                new VectorSearchOptions { Filter = new VectorSearchFilter().EqualTo("HotelCode", 1), IncludeVectors = true });
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

        // Assert
        var collectionExistResult = await sut.CollectionExistsAsync();
        Assert.True(collectionExistResult);
        await sut.DeleteCollectionAsync();

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Equal("Upsert-1", upsertResult);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Assert.Equal("Upsert-1", upsertResult);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        Assert.Equal("Upsert-1", upsertResult);
=======
>>>>>>> Stashed changes
=======
        Assert.Equal("Upsert-1", upsertResult);
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        Assert.Equal("HUpsert-1", upsertResult);
=======
        Assert.Equal("Upsert-1", upsertResult);
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        Assert.Equal("HUpsert-1", upsertResult);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.HotelCode, getResult?.HotelCode);
        Assert.Equal(record.ParkingIncluded, getResult?.ParkingIncluded);
        Assert.Equal(record.Rating, getResult?.Rating);
        Assert.Equal(record.Description, getResult?.Description);
        Assert.Equal(record.DescriptionEmbedding?.ToArray(), getResult?.DescriptionEmbedding?.ToArray());

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        Assert.Single(searchResult);
        var searchResultRecord = searchResult.First().Record;
=======
        var searchResults = await actual.Results.ToListAsync();
        Assert.Single(searchResults);
        var searchResultRecord = searchResults.First().Record;
>>>>>>> upstream/main
        Assert.Equal(record.HotelId, searchResultRecord?.HotelId);
        Assert.Equal(record.HotelName, searchResultRecord?.HotelName);
        Assert.Equal(record.HotelCode, searchResultRecord?.HotelCode);
        Assert.Equal(record.ParkingIncluded, searchResultRecord?.ParkingIncluded);
        Assert.Equal(record.Rating, searchResultRecord?.Rating);
        Assert.Equal(record.Description, searchResultRecord?.Description);
        Assert.Equal(record.DescriptionEmbedding?.ToArray(), searchResultRecord?.DescriptionEmbedding?.ToArray());

<<<<<<< main
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        // Output
        output.WriteLine(collectionExistResult.ToString());
        output.WriteLine(upsertResult);
        output.WriteLine(getResult?.ToString());
    }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    [Fact(Skip = SkipReason)]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    [Fact(Skip = SkipReason)]
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    [Fact(Skip = SkipReason)]
=======
>>>>>>> Stashed changes
=======
    [Fact(Skip = SkipReason)]
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    [Fact(Skip = SkipReason)]
=======
    [Fact]
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        var tempCollectionName = "temp-test";
        var schema = new Schema();
        schema.AddTextField("HotelName");
        var createParams = new FTCreateParams();
        createParams.AddPrefix(tempCollectionName);
        await fixture.Database.FT().CreateAsync(tempCollectionName, createParams, schema);

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, tempCollectionName);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, tempCollectionName);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, tempCollectionName);
=======
>>>>>>> Stashed changes
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, tempCollectionName);
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, tempCollectionName);
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, tempCollectionName);
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, tempCollectionName);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

        // Act
        await sut.DeleteCollectionAsync();

        // Assert
        Assert.False(await sut.CollectionExistsAsync());
    }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    [Theory(Skip = SkipReason)]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    [Theory(Skip = SkipReason)]
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    [Theory(Skip = SkipReason)]
=======
>>>>>>> Stashed changes
=======
    [Theory(Skip = SkipReason)]
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    [Theory(Skip = SkipReason)]
=======
    [Theory]
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanUpsertDocumentToVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange.
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
>>>>>>> Stashed changes
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel>
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel>
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
        var record = CreateTestHotel("Upsert-2", 2);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
        var record = CreateTestHotel("Upsert-2", 2);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
        var record = CreateTestHotel("Upsert-2", 2);
=======
>>>>>>> Stashed changes
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
        var record = CreateTestHotel("Upsert-2", 2);
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        var record = CreateTestHotel("HUpsert-2", 2);
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
        var record = CreateTestHotel("Upsert-2", 2);
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        var record = CreateTestHotel("HUpsert-2", 2);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

        // Act.
        var upsertResult = await sut.UpsertAsync(record);

        // Assert.
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var getResult = await sut.GetAsync("Upsert-2", new GetRecordOptions { IncludeVectors = true });
        Assert.Equal("Upsert-2", upsertResult);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var getResult = await sut.GetAsync("Upsert-2", new GetRecordOptions { IncludeVectors = true });
        Assert.Equal("Upsert-2", upsertResult);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        var getResult = await sut.GetAsync("Upsert-2", new GetRecordOptions { IncludeVectors = true });
        Assert.Equal("Upsert-2", upsertResult);
=======
>>>>>>> Stashed changes
=======
        var getResult = await sut.GetAsync("Upsert-2", new GetRecordOptions { IncludeVectors = true });
        Assert.Equal("Upsert-2", upsertResult);
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var getResult = await sut.GetAsync("HUpsert-2", new GetRecordOptions { IncludeVectors = true });
        Assert.Equal("HUpsert-2", upsertResult);
=======
        var getResult = await sut.GetAsync("Upsert-2", new GetRecordOptions { IncludeVectors = true });
        Assert.Equal("Upsert-2", upsertResult);
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var getResult = await sut.GetAsync("HUpsert-2", new GetRecordOptions { IncludeVectors = true });
        Assert.Equal("HUpsert-2", upsertResult);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.HotelCode, getResult?.HotelCode);
        Assert.Equal(record.ParkingIncluded, getResult?.ParkingIncluded);
        Assert.Equal(record.Rating, getResult?.Rating);
        Assert.Equal(record.Description, getResult?.Description);
        Assert.Equal(record.DescriptionEmbedding?.ToArray(), getResult?.DescriptionEmbedding?.ToArray());

        // Output.
        output.WriteLine(upsertResult);
        output.WriteLine(getResult?.ToString());
    }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    [Theory(Skip = SkipReason)]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    [Theory(Skip = SkipReason)]
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    [Theory(Skip = SkipReason)]
=======
>>>>>>> Stashed changes
=======
    [Theory(Skip = SkipReason)]
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    [Theory(Skip = SkipReason)]
=======
    [Theory]
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanUpsertManyDocumentsToVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange.
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
>>>>>>> Stashed changes
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel>
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel>
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
=======
>>>>>>> Stashed changes
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

        // Act.
        var results = sut.UpsertBatchAsync(
            [
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                CreateTestHotel("UpsertMany-1", 1),
                CreateTestHotel("UpsertMany-2", 2),
                CreateTestHotel("UpsertMany-3", 3),
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                CreateTestHotel("UpsertMany-1", 1),
                CreateTestHotel("UpsertMany-2", 2),
                CreateTestHotel("UpsertMany-3", 3),
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
                CreateTestHotel("HUpsertMany-1", 1),
                CreateTestHotel("HUpsertMany-2", 2),
                CreateTestHotel("HUpsertMany-3", 3),
=======
                CreateTestHotel("UpsertMany-1", 1),
                CreateTestHotel("UpsertMany-2", 2),
                CreateTestHotel("UpsertMany-3", 3),
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
                CreateTestHotel("HUpsertMany-1", 1),
                CreateTestHotel("HUpsertMany-2", 2),
                CreateTestHotel("HUpsertMany-3", 3),
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
            ]);

        // Assert.
        Assert.NotNull(results);
        var resultsList = await results.ToListAsync();

        Assert.Equal(3, resultsList.Count);
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
        Assert.Contains("UpsertMany-1", resultsList);
        Assert.Contains("UpsertMany-2", resultsList);
        Assert.Contains("UpsertMany-3", resultsList);
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Assert.Contains("UpsertMany-1", resultsList);
        Assert.Contains("UpsertMany-2", resultsList);
        Assert.Contains("UpsertMany-3", resultsList);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        Assert.Contains("HUpsertMany-1", resultsList);
        Assert.Contains("HUpsertMany-2", resultsList);
        Assert.Contains("HUpsertMany-3", resultsList);
=======
        Assert.Contains("UpsertMany-1", resultsList);
        Assert.Contains("UpsertMany-2", resultsList);
        Assert.Contains("UpsertMany-3", resultsList);
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        Assert.Contains("HUpsertMany-1", resultsList);
        Assert.Contains("HUpsertMany-2", resultsList);
        Assert.Contains("HUpsertMany-3", resultsList);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

        // Output
        foreach (var result in resultsList)
        {
            output.WriteLine(result);
        }
    }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    [Theory(Skip = SkipReason)]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    [Theory(Skip = SkipReason)]
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    [Theory(Skip = SkipReason)]
=======
>>>>>>> Stashed changes
=======
    [Theory(Skip = SkipReason)]
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    [Theory(Skip = SkipReason)]
=======
    [Theory]
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task ItCanGetDocumentFromVectorStoreAsync(bool includeVectors, bool useRecordDefinition)
    {
        // Arrange.
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
>>>>>>> Stashed changes
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel>
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel>
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);

        // Act.
        var getResult = await sut.GetAsync("HBaseSet-1", new GetRecordOptions { IncludeVectors = includeVectors });

        // Assert.
        Assert.Equal("HBaseSet-1", getResult?.HotelId);
=======
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
>>>>>>> upstream/main

        // Act.
        var getResult = await sut.GetAsync("HBaseSet-1", new GetRecordOptions { IncludeVectors = includeVectors });

        // Assert.
<<<<<<< main
        Assert.Equal("BaseSet-1", getResult?.HotelId);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        Assert.Equal("HBaseSet-1", getResult?.HotelId);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        Assert.Equal("My Hotel 1", getResult?.HotelName);
        Assert.Equal(1, getResult?.HotelCode);
        Assert.True(getResult?.ParkingIncluded);
        Assert.Equal(3.6, getResult?.Rating);
        Assert.Equal("This is a great hotel.", getResult?.Description);
        if (includeVectors)
        {
            Assert.Equal(new[] { 30f, 31f, 32f, 33f }, getResult?.DescriptionEmbedding?.ToArray());
        }
        else
        {
            Assert.Null(getResult?.DescriptionEmbedding);
        }

        // Output.
        output.WriteLine(getResult?.ToString());
    }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    [Fact(Skip = SkipReason)]
    public async Task ItCanGetManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
<<<<<<< HEAD
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    [Fact(Skip = SkipReason)]
    public async Task ItCanGetManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
<<<<<<< main
<<<<<<< Updated upstream
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
=======
<<<<<<< div
=======
<<<<<<< HEAD
    [Fact(Skip = SkipReason)]
    public async Task ItCanGetManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);

        // Act
        // Also include one non-existing key to test that the operation does not fail for these and returns only the found ones.
        var hotels = sut.GetBatchAsync(["HBaseSet-1", "HBaseSet-5", "HBaseSet-2"], new GetRecordOptions { IncludeVectors = true });
=======
    [Fact]
    public async Task ItCanGetManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);

        // Act
        // Also include one non-existing key to test that the operation does not fail for these and returns only the found ones.
        var hotels = sut.GetBatchAsync(["BaseSet-1", "BaseSet-5", "BaseSet-2"], new GetRecordOptions { IncludeVectors = true });
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);

        // Act
        // Also include one non-existing key to test that the operation does not fail for these and returns only the found ones.
        var hotels = sut.GetBatchAsync(["HBaseSet-1", "HBaseSet-5", "HBaseSet-2"], new GetRecordOptions { IncludeVectors = true });
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

        // Assert
        Assert.NotNull(hotels);
        var hotelsList = await hotels.ToListAsync();
        Assert.Equal(2, hotelsList.Count);

        // Output
        foreach (var hotel in hotelsList)
        {
            output.WriteLine(hotel?.ToString() ?? "Null");
        }
    }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    [Theory(Skip = SkipReason)]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    [Theory(Skip = SkipReason)]
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    [Theory(Skip = SkipReason)]
=======
>>>>>>> Stashed changes
=======
    [Theory(Skip = SkipReason)]
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    [Theory(Skip = SkipReason)]
=======
    [Theory]
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanRemoveDocumentFromVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange.
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
>>>>>>> Stashed changes
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel>
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel>
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        var record = new BasicFloat32Hotel
        {
            HotelId = "HRemove-1",
=======
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        var record = new BasicFloat32Hotel
        {
            HotelId = "HRemove-1",
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
        var record = new BasicHotel
        {
            HotelId = "Remove-1",
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        var record = new BasicFloat32Hotel
        {
            HotelId = "HRemove-1",
>>>>>>> upstream/main
=======
<<<<<<< div
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
>>>>>>> div
            HotelName = "Remove Test Hotel",
            HotelCode = 20,
            Description = "This is a great hotel.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f }
        };

        await sut.UpsertAsync(record);

        // Act.
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        await sut.DeleteAsync("HRemove-1");
        // Also delete a non-existing key to test that the operation does not fail for these.
        await sut.DeleteAsync("HRemove-2");

        // Assert.
        Assert.Null(await sut.GetAsync("HRemove-1"));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanRemoveManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        await sut.UpsertAsync(CreateTestHotel("HRemoveMany-1", 1));
        await sut.UpsertAsync(CreateTestHotel("HRemoveMany-2", 2));
        await sut.UpsertAsync(CreateTestHotel("HRemoveMany-3", 3));

        // Act
        // Also include a non-existing key to test that the operation does not fail for these.
        await sut.DeleteBatchAsync(["HRemoveMany-1", "HRemoveMany-2", "HRemoveMany-3", "HRemoveMany-4"]);

        // Assert
        Assert.Null(await sut.GetAsync("HRemoveMany-1", new GetRecordOptions { IncludeVectors = true }));
        Assert.Null(await sut.GetAsync("HRemoveMany-2", new GetRecordOptions { IncludeVectors = true }));
        Assert.Null(await sut.GetAsync("HRemoveMany-3", new GetRecordOptions { IncludeVectors = true }));
    }

    [Theory(Skip = SkipReason)]
    [InlineData("hotelCode", true)]
    [InlineData("hotelName", false)]
    public async Task ItCanSearchWithFloat32VectorAndFilterAsync(string filterType, bool includeVectors)
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        var vector = new ReadOnlyMemory<float>(new[] { 30f, 31f, 32f, 33f });
        var filter = filterType == "equality" ? new VectorSearchFilter().EqualTo("HotelCode", 1) : new VectorSearchFilter().EqualTo("HotelName", "My Hotel 1");

        // Act
        var actual = await sut.VectorizedSearchAsync(
            vector,
            new VectorSearchOptions
            {
                IncludeVectors = includeVectors,
                Filter = filter
            }).ToListAsync();

        // Assert
        Assert.Single(actual);
        var searchResult = actual.First().Record;
        Assert.Equal("HBaseSet-1", searchResult?.HotelId);
        Assert.Equal("My Hotel 1", searchResult?.HotelName);
        Assert.Equal(1, searchResult?.HotelCode);
        Assert.True(searchResult?.ParkingIncluded);
        Assert.Equal(3.6, searchResult?.Rating);
        Assert.Equal("This is a great hotel.", searchResult?.Description);
        if (includeVectors)
        {
            Assert.Equal(new[] { 30f, 31f, 32f, 33f }, searchResult?.DescriptionEmbedding?.ToArray());
        }
        else
        {
            Assert.Null(searchResult?.DescriptionEmbedding);
        }
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanSearchWithFloat32VectorAndTopSkipAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName + "TopSkip", options);
        await sut.CreateCollectionIfNotExistsAsync();
        await sut.UpsertAsync(new BasicFloat32Hotel { HotelId = "HTopSkip_1", HotelName = "1", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 1.0f]) });
        await sut.UpsertAsync(new BasicFloat32Hotel { HotelId = "HTopSkip_2", HotelName = "2", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 2.0f]) });
        await sut.UpsertAsync(new BasicFloat32Hotel { HotelId = "HTopSkip_3", HotelName = "3", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 3.0f]) });
        await sut.UpsertAsync(new BasicFloat32Hotel { HotelId = "HTopSkip_4", HotelName = "4", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 4.0f]) });
        await sut.UpsertAsync(new BasicFloat32Hotel { HotelId = "HTopSkip_5", HotelName = "5", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 5.0f]) });
        var vector = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 1.0f]);

        // Act
        var actual = await sut.VectorizedSearchAsync(
            vector,
            new VectorSearchOptions
            {
                Top = 3,
                Skip = 2
            }).ToListAsync();

        // Assert
        Assert.Equal(3, actual.Count);
        Assert.True(actual.Select(x => x.Record.HotelId).SequenceEqual(["HTopSkip_3", "HTopSkip_4", "HTopSkip_5"]));
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanSearchWithFloat64VectorAsync(bool includeVectors)
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat64Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat64Hotel>(fixture.Database, TestCollectionName + "Float64", options);
        await sut.CreateCollectionIfNotExistsAsync();
        await sut.UpsertAsync(new BasicFloat64Hotel { HotelId = "HFloat64_1", HotelName = "1", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<double>([1.0d, 1.1d, 1.2d, 1.3d]) });
        await sut.UpsertAsync(new BasicFloat64Hotel { HotelId = "HFloat64_2", HotelName = "2", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<double>([2.0d, 2.1d, 2.2d, 2.3d]) });
        await sut.UpsertAsync(new BasicFloat64Hotel { HotelId = "HFloat64_3", HotelName = "3", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<double>([3.0d, 3.1d, 3.2d, 3.3d]) });

        var vector = new ReadOnlyMemory<double>([2.0d, 2.1d, 2.2d, 2.3d]);

        // Act
        var actual = await sut.VectorizedSearchAsync(
            vector,
            new VectorSearchOptions
            {
                IncludeVectors = includeVectors,
                Top = 1
            }).ToListAsync();

        // Assert
        Assert.Single(actual);
        var searchResult = actual.First().Record;
        Assert.Equal("HFloat64_2", searchResult?.HotelId);
        Assert.Equal("2", searchResult?.HotelName);
        Assert.Equal("Nice hotel", searchResult?.Description);
        if (includeVectors)
        {
            Assert.Equal<double[]>([2.0d, 2.1d, 2.2d, 2.3d], searchResult?.DescriptionEmbedding?.ToArray());
        }
        else
        {
            Assert.Null(searchResult?.DescriptionEmbedding);
        }
    }

    [Fact(Skip = SkipReason)]
    public async Task ItReturnsNullWhenGettingNonExistentRecordAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);

        // Act & Assert
        Assert.Null(await sut.GetAsync("HBaseSet-5", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItThrowsMappingExceptionForFailedMapperAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel>
=======
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        await sut.DeleteAsync("Remove-1");
=======
        await sut.DeleteAsync("HRemove-1");
>>>>>>> upstream/main
        // Also delete a non-existing key to test that the operation does not fail for these.
        await sut.DeleteAsync("HRemove-2");

        // Assert.
        Assert.Null(await sut.GetAsync("HRemove-1"));
    }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    [Fact(Skip = SkipReason)]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    [Fact(Skip = SkipReason)]
=======
    [Fact]
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    [Fact]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
    [Fact]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
    public async Task ItCanRemoveManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        await sut.UpsertAsync(CreateTestHotel("HRemoveMany-1", 1));
        await sut.UpsertAsync(CreateTestHotel("HRemoveMany-2", 2));
        await sut.UpsertAsync(CreateTestHotel("HRemoveMany-3", 3));

        // Act
        // Also include a non-existing key to test that the operation does not fail for these.
        await sut.DeleteBatchAsync(["HRemoveMany-1", "HRemoveMany-2", "HRemoveMany-3", "HRemoveMany-4"]);

        // Assert
        Assert.Null(await sut.GetAsync("HRemoveMany-1", new GetRecordOptions { IncludeVectors = true }));
        Assert.Null(await sut.GetAsync("HRemoveMany-2", new GetRecordOptions { IncludeVectors = true }));
        Assert.Null(await sut.GetAsync("HRemoveMany-3", new GetRecordOptions { IncludeVectors = true }));
    }

    [Theory(Skip = SkipReason)]
    [InlineData("hotelCode", true)]
    [InlineData("hotelName", false)]
    public async Task ItCanSearchWithFloat32VectorAndFilterAsync(string filterType, bool includeVectors)
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        var vector = new ReadOnlyMemory<float>(new[] { 30f, 31f, 32f, 33f });
        var filter = filterType == "equality" ? new VectorSearchFilter().EqualTo("HotelCode", 1) : new VectorSearchFilter().EqualTo("HotelName", "My Hotel 1");

        // Act
        var actual = await sut.VectorizedSearchAsync(
            vector,
            new VectorSearchOptions
            {
                IncludeVectors = includeVectors,
                Filter = filter
            });

        // Assert
        var searchResults = await actual.Results.ToListAsync();
        Assert.Single(searchResults);
        var searchResult = searchResults.First().Record;
        Assert.Equal("HBaseSet-1", searchResult?.HotelId);
        Assert.Equal("My Hotel 1", searchResult?.HotelName);
        Assert.Equal(1, searchResult?.HotelCode);
        Assert.True(searchResult?.ParkingIncluded);
        Assert.Equal(3.6, searchResult?.Rating);
        Assert.Equal("This is a great hotel.", searchResult?.Description);
        if (includeVectors)
        {
            Assert.Equal(new[] { 30f, 31f, 32f, 33f }, searchResult?.DescriptionEmbedding?.ToArray());
        }
        else
        {
            Assert.Null(searchResult?.DescriptionEmbedding);
        }
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanSearchWithFloat32VectorAndTopSkipAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName + "TopSkip", options);
        await sut.CreateCollectionIfNotExistsAsync();
        await sut.UpsertAsync(new BasicFloat32Hotel { HotelId = "HTopSkip_1", HotelName = "1", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 1.0f]) });
        await sut.UpsertAsync(new BasicFloat32Hotel { HotelId = "HTopSkip_2", HotelName = "2", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 2.0f]) });
        await sut.UpsertAsync(new BasicFloat32Hotel { HotelId = "HTopSkip_3", HotelName = "3", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 3.0f]) });
        await sut.UpsertAsync(new BasicFloat32Hotel { HotelId = "HTopSkip_4", HotelName = "4", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 4.0f]) });
        await sut.UpsertAsync(new BasicFloat32Hotel { HotelId = "HTopSkip_5", HotelName = "5", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 5.0f]) });
        var vector = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 1.0f]);

        // Act
        var actual = await sut.VectorizedSearchAsync(
            vector,
            new VectorSearchOptions
            {
                Top = 3,
                Skip = 2
            });

        // Assert
        var searchResults = await actual.Results.ToListAsync();
        Assert.Equal(3, searchResults.Count);
        Assert.True(searchResults.Select(x => x.Record.HotelId).SequenceEqual(["HTopSkip_3", "HTopSkip_4", "HTopSkip_5"]));
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanSearchWithFloat64VectorAsync(bool includeVectors)
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat64Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat64Hotel>(fixture.Database, TestCollectionName + "Float64", options);
        await sut.CreateCollectionIfNotExistsAsync();
        await sut.UpsertAsync(new BasicFloat64Hotel { HotelId = "HFloat64_1", HotelName = "1", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<double>([1.0d, 1.1d, 1.2d, 1.3d]) });
        await sut.UpsertAsync(new BasicFloat64Hotel { HotelId = "HFloat64_2", HotelName = "2", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<double>([2.0d, 2.1d, 2.2d, 2.3d]) });
        await sut.UpsertAsync(new BasicFloat64Hotel { HotelId = "HFloat64_3", HotelName = "3", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<double>([3.0d, 3.1d, 3.2d, 3.3d]) });

        var vector = new ReadOnlyMemory<double>([2.0d, 2.1d, 2.2d, 2.3d]);

        // Act
        var actual = await sut.VectorizedSearchAsync(
            vector,
            new VectorSearchOptions
            {
                IncludeVectors = includeVectors,
                Top = 1
            });

        // Assert
        var searchResults = await actual.Results.ToListAsync();
        Assert.Single(searchResults);
        var searchResult = searchResults.First().Record;
        Assert.Equal("HFloat64_2", searchResult?.HotelId);
        Assert.Equal("2", searchResult?.HotelName);
        Assert.Equal("Nice hotel", searchResult?.Description);
        if (includeVectors)
        {
            Assert.Equal<double[]>([2.0d, 2.1d, 2.2d, 2.3d], searchResult?.DescriptionEmbedding?.ToArray());
        }
        else
        {
            Assert.Null(searchResult?.DescriptionEmbedding);
        }
    }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    [Fact(Skip = SkipReason)]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    [Fact(Skip = SkipReason)]
=======
    [Fact]
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    [Fact]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
    [Fact]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
    public async Task ItReturnsNullWhenGettingNonExistentRecordAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);

        // Act & Assert
        Assert.Null(await sut.GetAsync("HBaseSet-5", new GetRecordOptions { IncludeVectors = true }));
    }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    [Fact(Skip = SkipReason)]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    [Fact(Skip = SkipReason)]
=======
    [Fact]
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    [Fact]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
    [Fact]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
    public async Task ItThrowsMappingExceptionForFailedMapperAsync()
    {
        // Arrange
<<<<<<< main
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicFloat32Hotel>
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            PrefixCollectionNameToKeyNames = true,
            HashEntriesCustomMapper = new FailingMapper()
        };
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreRecordMappingException>(async () => await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true }));
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreRecordMappingException>(async () => await sut.GetAsync("HBaseSet-1", new GetRecordOptions { IncludeVectors = true }));
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicFloat32Hotel>(fixture.Database, TestCollectionName, options);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreRecordMappingException>(async () => await sut.GetAsync("HBaseSet-1", new GetRecordOptions { IncludeVectors = true }));
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertAndRetrieveUsingTheGenericMapperAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<VectorStoreGenericDataModel<string>>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = fixture.BasicVectorStoreRecordDefinition
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<VectorStoreGenericDataModel<string>>(fixture.Database, TestCollectionName, options);

        // Act
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var baseSetGetResult = await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true });
        var upsertResult = await sut.UpsertAsync(new VectorStoreGenericDataModel<string>("GenericMapper-1")
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        var baseSetGetResult = await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true });
        var upsertResult = await sut.UpsertAsync(new VectorStoreGenericDataModel<string>("GenericMapper-1")
=======
        var baseSetGetResult = await sut.GetAsync("HBaseSet-1", new GetRecordOptions { IncludeVectors = true });
        var upsertResult = await sut.UpsertAsync(new VectorStoreGenericDataModel<string>("HGenericMapper-1")
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        var baseSetGetResult = await sut.GetAsync("HBaseSet-1", new GetRecordOptions { IncludeVectors = true });
        var upsertResult = await sut.UpsertAsync(new VectorStoreGenericDataModel<string>("HGenericMapper-1")
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
        var baseSetGetResult = await sut.GetAsync("HBaseSet-1", new GetRecordOptions { IncludeVectors = true });
        var upsertResult = await sut.UpsertAsync(new VectorStoreGenericDataModel<string>("HGenericMapper-1")
>>>>>>> upstream/main
=======
<<<<<<< div
=======
        var baseSetGetResult = await sut.GetAsync("HBaseSet-1", new GetRecordOptions { IncludeVectors = true });
        var upsertResult = await sut.UpsertAsync(new VectorStoreGenericDataModel<string>("HGenericMapper-1")
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
>>>>>>> div
        {
            Data =
            {
                { "HotelName", "Generic Mapper Hotel" },
                { "HotelCode", 40 },
                { "ParkingIncluded", true },
                { "Rating", 3.6d },
                { "Description", "This is a generic mapper hotel" },
            },
            Vectors =
            {
                { "DescriptionEmbedding", new ReadOnlyMemory<float>(new[] { 30f, 31f, 32f, 33f }) }
            }
        });
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        var localGetResult = await sut.GetAsync("GenericMapper-1", new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(baseSetGetResult);
        Assert.Equal("BaseSet-1", baseSetGetResult.Key);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        var localGetResult = await sut.GetAsync("HGenericMapper-1", new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(baseSetGetResult);
        Assert.Equal("HBaseSet-1", baseSetGetResult.Key);
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        var localGetResult = await sut.GetAsync("HGenericMapper-1", new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(baseSetGetResult);
        Assert.Equal("HBaseSet-1", baseSetGetResult.Key);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        Assert.Equal("My Hotel 1", baseSetGetResult.Data["HotelName"]);
        Assert.Equal(1, baseSetGetResult.Data["HotelCode"]);
        Assert.True((bool)baseSetGetResult.Data["ParkingIncluded"]!);
        Assert.Equal(3.6d, baseSetGetResult.Data["Rating"]);
        Assert.Equal("This is a great hotel.", baseSetGetResult.Data["Description"]);
        Assert.NotNull(baseSetGetResult.Vectors["DescriptionEmbedding"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)baseSetGetResult.Vectors["DescriptionEmbedding"]!).ToArray());

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        Assert.Equal("GenericMapper-1", upsertResult);

        Assert.NotNull(localGetResult);
        Assert.Equal("GenericMapper-1", localGetResult.Key);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
        Assert.Equal("HGenericMapper-1", upsertResult);

        Assert.NotNull(localGetResult);
        Assert.Equal("HGenericMapper-1", localGetResult.Key);
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        Assert.Equal("HGenericMapper-1", upsertResult);

        Assert.NotNull(localGetResult);
        Assert.Equal("HGenericMapper-1", localGetResult.Key);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        Assert.Equal("Generic Mapper Hotel", localGetResult.Data["HotelName"]);
        Assert.Equal(40, localGetResult.Data["HotelCode"]);
        Assert.True((bool)localGetResult.Data["ParkingIncluded"]!);
        Assert.Equal(3.6d, localGetResult.Data["Rating"]);
        Assert.Equal("This is a generic mapper hotel", localGetResult.Data["Description"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)localGetResult.Vectors["DescriptionEmbedding"]!).ToArray());
    }

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    private static BasicHotel CreateTestHotel(string hotelId, int hotelCode)
    {
        var record = new BasicHotel
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    private static BasicHotel CreateTestHotel(string hotelId, int hotelCode)
    {
        var record = new BasicHotel
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    private static BasicFloat32Hotel CreateTestHotel(string hotelId, int hotelCode)
    {
        var record = new BasicFloat32Hotel
=======
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreRecordMappingException>(async () => await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true }));
    }

    private static BasicHotel CreateTestHotel(string hotelId, int hotelCode)
    {
        var record = new BasicHotel
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
    private static BasicFloat32Hotel CreateTestHotel(string hotelId, int hotelCode)
    {
        var record = new BasicFloat32Hotel
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            HotelId = hotelId,
            HotelName = $"My Hotel {hotelCode}",
            HotelCode = 1,
            ParkingIncluded = true,
            Rating = 3.6,
            Description = "This is a great hotel.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f }
        };
        return record;
    }

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    private sealed class FailingMapper : IVectorStoreRecordMapper<BasicHotel, (string Key, HashEntry[] HashEntries)>
    {
        public (string Key, HashEntry[] HashEntries) MapFromDataToStorageModel(BasicHotel dataModel)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    private sealed class FailingMapper : IVectorStoreRecordMapper<BasicHotel, (string Key, HashEntry[] HashEntries)>
    {
        public (string Key, HashEntry[] HashEntries) MapFromDataToStorageModel(BasicHotel dataModel)
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    private sealed class FailingMapper : IVectorStoreRecordMapper<BasicFloat32Hotel, (string Key, HashEntry[] HashEntries)>
    {
        public (string Key, HashEntry[] HashEntries) MapFromDataToStorageModel(BasicFloat32Hotel dataModel)
=======
    private sealed class FailingMapper : IVectorStoreRecordMapper<BasicHotel, (string Key, HashEntry[] HashEntries)>
    {
        public (string Key, HashEntry[] HashEntries) MapFromDataToStorageModel(BasicHotel dataModel)
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
    private sealed class FailingMapper : IVectorStoreRecordMapper<BasicFloat32Hotel, (string Key, HashEntry[] HashEntries)>
    {
        public (string Key, HashEntry[] HashEntries) MapFromDataToStorageModel(BasicFloat32Hotel dataModel)
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            throw new NotImplementedException();
        }

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        public BasicHotel MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, StorageToDataModelMapperOptions options)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        public BasicHotel MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, StorageToDataModelMapperOptions options)
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        public BasicHotel MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, StorageToDataModelMapperOptions options)
=======
>>>>>>> Stashed changes
=======
        public BasicHotel MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, StorageToDataModelMapperOptions options)
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        public BasicFloat32Hotel MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, StorageToDataModelMapperOptions options)
=======
        public BasicHotel MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, StorageToDataModelMapperOptions options)
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        public BasicFloat32Hotel MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, StorageToDataModelMapperOptions options)
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            throw new NotImplementedException();
        }
    }
}
