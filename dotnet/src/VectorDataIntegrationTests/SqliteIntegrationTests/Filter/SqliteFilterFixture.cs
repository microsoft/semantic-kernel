// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using SqliteIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;

namespace SqliteIntegrationTests.Filter;

public class SqliteFilterFixture : FilterFixtureBase<ulong>
{
    protected override TestStore TestStore => SqliteTestStore.Instance;

    protected override string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

    // Override to remove the string array property, which isn't (currently) supported on SQLite
    protected override VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties = base.GetRecordDefinition().Properties.Where(p => p.PropertyType != typeof(string[]) && p.PropertyType != typeof(List<string>)).ToList()
        };
}
