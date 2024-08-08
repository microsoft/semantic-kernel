// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class AzureAIInferenceConfiguration(string? serviceId, Uri endpoint, string apiKey)
{
    public string? ServiceId { get; set; } = serviceId;
    public Uri Endpoint { get; set; } = endpoint;
    public string ApiKey { get; set; } = apiKey;
}
