// Copyright (c) Microsoft. All rights reserved.

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
}