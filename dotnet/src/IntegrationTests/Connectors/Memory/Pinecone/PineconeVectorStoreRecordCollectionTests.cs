// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Grpc.Core;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Pinecone;
using SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone.Xunit;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

[Collection("PineconeVectorStoreTests")]
[PineconeApiKeySetCondition]
public class PineconeVectorStoreRecordCollectionTests(PineconeVectorStoreFixture fixture) : IClassFixture<PineconeVectorStoreFixture>
{
    private PineconeVectorStoreFixture Fixture { get; } = fixture;

    [VectorStoreFact]
    public async Task TryCreateExistingIndexIsNoopAsync()
    {
        await this.Fixture.HotelRecordCollection.CreateCollectionIfNotExistsAsync();
    }

    [VectorStoreFact]
    public async Task CollectionExistsReturnsTrueForExistingCollectionAsync()
    {
        var result = await this.Fixture.HotelRecordCollection.CollectionExistsAsync();

        Assert.True(result);
    }

    [VectorStoreTheory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task BasicGetAsync(bool includeVectors)
    {
        var fiveSeasons = await this.Fixture.HotelRecordCollection.GetAsync("five-seasons", new GetRecordOptions { IncludeVectors = includeVectors });

        Assert.NotNull(fiveSeasons);
        Assert.Equal("five-seasons", fiveSeasons.HotelId);
        Assert.Equal("Five Seasons Hotel", fiveSeasons.HotelName);
        Assert.Equal("Great service any season.", fiveSeasons.Description);
        Assert.Equal(7, fiveSeasons.HotelCode);
        Assert.Equal(4.5f, fiveSeasons.HotelRating);
        Assert.True(fiveSeasons.ParkingIncluded);
        Assert.Contains("wi-fi", fiveSeasons.Tags);
        Assert.Contains("sauna", fiveSeasons.Tags);
        Assert.Contains("gym", fiveSeasons.Tags);
        Assert.Contains("pool", fiveSeasons.Tags);

        if (includeVectors)
        {
            Assert.Equal(new ReadOnlyMemory<float>([7.5f, 71.0f, 71.5f, 72.0f, 72.5f, 73.0f, 73.5f, 74.0f]), fiveSeasons.DescriptionEmbedding);
        }
        else
        {
            Assert.Equal(new ReadOnlyMemory<float>([]), fiveSeasons.DescriptionEmbedding);
        }
    }

    [VectorStoreTheory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task BatchGetAsync(bool collectionFromVectorStore)
    {
        var hotelsCollection = collectionFromVectorStore
            ? this.Fixture.HotelRecordCollection
            : this.Fixture.HotelRecordCollectionFromVectorStore;

        var hotels = await hotelsCollection.GetBatchAsync(["five-seasons", "vacation-inn", "best-eastern"]).ToListAsync();

        var fiveSeasons = hotels.Single(x => x.HotelId == "five-seasons");
        var vacationInn = hotels.Single(x => x.HotelId == "vacation-inn");
        var bestEastern = hotels.Single(x => x.HotelId == "best-eastern");

        Assert.Equal("Five Seasons Hotel", fiveSeasons.HotelName);
        Assert.Equal("Great service any season.", fiveSeasons.Description);
        Assert.Equal(7, fiveSeasons.HotelCode);
        Assert.Equal(4.5f, fiveSeasons.HotelRating);
        Assert.True(fiveSeasons.ParkingIncluded);
        Assert.Contains("wi-fi", fiveSeasons.Tags);
        Assert.Contains("sauna", fiveSeasons.Tags);
        Assert.Contains("gym", fiveSeasons.Tags);
        Assert.Contains("pool", fiveSeasons.Tags);

        Assert.Equal("Vacation Inn Hotel", vacationInn.HotelName);
        Assert.Equal("On vacation? Stay with us.", vacationInn.Description);
        Assert.Equal(11, vacationInn.HotelCode);
        Assert.Equal(4.3f, vacationInn.HotelRating);
        Assert.True(vacationInn.ParkingIncluded);
        Assert.Contains("wi-fi", vacationInn.Tags);
        Assert.Contains("breakfast", vacationInn.Tags);
        Assert.Contains("gym", vacationInn.Tags);

        Assert.Equal("Best Eastern Hotel", bestEastern.HotelName);
        Assert.Equal("Best hotel east of New York.", bestEastern.Description);
        Assert.Equal(42, bestEastern.HotelCode);
        Assert.Equal(4.7f, bestEastern.HotelRating);
        Assert.True(bestEastern.ParkingIncluded);
        Assert.Contains("wi-fi", bestEastern.Tags);
        Assert.Contains("breakfast", bestEastern.Tags);
        Assert.Contains("gym", bestEastern.Tags);
    }

    [VectorStoreTheory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task AllTypesBatchGetAsync(bool includeVectors)
    {
        var allTypes = await this.Fixture.AllTypesRecordCollection.GetBatchAsync(["all-types-1", "all-types-2"], new GetRecordOptions { IncludeVectors = includeVectors }).ToListAsync();

        var allTypes1 = allTypes.Single(x => x.Id == "all-types-1");
        var allTypes2 = allTypes.Single(x => x.Id == "all-types-2");

        Assert.True(allTypes1.BoolProperty);
        Assert.Equal("string prop 1", allTypes1.StringProperty);
        Assert.Equal(1, allTypes1.IntProperty);
        Assert.Equal(100L, allTypes1.LongProperty);
        Assert.Equal(10.5f, allTypes1.FloatProperty);
        Assert.Equal(23.75d, allTypes1.DoubleProperty);
        Assert.Equal(50.75m, allTypes1.DecimalProperty);
        Assert.Contains("one", allTypes1.StringArray);
        Assert.Contains("two", allTypes1.StringArray);
        Assert.Contains("eleven", allTypes1.StringList);
        Assert.Contains("twelve", allTypes1.StringList);
        Assert.Contains("Foo", allTypes1.Collection);
        Assert.Contains("Bar", allTypes1.Collection);
        Assert.Contains("another", allTypes1.Enumerable);
        Assert.Contains("and another", allTypes1.Enumerable);

        Assert.False(allTypes2.BoolProperty);
        Assert.Equal("string prop 2", allTypes2.StringProperty);
        Assert.Equal(2, allTypes2.IntProperty);
        Assert.Equal(200L, allTypes2.LongProperty);
        Assert.Equal(20.5f, allTypes2.FloatProperty);
        Assert.Equal(43.75d, allTypes2.DoubleProperty);
        Assert.Equal(250.75m, allTypes2.DecimalProperty);
        Assert.Empty(allTypes2.StringArray);
        Assert.Empty(allTypes2.StringList);
        Assert.Empty(allTypes2.Collection);
        Assert.Empty(allTypes2.Enumerable);

        if (includeVectors)
        {
            Assert.True(allTypes1.Embedding.HasValue);
            Assert.Equal(new ReadOnlyMemory<float>([1.5f, 2.5f, 3.5f, 4.5f, 5.5f, 6.5f, 7.5f, 8.5f]), allTypes1.Embedding.Value);

            Assert.True(allTypes2.Embedding.HasValue);
            Assert.Equal(new ReadOnlyMemory<float>([10.5f, 20.5f, 30.5f, 40.5f, 50.5f, 60.5f, 70.5f, 80.5f]), allTypes2.Embedding.Value);
        }
        else
        {
            Assert.Null(allTypes1.Embedding);
            Assert.Null(allTypes2.Embedding);
        }
    }

    [VectorStoreFact]
    public async Task BatchGetIncludingNonExistingRecordAsync()
    {
        var hotels = await this.Fixture.HotelRecordCollection.GetBatchAsync(["vacation-inn", "non-existing"]).ToListAsync();

        Assert.Single(hotels);
        var vacationInn = hotels.Single(x => x.HotelId == "vacation-inn");

        Assert.Equal("Vacation Inn Hotel", vacationInn.HotelName);
        Assert.Equal("On vacation? Stay with us.", vacationInn.Description);
        Assert.Equal(11, vacationInn.HotelCode);
        Assert.Equal(4.3f, vacationInn.HotelRating);
        Assert.True(vacationInn.ParkingIncluded);
        Assert.Contains("wi-fi", vacationInn.Tags);
        Assert.Contains("breakfast", vacationInn.Tags);
        Assert.Contains("gym", vacationInn.Tags);
    }

    [VectorStoreFact]
    public async Task GetNonExistingRecordAsync()
    {
        var result = await this.Fixture.HotelRecordCollection.GetAsync("non-existing");
        Assert.Null(result);
    }

    [VectorStoreTheory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetFromCustomNamespaceAsync(bool includeVectors)
    {
        var custom = await this.Fixture.HotelRecordCollectionWithCustomNamespace.GetAsync("custom-hotel", new GetRecordOptions { IncludeVectors = includeVectors });

        Assert.NotNull(custom);
        Assert.Equal("custom-hotel", custom.HotelId);
        Assert.Equal("Custom Hotel", custom.HotelName);
        if (includeVectors)
        {
            Assert.Equal(new ReadOnlyMemory<float>([147.5f, 1421.0f, 1741.5f, 1744.0f, 1742.5f, 1483.0f, 1743.5f, 1744.0f]), custom.DescriptionEmbedding);
        }
        else
        {
            Assert.Equal(new ReadOnlyMemory<float>([]), custom.DescriptionEmbedding);
        }
    }

    [VectorStoreFact]
    public async Task TryGetVectorLocatedInDefaultNamespaceButLookInCustomNamespaceAsync()
    {
        var badFiveSeasons = await this.Fixture.HotelRecordCollectionWithCustomNamespace.GetAsync("five-seasons");

        Assert.Null(badFiveSeasons);
    }

    [VectorStoreFact]
    public async Task TryGetVectorLocatedInCustomNamespaceButLookInDefaultNamespaceAsync()
    {
        var badCustomHotel = await this.Fixture.HotelRecordCollection.GetAsync("custom-hotel");

        Assert.Null(badCustomHotel);
    }

    [VectorStoreFact]
    public async Task DeleteNonExistingRecordAsync()
    {
        await this.Fixture.HotelRecordCollection.DeleteAsync("non-existing");
    }

    [VectorStoreFact]
    public async Task TryDeleteExistingVectorLocatedInDefaultNamespaceButUseCustomNamespaceDoesNotDoAnythingAsync()
    {
        await this.Fixture.HotelRecordCollectionWithCustomNamespace.DeleteAsync("five-seasons");

        var stillThere = await this.Fixture.HotelRecordCollection.GetAsync("five-seasons");
        Assert.NotNull(stillThere);
        Assert.Equal("five-seasons", stillThere.HotelId);
    }

    [VectorStoreFact]
    public async Task TryDeleteExistingVectorLocatedInCustomNamespaceButUseDefaultNamespaceDoesNotDoAnythingAsync()
    {
        await this.Fixture.HotelRecordCollection.DeleteAsync("custom-hotel");

        var stillThere = await this.Fixture.HotelRecordCollectionWithCustomNamespace.GetAsync("custom-hotel");
        Assert.NotNull(stillThere);
        Assert.Equal("custom-hotel", stillThere.HotelId);
    }

    [VectorStoreTheory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task InsertGetModifyDeleteVectorAsync(bool collectionFromVectorStore)
    {
        var langriSha = new PineconeHotel
        {
            HotelId = "langri-sha",
            HotelName = "Langri-Sha Hotel",
            Description = "Lorem ipsum",
            HotelCode = 100,
            HotelRating = 4.2f,
            ParkingIncluded = false,
            DescriptionEmbedding = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f, 5f, 6f, 7f, 8f])
        };

        var stats = await this.Fixture.Index.DescribeStats();
        var vectorCountBefore = stats.TotalVectorCount;

        var hotelRecordCollection = collectionFromVectorStore
            ? this.Fixture.HotelRecordCollectionFromVectorStore
            : this.Fixture.HotelRecordCollection;

        // insert
        await hotelRecordCollection.UpsertAsync(langriSha);

        vectorCountBefore = await this.Fixture.VerifyVectorCountModifiedAsync(vectorCountBefore, delta: 1);

        var inserted = await hotelRecordCollection.GetAsync("langri-sha", new GetRecordOptions { IncludeVectors = true });

        Assert.NotNull(inserted);
        Assert.Equal(langriSha.HotelName, inserted.HotelName);
        Assert.Equal(langriSha.Description, inserted.Description);
        Assert.Equal(langriSha.HotelCode, inserted.HotelCode);
        Assert.Equal(langriSha.HotelRating, inserted.HotelRating);
        Assert.Equal(langriSha.ParkingIncluded, inserted.ParkingIncluded);
        Assert.Equal(langriSha.DescriptionEmbedding, inserted.DescriptionEmbedding);

        langriSha.Description += " dolor sit amet";
        langriSha.ParkingIncluded = true;
        langriSha.DescriptionEmbedding = new ReadOnlyMemory<float>([11f, 12f, 13f, 14f, 15f, 16f, 17f, 18f]);

        // update
        await hotelRecordCollection.UpsertAsync(langriSha);

        // this is not great but no vectors are added so we can't query status for number of vectors like we do for insert/delete
        await Task.Delay(2000);

        var updated = await hotelRecordCollection.GetAsync("langri-sha", new GetRecordOptions { IncludeVectors = true });

        Assert.NotNull(updated);
        Assert.Equal(langriSha.HotelName, updated.HotelName);
        Assert.Equal(langriSha.Description, updated.Description);
        Assert.Equal(langriSha.HotelCode, updated.HotelCode);
        Assert.Equal(langriSha.HotelRating, updated.HotelRating);
        Assert.Equal(langriSha.ParkingIncluded, updated.ParkingIncluded);
        Assert.Equal(langriSha.DescriptionEmbedding, updated.DescriptionEmbedding);

        // delete
        await hotelRecordCollection.DeleteAsync("langri-sha");

        await this.Fixture.VerifyVectorCountModifiedAsync(vectorCountBefore, delta: -1);
    }

    [VectorStoreTheory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task VectorizedSearchAsync(bool collectionFromVectorStore, bool includeVectors)
    {
        // Arrange.
        var hotelRecordCollection = collectionFromVectorStore
            ? this.Fixture.HotelRecordCollectionFromVectorStore
            : this.Fixture.HotelRecordCollection;
        var searchVector = new ReadOnlyMemory<float>([17.5f, 721.0f, 731.5f, 742.0f, 762.5f, 783.0f, 793.5f, 704.0f]);

        // Act.
        var actual = await hotelRecordCollection.VectorizedSearchAsync(searchVector, new() { IncludeVectors = includeVectors });
        var searchResults = await actual.Results.ToListAsync();
        var searchResultRecord = searchResults.First().Record;

        Assert.Equal("Vacation Inn Hotel", searchResultRecord.HotelName);
        Assert.Equal("On vacation? Stay with us.", searchResultRecord.Description);
        Assert.Equal(11, searchResultRecord.HotelCode);
        Assert.Equal(4.3f, searchResultRecord.HotelRating);
        Assert.True(searchResultRecord.ParkingIncluded);
        Assert.Contains("wi-fi", searchResultRecord.Tags);
        Assert.Contains("breakfast", searchResultRecord.Tags);
        Assert.Contains("gym", searchResultRecord.Tags);
        Assert.Equal(includeVectors, searchResultRecord.DescriptionEmbedding.Length > 0);
    }

    [VectorStoreTheory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task VectorizedSearchWithTopSkipAsync(bool collectionFromVectorStore)
    {
        // Arrange.
        var hotelRecordCollection = collectionFromVectorStore
            ? this.Fixture.HotelRecordCollectionFromVectorStore
            : this.Fixture.HotelRecordCollection;
        var searchVector = new ReadOnlyMemory<float>([17.5f, 721.0f, 731.5f, 742.0f, 762.5f, 783.0f, 793.5f, 704.0f]);

        // Act.
        var actual = await hotelRecordCollection.VectorizedSearchAsync(searchVector, new() { Skip = 1, Top = 1 });
        var searchResults = await actual.Results.ToListAsync();
        Assert.Single(searchResults);
        var searchResultRecord = searchResults.First().Record;
        Assert.Equal("Best Eastern Hotel", searchResultRecord.HotelName);
    }

    [VectorStoreTheory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task VectorizedSearchWithFilterAsync(bool collectionFromVectorStore)
    {
        // Arrange.
        var hotelRecordCollection = collectionFromVectorStore
            ? this.Fixture.HotelRecordCollectionFromVectorStore
            : this.Fixture.HotelRecordCollection;
        var searchVector = new ReadOnlyMemory<float>([17.5f, 721.0f, 731.5f, 742.0f, 762.5f, 783.0f, 793.5f, 704.0f]);

        // Act.
        var filter = new VectorSearchFilter().EqualTo(nameof(PineconeHotel.HotelCode), 42);
        var actual = await hotelRecordCollection.VectorizedSearchAsync(searchVector, new() { Top = 1, OldFilter = filter });
        var searchResults = await actual.Results.ToListAsync();
        Assert.Single(searchResults);
        var searchResultRecord = searchResults.First().Record;
        Assert.Equal("Best Eastern Hotel", searchResultRecord.HotelName);
    }

    [VectorStoreFact]
    public async Task ItCanUpsertAndRetrieveUsingTheGenericMapperAsync()
    {
        var merryYacht = new VectorStoreGenericDataModel<string>("merry-yacht")
        {
            Data =
            {
                ["HotelName"] = "Merry Yacht Hotel",
                ["Description"] = "Stay afloat at the Merry Yacht Hotel",
                ["HotelCode"] = 101,
                ["HotelRating"] = 4.2f,
                ["ParkingIncluded"] = true,
                ["Tags"] = new[] { "wi-fi", "breakfast", "gym" }
            },
            Vectors =
            {
                ["DescriptionEmbedding"] = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f, 5f, 6f, 7f, 8f])
            }
        };

        var stats = await this.Fixture.Index.DescribeStats();
        var vectorCountBefore = stats.TotalVectorCount;

        var hotelRecordCollection = this.Fixture.HotelRecordCollectionWithGenericDataModel;

        // insert
        await hotelRecordCollection.UpsertAsync(merryYacht);

        vectorCountBefore = await this.Fixture.VerifyVectorCountModifiedAsync(vectorCountBefore, delta: 1);

        var inserted = await hotelRecordCollection.GetAsync("merry-yacht", new GetRecordOptions { IncludeVectors = true });

        Assert.NotNull(inserted);
        Assert.Equal(merryYacht.Data["HotelName"], inserted.Data["HotelName"]);
        Assert.Equal(merryYacht.Data["Description"], inserted.Data["Description"]);
        Assert.Equal(merryYacht.Data["HotelCode"], inserted.Data["HotelCode"]);
        Assert.Equal(merryYacht.Data["HotelRating"], inserted.Data["HotelRating"]);
        Assert.Equal(merryYacht.Data["ParkingIncluded"], inserted.Data["ParkingIncluded"]);
        Assert.Equal(merryYacht.Data["Tags"], inserted.Data["Tags"]);
        Assert.Equal(
            ((ReadOnlyMemory<float>)merryYacht.Vectors["DescriptionEmbedding"]!).ToArray(),
            ((ReadOnlyMemory<float>)inserted.Vectors["DescriptionEmbedding"]!).ToArray());

        // delete
        await hotelRecordCollection.DeleteAsync("merry-yacht");

        await this.Fixture.VerifyVectorCountModifiedAsync(vectorCountBefore, delta: -1);
    }

    [VectorStoreFact]
    public async Task UseCollectionExistsOnNonExistingStoreReturnsFalseAsync()
    {
        var incorrectRecordStore = new PineconeVectorStoreRecordCollection<PineconeHotel>(
            this.Fixture.Client,
            "incorrect");

        var result = await incorrectRecordStore.CollectionExistsAsync();

        Assert.False(result);
    }

    [VectorStoreFact]
    public async Task UseNonExistingIndexThrowsAsync()
    {
        var incorrectRecordStore = new PineconeVectorStoreRecordCollection<PineconeHotel>(
            this.Fixture.Client,
            "incorrect");

        var statusCode = (await Assert.ThrowsAsync<HttpRequestException>(
            () => incorrectRecordStore.GetAsync("best-eastern"))).StatusCode;

        Assert.Equal(HttpStatusCode.NotFound, statusCode);
    }

    [VectorStoreFact]
    public async Task UseRecordStoreWithCustomMapperAsync()
    {
        var recordStore = new PineconeVectorStoreRecordCollection<PineconeHotel>(
            this.Fixture.Client,
            this.Fixture.IndexName,
            new PineconeVectorStoreRecordCollectionOptions<PineconeHotel> { VectorCustomMapper = new CustomHotelRecordMapper() });

        var vacationInn = await recordStore.GetAsync("vacation-inn", new GetRecordOptions { IncludeVectors = true });

        Assert.NotNull(vacationInn);
        Assert.Equal("Custom Vacation Inn Hotel", vacationInn.HotelName);
        Assert.Equal("On vacation? Stay with us.", vacationInn.Description);
        Assert.Equal(11, vacationInn.HotelCode);
        Assert.Equal(4.3f, vacationInn.HotelRating);
        Assert.True(vacationInn.ParkingIncluded);
        Assert.Contains("wi-fi", vacationInn.Tags);
        Assert.Contains("breakfast", vacationInn.Tags);
        Assert.Contains("gym", vacationInn.Tags);
    }

    private sealed class CustomHotelRecordMapper : IVectorStoreRecordMapper<PineconeHotel, Vector>
    {
        public Vector MapFromDataToStorageModel(PineconeHotel dataModel)
        {
            var metadata = new MetadataMap
            {
                [nameof(PineconeHotel.HotelName)] = dataModel.HotelName,
                [nameof(PineconeHotel.Description)] = dataModel.Description,
                [nameof(PineconeHotel.HotelCode)] = dataModel.HotelCode,
                [nameof(PineconeHotel.HotelRating)] = dataModel.HotelRating,
                ["parking_is_included"] = dataModel.ParkingIncluded,
                [nameof(PineconeHotel.Tags)] = dataModel.Tags.ToArray(),
            };

            return new Vector
            {
                Id = dataModel.HotelId,
                Values = dataModel.DescriptionEmbedding.ToArray(),
                Metadata = metadata,
            };
        }

        public PineconeHotel MapFromStorageToDataModel(Vector storageModel, StorageToDataModelMapperOptions options)
        {
            if (storageModel.Metadata == null)
            {
                throw new InvalidOperationException("Missing metadata.");
            }

            return new PineconeHotel
            {
                HotelId = storageModel.Id,
                HotelName = "Custom " + (string)storageModel.Metadata[nameof(PineconeHotel.HotelName)].Inner!,
                Description = (string)storageModel.Metadata[nameof(PineconeHotel.Description)].Inner!,
                HotelCode = (int)(double)storageModel.Metadata[nameof(PineconeHotel.HotelCode)].Inner!,
                HotelRating = (float)(double)storageModel.Metadata[nameof(PineconeHotel.HotelRating)].Inner!,
                ParkingIncluded = (bool)storageModel.Metadata["parking_is_included"].Inner!,
                Tags = ((MetadataValue[])storageModel.Metadata[nameof(PineconeHotel.Tags)].Inner!)!.Select(x => (string)x.Inner!).ToList(),
            };
        }
    }

    #region Negative

    [VectorStoreFact]
    public void UseRecordWithNoEmbeddingThrows()
    {
        var exception = Assert.Throws<ArgumentException>(
            () => new PineconeVectorStoreRecordCollection<PineconeRecordNoEmbedding>(
            this.Fixture.Client,
            "Whatever"));

        Assert.Equal(
            $"No vector property found on type {nameof(PineconeRecordNoEmbedding)} or the provided VectorStoreRecordDefinition while at least one is required.",
            exception.Message);
    }

#pragma warning disable CA1812
    private sealed record PineconeRecordNoEmbedding
    {
        [VectorStoreRecordKey]
        public int Id { get; set; }

        [VectorStoreRecordData]
        public string? Name { get; set; }
    }
#pragma warning restore CA1812

    [VectorStoreFact]
    public void UseRecordWithMultipleEmbeddingsThrows()
    {
        var exception = Assert.Throws<ArgumentException>(
            () => new PineconeVectorStoreRecordCollection<PineconeRecordMultipleEmbeddings>(
            this.Fixture.Client,
            "Whatever"));

        Assert.Equal(
            $"Multiple vector properties found on type {nameof(PineconeRecordMultipleEmbeddings)} or the provided VectorStoreRecordDefinition while only one is supported.",
            exception.Message);
    }

#pragma warning disable CA1812
    private sealed record PineconeRecordMultipleEmbeddings
    {
        [VectorStoreRecordKey]
        public string Id { get; set; } = null!;

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float> Embedding1 { get; set; }

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float> Embedding2 { get; set; }
    }
#pragma warning restore CA1812

    [VectorStoreFact]
    public void UseRecordWithUnsupportedKeyTypeThrows()
    {
        var message = Assert.Throws<ArgumentException>(
            () => new PineconeVectorStoreRecordCollection<PineconeRecordUnsupportedKeyType>(
                this.Fixture.Client,
                "Whatever")).Message;

        Assert.Equal(
            $"Key properties must be one of the supported types: {typeof(string).FullName}. Type of the property '{nameof(PineconeRecordUnsupportedKeyType.Id)}' is {typeof(int).FullName}.",
            message);
    }

#pragma warning disable CA1812
    private sealed record PineconeRecordUnsupportedKeyType
    {
        [VectorStoreRecordKey]
        public int Id { get; set; }

        [VectorStoreRecordData]
        public string? Name { get; set; }

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
#pragma warning restore CA1812

    [VectorStoreFact]
    public async Task TryAddingVectorWithUnsupportedValuesAsync()
    {
        var badAllTypes = new PineconeAllTypes
        {
            Id = "bad",
            BoolProperty = true,
            DecimalProperty = 1m,
            DoubleProperty = 1.5d,
            FloatProperty = 2.5f,
            IntProperty = 1,
            LongProperty = 11L,
            NullableStringArray = ["foo", null!, "bar",],
            Embedding = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f, 5f, 6f, 7f, 8f])
        };

        var exception = await Assert.ThrowsAsync<VectorStoreOperationException>(
            () => this.Fixture.AllTypesRecordCollection.UpsertAsync(badAllTypes));

        Assert.Equal("Microsoft.SemanticKernel.Connectors.Pinecone", exception.Source);
        Assert.Equal("Pinecone", exception.VectorStoreType);
        Assert.Equal("Upsert", exception.OperationName);
        Assert.Equal(this.Fixture.IndexName, exception.CollectionName);

        var inner = exception.InnerException as RpcException;
        Assert.NotNull(inner);
        Assert.Equal(StatusCode.InvalidArgument, inner.StatusCode);
    }

    [VectorStoreFact]
    public async Task TryCreateIndexWithIncorrectDimensionFailsAsync()
    {
        var recordCollection = new PineconeVectorStoreRecordCollection<PineconeRecordWithIncorrectDimension>(
            this.Fixture.Client,
            "negative-dimension");

        var message = (await Assert.ThrowsAsync<InvalidOperationException>(() => recordCollection.CreateCollectionAsync())).Message;

        Assert.Equal("Property Dimensions on VectorStoreRecordVectorProperty 'Embedding' must be set to a positive integer to create a collection.", message);
    }

#pragma warning disable CA1812
    private sealed record PineconeRecordWithIncorrectDimension
    {
        [VectorStoreRecordKey]
        public string Id { get; set; } = null!;

        [VectorStoreRecordData]
        public string? Name { get; set; }

        [VectorStoreRecordVector(Dimensions: -7)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
#pragma warning restore CA1812

    [VectorStoreFact]
    public async Task TryCreateIndexWithUnsSupportedMetricFailsAsync()
    {
        var recordCollection = new PineconeVectorStoreRecordCollection<PineconeRecordWithUnsupportedMetric>(
            this.Fixture.Client,
            "bad-metric");

        var message = (await Assert.ThrowsAsync<InvalidOperationException>(() => recordCollection.CreateCollectionAsync())).Message;

        Assert.Equal("Distance function 'just eyeball it' for VectorStoreRecordVectorProperty 'Embedding' is not supported by the Pinecone VectorStore.", message);
    }

#pragma warning disable CA1812
    private sealed record PineconeRecordWithUnsupportedMetric
    {
        [VectorStoreRecordKey]
        public string Id { get; set; } = null!;

        [VectorStoreRecordData]
        public string? Name { get; set; }

        [VectorStoreRecordVector(Dimensions: 5, DistanceFunction: "just eyeball it")]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
#pragma warning restore CA1812

    #endregion
}
