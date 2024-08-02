// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using OpenAI;
using OpenAI.Files;
using OpenAI.VectorStores;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Extension method for creating OpenAI clients from a <see cref="OpenAIServiceConfiguration"/>.
/// </summary>
public static class OpenAIServiceConfigurationExtensions
{
    /// <summary>
    /// Provide a newly created <see cref="FileClient"/> based on the specified configuration.
    /// </summary>
    /// <param name="configuration">The configuration</param>
    public static FileClient CreateFileClient(this OpenAIServiceConfiguration configuration)
        => OpenAIClientFactory.CreateClient(configuration).GetFileClient();

    /// <summary>
    /// Provide a newly created <see cref="VectorStoreClient"/> based on the specified configuration.
    /// </summary>
    /// <param name="configuration">The configuration</param>
    public static VectorStoreClient CreateVectorStoreClient(this OpenAIServiceConfiguration configuration)
        => OpenAIClientFactory.CreateClient(configuration).GetVectorStoreClient();
}
