// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Filter;
using Xunit;

namespace CosmosNoSQLIntegrationTests.Filter;

public class CosmosNoSQLBasicFilterTests(CosmosNoSQLFilterFixture fixture) : BasicFilterTestsBase<string>(fixture), IClassFixture<CosmosNoSQLFilterFixture>;
