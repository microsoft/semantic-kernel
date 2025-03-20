﻿// Copyright (c) Microsoft. All rights reserved.

using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace QdrantIntegrationTests.Collections;

public class QdrantCollectionConformanceTests_UnnamedVector(QdrantUnnamedVectorFixture fixture)
    : CollectionConformanceTests<ulong>(fixture), IClassFixture<QdrantUnnamedVectorFixture>
{
}
