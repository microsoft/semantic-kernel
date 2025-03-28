// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace SqliteIntegrationTests.Support;

public class SqliteSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => SqliteTestStore.Instance;

    public override string DefaultDistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;
}
