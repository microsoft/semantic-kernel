// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// A collection definition for shared process tests.
/// </summary>
[CollectionDefinition(nameof(ProcessTestGroup))]
public class ProcessTestGroup : ICollectionFixture<ProcessTestFixture>
{
}
