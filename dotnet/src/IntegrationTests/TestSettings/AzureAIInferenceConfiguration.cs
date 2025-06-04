// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class AzureAIInferenceConfiguration(Uri endpoint, string apiKey, string? serviceId = null, string? chatModelId = null, string? embeddingModelId = null)
{
    public Uri Endpoint { get; set; } = endpoint;
    public string? ApiKey { get; set; } = apiKey;
    public string? ServiceId { get; set; } = serviceId;
    public string? ChatModelId { get; set; } = chatModelId;
    public string? EmbeddingModelId { get; set; } = embeddingModelId;
}

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class AzureAIInferenceEmbeddingsConfiguration(Uri endpoint, string? apiKey = null, string? serviceId = null, string? deploymentName = null)
{
    public Uri Endpoint { get; set; } = endpoint;
    public string? ApiKey { get; set; } = apiKey;
    public string? ServiceId { get; set; } = serviceId;
    public string? ModelId { get; set; } = deploymentName;
}
