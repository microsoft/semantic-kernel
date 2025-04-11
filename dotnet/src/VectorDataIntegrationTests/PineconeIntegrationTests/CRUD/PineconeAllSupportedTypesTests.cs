// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using PineconeIntegrationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace PineconeIntegrationTests.CRUD;

public class PineconeAllSupportedTypesTests(PineconeFixture fixture) : IClassFixture<PineconeFixture>
{
    [ConditionalFact]
    public async Task AllTypesBatchGetAsync()
    {
        var collection = fixture.TestStore.DefaultVectorStore.GetCollection<string, PineconeAllTypes>("all-types", PineconeAllTypes.GetRecordDefinition());
        await collection.CreateCollectionIfNotExistsAsync();

        List<PineconeAllTypes> records =
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
                StringArray = ["one", "two"],
                NullableStringArray = ["five", "six"],
                StringList = ["eleven", "twelve"],
                NullableStringList = ["fifteen", "sixteen"],
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
                StringArray = [],
                NullableStringArray = null,
                StringList = [],
                NullableStringList = null,
                Embedding = new ReadOnlyMemory<float>([10.5f, 20.5f, 30.5f, 40.5f, 50.5f, 60.5f, 70.5f, 80.5f])
            }
        ];

        await collection.UpsertAsync(records);

        var allTypes = await collection.GetAsync(records.Select(r => r.Id), new GetRecordOptions { IncludeVectors = true }).ToListAsync();

        var allTypes1 = allTypes.Single(x => x.Id == records[0].Id);
        var allTypes2 = allTypes.Single(x => x.Id == records[1].Id);

        records[0].AssertEqual(allTypes1);
        records[1].AssertEqual(allTypes2);
    }
}
