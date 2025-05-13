// Copyright (c) Microsoft. All rights reserved.

using System;
using Amazon.BedrockRuntime;
using Amazon.Runtime;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extensions for adding Bedrock modality services to the service collection.
/// </summary>
public static class BedrockServiceCollectionExtensions
{
    /// <summary>
    /// Add Amazon Bedrock Embedding Generator service to the <see cref="IServiceCollection" />.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bedrockRuntime">The optional <see cref="IAmazonBedrockRuntime" /> to use. If not provided will be retrieved from the Service Collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>Returns back <see cref="IServiceCollection"/> with a configured service.</returns>
    public static IServiceCollection AddBedrockEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null)
    {
        if (bedrockRuntime == null)
        {
            // Add IAmazonBedrockRuntime service client to the DI container
            services.TryAddAWSService<IAmazonBedrockRuntime>();
        }
        services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
        {
            try
            {
                IAmazonBedrockRuntime runtime = bedrockRuntime ?? serviceProvider.GetRequiredService<IAmazonBedrockRuntime>();
                var logger = serviceProvider.GetService<ILoggerFactory>();
                // Check if the runtime instance is a proxy object
                if (runtime.GetType().BaseType == typeof(AmazonServiceClient))
                {
                    // Cast to AmazonServiceClient and subscribe to the event
                    ((AmazonServiceClient)runtime).BeforeRequestEvent += BedrockClientUtilities.BedrockServiceClientRequestHandler;
                }
                return runtime.AsIEmbeddingGenerator(modelId);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the {nameof(IEmbeddingGenerator)}: {ex.Message}", ex);
            }
        });

        return services;
    }
}
