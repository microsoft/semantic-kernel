// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.IntegrationTests.TestSettings;

#pragma warning disable CA1812 // Configuration classes are instantiated through IConfiguration.
internal sealed class KeenableConfiguration(string? apiKey = null)
{
    /// <summary>
    /// Optional API key. When null or empty the public endpoint is used.
    /// </summary>
    public string? ApiKey { get; init; } = apiKey;
}
