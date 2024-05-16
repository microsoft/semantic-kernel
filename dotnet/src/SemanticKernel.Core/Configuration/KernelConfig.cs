// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.Configuration;

namespace Microsoft.SemanticKernel;

public class KernelConfig
{
    public string TextGenerationType { get; set; } = string.Empty;

    public string EmbeddingGeneratorType { get; set; } = string.Empty;

    public string ChatCompletionType { get; set; } = string.Empty;

    public string TextToImageType { get; set; } = string.Empty;

    public string FilesType { get; set; } = string.Empty;

    public string TextToAudioType { get; set; } = string.Empty;

    public string AudioToTextType { get; set; } = string.Empty;

    /// <summary>
    /// Dependencies settings, e.g. credentials, endpoints, etc.
    /// </summary>
    public Dictionary<string, Dictionary<string, object>> Services { get; set; } = new();

    /// <summary>
    /// Fetch a service configuration from the "Services" node
    /// </summary>
    /// <param name="cfg">Configuration instance</param>
    /// <param name="serviceName">Service name</param>
    /// <param name="root">Root node name of the Kernel Memory config</param>
    /// <typeparam name="T">Type of configuration to retrieve</typeparam>
    /// <returns>Instance of T configuration class</returns>
    public T GetServiceConfig<T>(IConfiguration cfg, string serviceName, string root = "Kernel")
    {
        return cfg
            .GetSection(root)
            .GetSection("Services")
            .GetSection(serviceName)
            .Get<T>() ?? throw new ConfigurationException($"The {serviceName} configuration is NULL");
    }
}
