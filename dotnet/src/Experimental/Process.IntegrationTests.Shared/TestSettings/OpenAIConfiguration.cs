// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class OpenAIConfiguration(string serviceId, string modelId, string apiKey, string? chatModelId = null)
{
    public string ServiceId { get; set; } = serviceId;
    public string ModelId { get; set; } = modelId;
    public string? ChatModelId { get; set; } = chatModelId;
    public string ApiKey { get; set; } = apiKey;
}
