// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests;
using Xunit;

namespace AzureAISearch.ConformanceTests;

public class AzureAISearchCollectionManagementTests(AzureAISearchFixture fixture)
    : CollectionManagementTests<string>(fixture), IClassFixture<AzureAISearchFixture>;
