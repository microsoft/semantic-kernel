// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Filter;
using Xunit;

namespace QdrantIntegrationTests.Filter;

public class QdrantBasicFilterTests(QdrantFilterFixture fixture) : BasicFilterTestsBase<ulong>(fixture), IClassFixture<QdrantFilterFixture>;
