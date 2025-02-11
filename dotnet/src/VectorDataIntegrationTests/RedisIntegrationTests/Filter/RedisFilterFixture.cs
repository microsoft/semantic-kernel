// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;

namespace RedisIntegrationTests.Filter;

public class RedisJsonCollectionFilterFixture : FilterFixtureBase<string>
{
    protected override TestStore TestStore => RedisTestStore.Instance;

    protected override string StoreName => "JsonCollectionFilterTests";

    // Override to remove the bool property, which isn't (currently) supported on Redis/JSON
    protected override VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties = base.GetRecordDefinition().Properties.Where(p => p.PropertyType != typeof(bool)).ToList()
        };

    protected override IVectorStoreRecordCollection<string, FilterRecord<string>> CreateCollection()
        => new RedisJsonVectorStoreRecordCollection<FilterRecord<string>>(
            RedisTestStore.Instance.Database,
            this.StoreName,
            new() { VectorStoreRecordDefinition = this.GetRecordDefinition() });
}

public class RedisHashSetCollectionFilterFixture : FilterFixtureBase<string>
{
    protected override TestStore TestStore => RedisTestStore.Instance;

    protected override string StoreName => "HashSetCollectionFilterTests";

    // Override to remove the bool property, which isn't (currently) supported on Redis
    protected override VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties = base.GetRecordDefinition().Properties.Where(p =>
                p.PropertyType != typeof(bool) &&
                p.PropertyType != typeof(string[]) &&
                p.PropertyType != typeof(List<string>)).ToList()
        };

    protected override IVectorStoreRecordCollection<string, FilterRecord<string>> CreateCollection()
        => new RedisHashSetVectorStoreRecordCollection<FilterRecord<string>>(
            RedisTestStore.Instance.Database,
            this.StoreName,
            new() { VectorStoreRecordDefinition = this.GetRecordDefinition() });

    protected override List<FilterRecord<string>> BuildTestData()
    {
        var testData = base.BuildTestData();

        foreach (var record in testData)
        {
            // Null values are not supported in Redis hashsets
            record.String ??= string.Empty;
        }

        return testData;
    }
}
