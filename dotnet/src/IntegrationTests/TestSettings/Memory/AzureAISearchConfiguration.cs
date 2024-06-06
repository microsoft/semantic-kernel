// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings.Memory;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class AzureAISearchConfiguration(string serviceUrl, string apiKey)
{
    public string ServiceUrl { get; set; } = serviceUrl;

    public string ApiKey { get; set; } = apiKey;
}
