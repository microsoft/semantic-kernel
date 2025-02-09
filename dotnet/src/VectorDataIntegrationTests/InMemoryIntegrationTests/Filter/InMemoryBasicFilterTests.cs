// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Filter;
using Xunit;

namespace PostgresIntegrationTests.Filter;

public class InMemoryBasicFilterTests(InMemoryFilterFixture fixture) : BasicFilterTestsBase<int>(fixture), IClassFixture<InMemoryFilterFixture>;
