// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using WeaviateIntegrationTests.Support;

namespace WeaviateIntegrationTests.Filter;

public class WeaviateFilterFixture : FilterFixtureBase<Guid>
{
    protected override TestStore TestStore => WeaviateTestStore.Instance;

    protected override string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;
}
