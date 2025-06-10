// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class AzureAIConfiguration(string endpoint, string chatModelId)
{
    public string Endpoint { get; set; } = endpoint;

    public string ChatModelId { get; set; } = chatModelId;
}
