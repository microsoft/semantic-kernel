﻿// Copyright (c) Microsoft. All rights reserved.

using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace QdrantIntegrationTests.Collections;

public class QdrantCollectionConformanceTests_NamedVectors(QdrantNamedVectorsFixture fixture)
    : CollectionConformanceTests<ulong>(fixture), IClassFixture<QdrantNamedVectorsFixture>
{
}
