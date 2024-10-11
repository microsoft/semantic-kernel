// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Pinecone.Grpc;
using Xunit;
using Sdk = Pinecone;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone;

public class PineconeVectorStoreFixture : IAsyncLifetime
{
    private const int MaxAttemptCount = 100;
    private const int DelayInterval = 300;

    public string IndexName { get; } = "sk-index"
#pragma warning disable CA1308 // Normalize strings to uppercase
        + new Regex("[^a-zA-Z0-9]", RegexOptions.None, matchTimeout: new TimeSpan(0, 0, 10)).Replace(Environment.MachineName.ToLowerInvariant(), "");
#pragma warning restore CA1308 // Normalize strings to uppercase

    public Sdk.PineconeClient Client { get; private set; } = null!;
    public PineconeVectorStore VectorStore { get; private set; } = null!;
    public PineconeVectorStoreRecordCollection<PineconeHotel> HotelRecordCollection { get; set; } = null!;
    public PineconeVectorStoreRecordCollection<PineconeAllTypes> AllTypesRecordCollection { get; set; } = null!;
    public PineconeVectorStoreRecordCollection<PineconeHotel> HotelRecordCollectionWithCustomNamespace { get; set; } = null!;
    public IVectorStoreRecordCollection<string, PineconeHotel> HotelRecordCollectionFromVectorStore { get; set; } = null!;

    public virtual Sdk.Index<GrpcTransport> Index { get; set; } = null!;

    public virtual async Task InitializeAsync()
    {
        this.Client = new Sdk.PineconeClient(PineconeUserSecretsExtensions.ReadPineconeApiKey());
        this.VectorStore = new PineconeVectorStore(this.Client);

        var hotelRecordDefinition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(PineconeHotel.HotelId), typeof(string)),
                new VectorStoreRecordDataProperty(nameof(PineconeHotel.HotelName), typeof(string)),
                new VectorStoreRecordDataProperty(nameof(PineconeHotel.HotelCode), typeof(int)),
                new VectorStoreRecordDataProperty(nameof(PineconeHotel.ParkingIncluded), typeof(bool)) { StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty(nameof(PineconeHotel.HotelRating), typeof(float)),
                new VectorStoreRecordDataProperty(nameof(PineconeHotel.Tags), typeof(List<string>)),
                new VectorStoreRecordDataProperty(nameof(PineconeHotel.Description), typeof(string)),
                new VectorStoreRecordVectorProperty(nameof(PineconeHotel.DescriptionEmbedding), typeof(ReadOnlyMemory<float>)) { Dimensions = 8, DistanceFunction = DistanceFunction.DotProductSimilarity }
            ]
        };

        var allTypesRecordDefinition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(PineconeAllTypes.Id), typeof(string)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.BoolProperty), typeof(bool)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableBoolProperty), typeof(bool?)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.StringProperty), typeof(string)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableStringProperty), typeof(string)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.IntProperty), typeof(int)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableIntProperty), typeof(int?)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.LongProperty), typeof(long)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableLongProperty), typeof(long?)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.FloatProperty), typeof(float)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableFloatProperty), typeof(float?)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.DoubleProperty), typeof(double)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableDoubleProperty), typeof(double?)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.DecimalProperty), typeof(decimal)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableDecimalProperty), typeof(decimal?)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.StringArray), typeof(string[])),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableStringArray), typeof(string[])),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.StringList), typeof(List<string>)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableStringList), typeof(List<string?>)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.Collection), typeof(IReadOnlyCollection<string>)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.Enumerable), typeof(IEnumerable<string>)),
                new VectorStoreRecordVectorProperty(nameof(PineconeAllTypes.Embedding), typeof(ReadOnlyMemory<float>?)) { Dimensions = 8, DistanceFunction = DistanceFunction.DotProductSimilarity }
            ]
        };

        this.HotelRecordCollection = new PineconeVectorStoreRecordCollection<PineconeHotel>(
            this.Client,
            this.IndexName,
            new PineconeVectorStoreRecordCollectionOptions<PineconeHotel>
            {
                VectorStoreRecordDefinition = hotelRecordDefinition
            });

        this.AllTypesRecordCollection = new PineconeVectorStoreRecordCollection<PineconeAllTypes>(
            this.Client,
            this.IndexName,
            new PineconeVectorStoreRecordCollectionOptions<PineconeAllTypes>
            {
                VectorStoreRecordDefinition = allTypesRecordDefinition
            });

        this.HotelRecordCollectionWithCustomNamespace = new PineconeVectorStoreRecordCollection<PineconeHotel>(
            this.Client,
            this.IndexName,
            new PineconeVectorStoreRecordCollectionOptions<PineconeHotel>
            {
                VectorStoreRecordDefinition = hotelRecordDefinition,
                IndexNamespace = "my-namespace"
            });

        this.HotelRecordCollectionFromVectorStore = this.VectorStore.GetCollection<string, PineconeHotel>(
            this.IndexName,
            hotelRecordDefinition);

        await this.ClearIndexesAsync();
        await this.CreateIndexAndWaitAsync();
        await this.AddSampleDataAsync();
    }

    private async Task CreateIndexAndWaitAsync()
    {
        var attemptCount = 0;

        await this.HotelRecordCollection.CreateCollectionAsync();

        do
        {
            await Task.Delay(DelayInterval);
            attemptCount++;
            this.Index = await this.Client.GetIndex(this.IndexName);
        } while (!this.Index.Status.IsReady && attemptCount <= MaxAttemptCount);

        if (!this.Index.Status.IsReady)
        {
            throw new InvalidOperationException("'Create index' operation didn't complete in time. Index name: " + this.IndexName);
        }
    }

    public async Task DisposeAsync()
    {
        if (this.Client is not null)
        {
            await this.ClearIndexesAsync();
            this.Client.Dispose();
        }
    }

    private async Task AddSampleDataAsync()
    {
        var fiveSeasons = new PineconeHotel
        {
            HotelId = "five-seasons",
            HotelName = "Five Seasons Hotel",
            Description = "Great service any season.",
            HotelCode = 7,
            HotelRating = 4.5f,
            ParkingIncluded = true,
            DescriptionEmbedding = new ReadOnlyMemory<float>([7.5f, 71.0f, 71.5f, 72.0f, 72.5f, 73.0f, 73.5f, 74.0f]),
            Tags = ["wi-fi", "sauna", "gym", "pool"]
        };

        var vacationInn = new PineconeHotel
        {
            HotelId = "vacation-inn",
            HotelName = "Vacation Inn Hotel",
            Description = "On vacation? Stay with us.",
            HotelCode = 11,
            HotelRating = 4.3f,
            ParkingIncluded = true,
            DescriptionEmbedding = new ReadOnlyMemory<float>([17.5f, 721.0f, 731.5f, 742.0f, 762.5f, 783.0f, 793.5f, 704.0f]),
            Tags = ["wi-fi", "breakfast", "gym"]
        };

        var bestEastern = new PineconeHotel
        {
            HotelId = "best-eastern",
            HotelName = "Best Eastern Hotel",
            Description = "Best hotel east of New York.",
            HotelCode = 42,
            HotelRating = 4.7f,
            ParkingIncluded = true,
            DescriptionEmbedding = new ReadOnlyMemory<float>([47.5f, 421.0f, 741.5f, 744.0f, 742.5f, 483.0f, 743.5f, 744.0f]),
            Tags = ["wi-fi", "breakfast", "gym"]
        };

        var stats = await this.Index.DescribeStats();
        var vectorCountBefore = stats.TotalVectorCount;

        // use both Upsert and BatchUpsert methods and also use record collections created directly and using vector store
        await this.HotelRecordCollection.UpsertAsync(fiveSeasons);
        vectorCountBefore = await this.VerifyVectorCountModifiedAsync(vectorCountBefore, delta: 1);

        await this.HotelRecordCollectionFromVectorStore.UpsertBatchAsync([vacationInn, bestEastern]).ToListAsync();
        vectorCountBefore = await this.VerifyVectorCountModifiedAsync(vectorCountBefore, delta: 2);

        var allTypes1 = new PineconeAllTypes
        {
            Id = "all-types-1",
            BoolProperty = true,
            NullableBoolProperty = false,
            StringProperty = "string prop 1",
            NullableStringProperty = "nullable prop 1",
            IntProperty = 1,
            NullableIntProperty = 10,
            LongProperty = 100L,
            NullableLongProperty = 1000L,
            FloatProperty = 10.5f,
            NullableFloatProperty = 100.5f,
            DoubleProperty = 23.75d,
            NullableDoubleProperty = 233.75d,
            DecimalProperty = 50.75m,
            NullableDecimalProperty = 500.75m,
            StringArray = ["one", "two"],
            NullableStringArray = ["five", "six"],
            StringList = ["eleven", "twelve"],
            NullableStringList = ["fifteen", "sixteen"],
            Collection = ["Foo", "Bar"],
            Enumerable = ["another", "and another"],
            Embedding = new ReadOnlyMemory<float>([1.5f, 2.5f, 3.5f, 4.5f, 5.5f, 6.5f, 7.5f, 8.5f])
        };

        var allTypes2 = new PineconeAllTypes
        {
            Id = "all-types-2",
            BoolProperty = false,
            NullableBoolProperty = null,
            StringProperty = "string prop 2",
            NullableStringProperty = null,
            IntProperty = 2,
            NullableIntProperty = null,
            LongProperty = 200L,
            NullableLongProperty = null,
            FloatProperty = 20.5f,
            NullableFloatProperty = null,
            DoubleProperty = 43.75,
            NullableDoubleProperty = null,
            DecimalProperty = 250.75M,
            NullableDecimalProperty = null,
            StringArray = [],
            NullableStringArray = null,
            StringList = [],
            NullableStringList = null,
            Collection = [],
            Enumerable = [],
            Embedding = new ReadOnlyMemory<float>([10.5f, 20.5f, 30.5f, 40.5f, 50.5f, 60.5f, 70.5f, 80.5f])
        };

        await this.AllTypesRecordCollection.UpsertBatchAsync([allTypes1, allTypes2]).ToListAsync();
        vectorCountBefore = await this.VerifyVectorCountModifiedAsync(vectorCountBefore, delta: 2);

        var custom = new PineconeHotel
        {
            HotelId = "custom-hotel",
            HotelName = "Custom Hotel",
            Description = "Everything customizable!",
            HotelCode = 17,
            HotelRating = 4.25f,
            ParkingIncluded = true,
            DescriptionEmbedding = new ReadOnlyMemory<float>([147.5f, 1421.0f, 1741.5f, 1744.0f, 1742.5f, 1483.0f, 1743.5f, 1744.0f]),
        };

        await this.HotelRecordCollectionWithCustomNamespace.UpsertAsync(custom);
        vectorCountBefore = await this.VerifyVectorCountModifiedAsync(vectorCountBefore, delta: 1);
    }

    public async Task<uint> VerifyVectorCountModifiedAsync(uint vectorCountBefore, int delta)
    {
        var attemptCount = 0;
        Sdk.IndexStats stats;

        do
        {
            await Task.Delay(DelayInterval);
            attemptCount++;
            stats = await this.Index.DescribeStats();
        } while (stats.TotalVectorCount != vectorCountBefore + delta && attemptCount <= MaxAttemptCount);

        if (stats.TotalVectorCount != vectorCountBefore + delta)
        {
            throw new InvalidOperationException("'Upsert'/'Delete' operation didn't complete in time.");
        }

        return stats.TotalVectorCount;
    }

    public async Task DeleteAndWaitAsync(IEnumerable<string> ids, string? indexNamespace = null)
    {
        var stats = await this.Index.DescribeStats();
        var vectorCountBefore = stats.Namespaces.Single(x => x.Name == (indexNamespace ?? "")).VectorCount;
        var idCount = ids.Count();

        var attemptCount = 0;
        await this.Index.Delete(ids, indexNamespace);
        long vectorCount;
        do
        {
            await Task.Delay(DelayInterval);
            attemptCount++;
            stats = await this.Index.DescribeStats();
            vectorCount = stats.Namespaces.Single(x => x.Name == (indexNamespace ?? "")).VectorCount;
        } while (vectorCount > vectorCountBefore - idCount && attemptCount <= MaxAttemptCount);

        if (vectorCount > vectorCountBefore - idCount)
        {
            throw new InvalidOperationException("'Delete' operation didn't complete in time.");
        }
    }

    private async Task ClearIndexesAsync()
    {
        var indexes = await this.Client.ListIndexes();
        var deletions = indexes.Select(x => this.DeleteExistingIndexAndWaitAsync(x.Name));

        await Task.WhenAll(deletions);
    }

    private async Task DeleteExistingIndexAndWaitAsync(string indexName)
    {
        var exists = true;
        try
        {
            var attemptCount = 0;
            await this.Client.DeleteIndex(indexName);

            do
            {
                await Task.Delay(DelayInterval);
                var indexes = (await this.Client.ListIndexes()).Select(x => x.Name).ToArray();
                if (indexes.Length == 0 || !indexes.Contains(indexName))
                {
                    exists = false;
                }
            } while (exists && attemptCount <= MaxAttemptCount);
        }
        catch (HttpRequestException ex) when (ex.Message.Contains("NOT_FOUND"))
        {
            // index was already deleted
            exists = false;
        }

        if (exists)
        {
            throw new InvalidOperationException("'Delete index' operation didn't complete in time. Index name: " + indexName);
        }
    }
}
