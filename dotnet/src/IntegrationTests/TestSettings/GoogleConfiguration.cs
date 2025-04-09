// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class GoogleConfiguration(string apiKey, string searchEngineId)
{
    public string ApiKey { get; init; } = apiKey;
    public string SearchEngineId { get; init; } = searchEngineId;
}
