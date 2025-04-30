// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Models;
using VectorDataSpecificationTests.Support;

namespace RedisIntegrationTests.Support;

public class RedisHashSetSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => RedisTestStore.HashSetInstance;

    public override VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(SimpleRecord<string>.Id), typeof(string))
                {
                    StoragePropertyName = "i d" // intentionally with a space
                },
                new VectorStoreRecordVectorProperty(nameof(SimpleRecord<string>.Floats), typeof(ReadOnlyMemory<float>?), SimpleRecord<string>.DimensionCount)
                {
                    DistanceFunction = this.DistanceFunction,
                    IndexKind = this.IndexKind,
                    // Redis HashSet does not support escaping column names used in the Query (Json does).
                },
                new VectorStoreRecordDataProperty(nameof(SimpleRecord<string>.Number), typeof(int))
                {
                    IsIndexed = true,
                    StoragePropertyName = "num'b\"er" // intentionally with both quotes
                },
                new VectorStoreRecordDataProperty(nameof(SimpleRecord<string>.Text), typeof(string))
                {
                    IsIndexed = true,
                    StoragePropertyName = "t e]xt" // intentionally with a space and ]
                },
            ]
        };
}
