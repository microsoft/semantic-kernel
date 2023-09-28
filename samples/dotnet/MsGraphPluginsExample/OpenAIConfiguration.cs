// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace MsGraphPluginsExample;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class OpenAIConfiguration
{
    public string ServiceId { get; set; }
    public string ModelId { get; set; }
    public string ApiKey { get; set; }

    public OpenAIConfiguration(string serviceId, string modelId, string apiKey)
    {
        this.ServiceId = serviceId;
        this.ModelId = modelId;
        this.ApiKey = apiKey;
    }
}
