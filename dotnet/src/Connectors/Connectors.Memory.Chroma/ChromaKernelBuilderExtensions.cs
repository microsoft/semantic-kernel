// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

public static class ChromaKernelBuilderExtensions
{
    public static KernelBuilder WithChromaMemoryStore(this KernelBuilder builder, string endpoint)
    {
        builder.WithMemoryStorage((parameters) =>
        {
            return new ChromaMemoryStore(
                HttpClientProvider.GetHttpClient(parameters.Config, null, parameters.Logger),
                endpoint,
                parameters.Logger);
        });

        return builder;
    }

    public static KernelBuilder WithChromaMemoryStore(this KernelBuilder builder,
        HttpClient httpClient,
        string? endpoint = null,
        string? apiKey = null)
    {
        builder.WithMemoryStorage((parameters) =>
        {
            return new ChromaMemoryStore(
                HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger),
                endpoint,
                parameters.Logger);
        });

        return builder;
    }
}
