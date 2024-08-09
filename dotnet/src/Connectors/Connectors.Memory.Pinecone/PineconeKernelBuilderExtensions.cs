// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Pinecone;
using Microsoft.SemanticKernel.Data;
using Sdk = Pinecone;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Pinecone <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
public static class PineconeKernelBuilderExtensions
{
    /// <summary>
    /// Register a Pinecone <see cref="IVectorStore"/> with the specified service ID and where <see cref="Sdk.PineconeClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddPineconeVectorStore(this IKernelBuilder builder, PineconeVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddPineconeVectorStore(options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Pinecone <see cref="IVectorStore"/> with the specified service ID and where <see cref="Sdk.PineconeClient"/> is constructed using the provided apikey.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="apiKey">The api key for Pinecone.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddPineconeVectorStore(this IKernelBuilder builder, string apiKey, PineconeVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddPineconeVectorStore(apiKey, options, serviceId);
        return builder;
    }
}
