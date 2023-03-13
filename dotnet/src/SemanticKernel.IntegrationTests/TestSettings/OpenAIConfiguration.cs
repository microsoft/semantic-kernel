// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class OpenAIConfiguration
{
    public string Label { get; set; }
    public string ModelId { get; set; }
    public string ApiKey { get; set; }

    public OpenAIConfiguration(string label, string modelId, string apiKey)
    {
        this.Label = label;
        this.ModelId = modelId;
        this.ApiKey = apiKey;
    }
}
