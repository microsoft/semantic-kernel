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
    /// <summary>Add Amazon Bedrock <see cref="IChatClient"/> to the <see cref="IServiceCollection" />.</summary>
    /// <param name="services">The service collection.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="bedrockRuntime">The optional <see cref="IAmazonBedrockRuntime" /> to use. If not provided will be retrieved from the Service Collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="openTelemetrySourceName">An optional source name that will be used on the telemetry data.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>Returns back <see cref="IServiceCollection"/> with a configured service.</returns>
    public static IServiceCollection AddBedrockChatClient(
        this IServiceCollection services,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        if (bedrockRuntime is null)
        {
            // Add IAmazonBedrockRuntime service client to the DI container
            services.TryAddAWSService<IAmazonBedrockRuntime>();
        }

        services.AddKeyedSingleton<IChatClient>(serviceId, (serviceProvider, _) =>
        {
            try
            {
                IAmazonBedrockRuntime runtime = bedrockRuntime ?? serviceProvider.GetRequiredService<IAmazonBedrockRuntime>();
                var loggerFactory = serviceProvider.GetService<ILoggerFactory>();
                // Check if the runtime instance is a proxy object
                if (runtime.GetType().BaseType == typeof(AmazonServiceClient))
                {
                    // Cast to AmazonServiceClient and subscribe to the event
                    ((AmazonServiceClient)runtime).BeforeRequestEvent += BedrockClientUtilities.BedrockServiceClientRequestHandler;
                }
                var builder = runtime
                    .AsIChatClient(modelId)
                    .AsBuilder();

                if (loggerFactory is not null)
                {
                    builder.UseLogging(loggerFactory);
                }

                builder.UseOpenTelemetry(loggerFactory, openTelemetrySourceName, openTelemetryConfig);

                return builder
                    .UseKernelFunctionInvocation(loggerFactory)
                    .Build(serviceProvider);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the Bedrock {nameof(IChatClient)}: {ex.Message}", ex);
            }
        });

        return services;
    }

    /// <summary>
    /// Add Amazon Bedrock <see cref="IEmbeddingGenerator"/> to the <see cref="IServiceCollection" />.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="modelId">The model for embedding generation.</param>
    /// <param name="bedrockRuntime">The optional <see cref="IAmazonBedrockRuntime" /> to use. If not provided will be retrieved from the Service Collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="openTelemetrySourceName">An optional source name that will be used on the telemetry data.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryEmbeddingGenerator{String, Embedding}"/> instance.</param>
    /// <returns>Returns back <see cref="IServiceCollection"/> with a configured <see cref="IEmbeddingGenerator"/>.</returns>
    public static IServiceCollection AddBedrockEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryEmbeddingGenerator<string, Embedding<float>>>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        if (bedrockRuntime is null)
        {
            // Add IAmazonBedrockRuntime service client to the DI container
            services.TryAddAWSService<IAmazonBedrockRuntime>();
        }
        services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
        {
            try
            {
                IAmazonBedrockRuntime runtime = bedrockRuntime ?? serviceProvider.GetRequiredService<IAmazonBedrockRuntime>();
                var loggerFactory = serviceProvider.GetService<ILoggerFactory>();
                // Check if the runtime instance is a proxy object
                if (runtime.GetType().BaseType == typeof(AmazonServiceClient))
                {
                    // Cast to AmazonServiceClient and subscribe to the event
                    ((AmazonServiceClient)runtime).BeforeRequestEvent += BedrockClientUtilities.BedrockServiceClientRequestHandler;
                }

                var builder = runtime.AsIEmbeddingGenerator(modelId).AsBuilder();

                if (loggerFactory is not null)
                {
                    builder.UseLogging(loggerFactory);
                }

                builder.UseOpenTelemetry(loggerFactory, openTelemetrySourceName, openTelemetryConfig);

                return builder.Build(serviceProvider);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the {nameof(IEmbeddingGenerator)}: {ex.Message}", ex);
            }
        });

        return services;
    }
}
