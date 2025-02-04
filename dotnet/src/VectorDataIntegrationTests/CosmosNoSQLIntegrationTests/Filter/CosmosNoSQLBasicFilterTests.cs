// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Filter;
using Xunit;

namespace CosmosNoSQLIntegrationTests.Filter;

public class CosmosNoSQLBasicFilterTests(CosmosFilterFixture fixture) : BasicFilterTestsBase<string>(fixture), IClassFixture<CosmosFilterFixture>;
