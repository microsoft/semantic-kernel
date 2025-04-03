// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.IntegrationTests.TestSettings;

#pragma warning disable CA1812 // Configuration classes are instantiated through IConfiguration.
internal sealed class TavilyConfiguration(string apiKey)
{
    public string ApiKey { get; init; } = apiKey;
}
