// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class OpenAIConfiguration
{
    public string ServiceId { get; set; }
    public string ModelId { get; set; }
    public string? ChatModelId { get; set; }
    public string ApiKey { get; set; }

    public OpenAIConfiguration(string serviceId, string modelId, string apiKey, string? chatModelId = null)
    {
        this.ServiceId = serviceId;
        this.ModelId = modelId;
        this.ChatModelId = chatModelId;
        this.ApiKey = apiKey;
    }
}
