// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace AzureAISearch.ConformanceTests.CRUD;

public class AzureAISearchAllSupportedTypesTests(AzureAISearchFixture fixture) : IClassFixture<AzureAISearchFixture>
{
    [ConditionalFact]
    public async Task AllTypesBatchGetAsync()
    {
        var collection = fixture.TestStore.DefaultVectorStore.GetCollection<string, AzureAISearchAllTypes>("all-types", AzureAISearchAllTypes.GetRecordDefinition());
        await collection.EnsureCollectionExistsAsync();

        List<AzureAISearchAllTypes> records =
        [
            new()
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
                DateTimeOffsetProperty = DateTimeOffset.UtcNow,
                NullableDateTimeOffsetProperty = DateTimeOffset.UtcNow,
                StringArray = ["one", "two"],
                StringList = ["eleven", "twelve"],
                BoolArray = [true, false],
                BoolList = [true, false],
                IntArray = [1, 2],
                IntList = [11, 12],
                LongArray = [100L, 200L],
                LongList = [1100L, 1200L],
                FloatArray = [1.5f, 2.5f],
                FloatList = [11.5f, 12.5f],
                DoubleArray = [1.5d, 2.5d],
                DoubleList = [11.5d, 12.5d],
                DateTimeOffsetArray = [DateTimeOffset.UtcNow, DateTimeOffset.UtcNow],
                DateTimeOffsetList = [DateTimeOffset.UtcNow, DateTimeOffset.UtcNow],
                Embedding = new ReadOnlyMemory<float>([1.5f, 2.5f, 3.5f, 4.5f, 5.5f, 6.5f, 7.5f, 8.5f])
            },
            new()
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
                Embedding = ReadOnlyMemory<float>.Empty,
                // From https://learn.microsoft.com/en-us/rest/api/searchservice/supported-data-types:
                // "All of the above types are nullable, except for collections of primitive and complex types, for example, Collection(Edm.String)"
                // So for collections, we can't use nulls.
                StringArray = [],
                StringList = [],
                BoolArray = [],
                BoolList = [],
                IntArray = [],
                IntList = [],
                LongArray = [],
                LongList = [],
                FloatArray = [],
                FloatList = [],
                DoubleArray = [],
                DoubleList = [],
                DateTimeOffsetArray = [],
                DateTimeOffsetList = [],
            }
        ];

        try
        {
            await collection.UpsertAsync(records);

            var allTypes = await collection.GetAsync(records.Select(r => r.Id), new RecordRetrievalOptions { IncludeVectors = true }).ToListAsync();

            var allTypes1 = allTypes.Single(x => x.Id == records[0].Id);
            var allTypes2 = allTypes.Single(x => x.Id == records[1].Id);

            records[0].AssertEqual(allTypes1);
            records[1].AssertEqual(allTypes2);
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }
}
