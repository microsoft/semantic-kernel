// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary.
using Xunit;
#pragma warning restore IDE0005 // Using directive is unnecessary.

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// A collection definition for shared process tests.
/// </summary>
[CollectionDefinition(nameof(ProcessTestGroup))]
public class ProcessTestGroup : ICollectionFixture<ProcessTestFixture>;
