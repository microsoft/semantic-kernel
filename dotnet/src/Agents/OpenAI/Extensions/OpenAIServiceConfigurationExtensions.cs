// Copyright (c) Microsoft. All rights reserved.
using OpenAI;
using OpenAI.Files;
using OpenAI.VectorStores;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Extensions;

/// <summary>
/// %%%
/// </summary>
public static class OpenAIServiceConfigurationExtensions
{
    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="configuration"></param>
    /// <returns></returns>
    public static FileClient CreateFileClient(this OpenAIServiceConfiguration configuration)
    {
        OpenAIClient client = OpenAIClientFactory.CreateClient(configuration);

        return client.GetFileClient();
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="configuration"></param>
    /// <returns></returns>
    public static VectorStoreClient CreateVectorStoreClient(this OpenAIServiceConfiguration configuration)
    {
        OpenAIClient client = OpenAIClientFactory.CreateClient(configuration);

        return client.GetVectorStoreClient();
    }
}
