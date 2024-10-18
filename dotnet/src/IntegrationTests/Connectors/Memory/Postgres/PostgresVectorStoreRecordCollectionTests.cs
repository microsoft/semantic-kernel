// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Postgres;

[Collection("PostgresVectorStoreCollection")]
public sealed class PostgresVectorStoreRecordCollectionTests(PostgresVectorStoreFixture fixture)
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(bool createCollection)
    {
        // Arrange
        var sut = fixture.GetCollection<int, PostgresHotel>("CollectionExists");

        if (createCollection)
        {
            await sut.CreateCollectionAsync();
        }

        try
        {
            // Act
            var collectionExists = await sut.CollectionExistsAsync();

            // Assert
            Assert.Equal(createCollection, collectionExists);
        }
        finally
        {
            // Cleanup
            if (createCollection)
            {
                await sut.DeleteCollectionAsync();
            }
        }
    }

    [Fact]
    public async Task CollectionCanUpsertAndGetAsync()
    {
        // Arrange
        var sut = fixture.GetCollection<int, PostgresHotel>("CollectionCanUpsertAndGet");
        if (await sut.CollectionExistsAsync())
        {
            await sut.DeleteCollectionAsync();
        }

        await sut.CreateCollectionAsync();

        try
        {
            // Act
            await sut.UpsertAsync(new PostgresHotel { HotelId = 1, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"] });
            await sut.UpsertAsync(new PostgresHotel { HotelId = 2, HotelName = "Hotel 2", HotelCode = 2, ParkingIncluded = false, HotelRating = 2.5f, ListInts = [1, 2] });

            var hotel1 = await sut.GetAsync(1);
            var hotel2 = await sut.GetAsync(2);

            // Assert
            Assert.NotNull(hotel1);
            Assert.Equal(1, hotel1!.HotelId);
            Assert.Equal("Hotel 1", hotel1!.HotelName);
            Assert.Equal(1, hotel1!.HotelCode);
            Assert.True(hotel1!.ParkingIncluded);
            Assert.Equal(4.5f, hotel1!.HotelRating);
            Assert.NotNull(hotel1!.Tags);
            Assert.Equal(2, hotel1!.Tags!.Count);
            Assert.Equal("tag1", hotel1!.Tags![0]);
            Assert.Equal("tag2", hotel1!.Tags![1]);
            Assert.Null(hotel1!.ListInts);

            Assert.NotNull(hotel2);
            Assert.Equal(2, hotel2!.HotelId);
            Assert.Equal("Hotel 2", hotel2!.HotelName);
            Assert.Equal(2, hotel2!.HotelCode);
            Assert.False(hotel2!.ParkingIncluded);
            Assert.Equal(2.5f, hotel2!.HotelRating);
            Assert.NotNull(hotel2!.Tags);
            Assert.Empty(hotel2!.Tags);
            Assert.NotNull(hotel2!.ListInts);
            Assert.Equal(2, hotel2!.ListInts!.Count);
            Assert.Equal(1, hotel2!.ListInts![0]);
            Assert.Equal(2, hotel2!.ListInts![1]);
        }
        finally
        {
            // Cleanup
            await sut.DeleteCollectionAsync();
        }
    }

    [Fact]
    public async Task ItCanGetAndDeleteRecordAsync()
    {
        // Arrange
        const int HotelId = 5;
        var sut = fixture.GetCollection<int, PostgresHotel>("DeleteRecord");

        await sut.CreateCollectionAsync();

        try
        {
            var record = new PostgresHotel { HotelId = HotelId, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"] };

            var upsertResult = await sut.UpsertAsync(record);
            var getResult = await sut.GetAsync(HotelId);

            Assert.Equal(HotelId, upsertResult);
            Assert.NotNull(getResult);

            // Act
            await sut.DeleteAsync(HotelId);

            getResult = await sut.GetAsync(HotelId);

            // Assert
            Assert.Null(getResult);
        }
        finally
        {
            // Cleanup
            await sut.DeleteCollectionAsync();
        }
    }

    [Fact]
    public async Task ItCanGetUpsertDeleteBatchAsync()
    {
        // Arrange
        const int HotelId1 = 1;
        const int HotelId2 = 2;
        const int HotelId3 = 3;

        var sut = fixture.GetCollection<int, PostgresHotel>("GetUpsertDeleteBatch");

        await sut.CreateCollectionAsync();

        var record1 = new PostgresHotel { HotelId = HotelId1, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"] };
        var record2 = new PostgresHotel { HotelId = HotelId2, HotelName = "Hotel 2", HotelCode = 1, ParkingIncluded = false, HotelRating = 3.5f, Tags = ["tag1", "tag3"] };
        var record3 = new PostgresHotel { HotelId = HotelId3, HotelName = "Hotel 3", HotelCode = 1, ParkingIncluded = true, HotelRating = 2.5f, Tags = ["tag1", "tag4"] };

        var upsertResults = await sut.UpsertBatchAsync([record1, record2, record3]).ToListAsync();
        var getResults = await sut.GetBatchAsync([HotelId1, HotelId2, HotelId3]).ToListAsync();

        Assert.Equal([HotelId1, HotelId2, HotelId3], upsertResults);

        Assert.NotNull(getResults.First(l => l.HotelId == HotelId1));
        Assert.NotNull(getResults.First(l => l.HotelId == HotelId2));
        Assert.NotNull(getResults.First(l => l.HotelId == HotelId3));

        // Act
        await sut.DeleteBatchAsync([HotelId1, HotelId2, HotelId3]);

        getResults = await sut.GetBatchAsync([HotelId1, HotelId2, HotelId3]).ToListAsync();

        // Assert
        Assert.Empty(getResults);
    }
}