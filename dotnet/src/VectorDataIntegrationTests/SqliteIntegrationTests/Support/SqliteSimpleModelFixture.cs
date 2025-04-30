// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Models;
using VectorDataSpecificationTests.Support;

namespace SqliteIntegrationTests.Support;

public class SqliteSimpleModelFixture<TKey> : SimpleModelFixture<TKey>
    where TKey : notnull
{
    public override TestStore TestStore => SqliteTestStore.Instance;

    public override VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties =
            [
                // The Id and Floats  properties are stored in the vec_ table and this extension currently does not support
                // quoting column names, so don't customize their storage property names.
                new VectorStoreRecordKeyProperty(nameof(SimpleRecord<TKey>.Id), typeof(TKey)),
                new VectorStoreRecordVectorProperty(nameof(SimpleRecord<TKey>.Floats), typeof(ReadOnlyMemory<float>?), SimpleRecord<TKey>.DimensionCount)
                {
                    DistanceFunction = this.DistanceFunction,
                    IndexKind = this.IndexKind,
                },
                new VectorStoreRecordDataProperty(nameof(SimpleRecord<TKey>.Number), typeof(int))
                {
                    IsIndexed = true,
                    StoragePropertyName = "num'b\"er" // intentionally with both quotes
                },
                new VectorStoreRecordDataProperty(nameof(SimpleRecord<TKey>.Text), typeof(string))
                {
                    IsIndexed = true,
                    StoragePropertyName = "t e]xt" // intentionally with a space and ]
                },
            ]
        };
}
