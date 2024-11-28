// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class AzureAIInferenceConfiguration(Uri endpoint, string apiKey, string? serviceId = null, string? chatModelId = null)
{
    public Uri Endpoint { get; set; } = endpoint;
    public string? ApiKey { get; set; } = apiKey;
    public string? ServiceId { get; set; } = serviceId;
    public string? ChatModelId { get; set; } = chatModelId;
}
