// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Amazon.BedrockRuntime;
using Amazon.Runtime;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding Bedrock services to the application.
/// </summary>
public static class BedrockKernelBuilderExtensions
{
    /// <summary>
    /// Add Amazon Bedrock Chat Completion service to the kernel builder using IAmazonBedrockRuntime object.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="bedrockRuntime">The IAmazonBedrockRuntime to run inference using the respective model.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns></returns>
    public static IKernelBuilder AddBedrockChatCompletionService(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null)
    {
        if (bedrockRuntime == null)
        {
            // Add IAmazonBedrockRuntime service client to the DI container
            builder.Services.TryAddAWSService<IAmazonBedrockRuntime>();
        }

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            try
            {
                IAmazonBedrockRuntime runtime = bedrockRuntime ?? serviceProvider.GetRequiredService<IAmazonBedrockRuntime>();
                var logger = serviceProvider.GetService<ILoggerFactory>();
                // Check if the runtime instance is a proxy object
                if (runtime.GetType().BaseType == typeof(AmazonServiceClient))
                {
                    // Cast to AmazonServiceClient and subscribe to the event
                    ((AmazonServiceClient)runtime).BeforeRequestEvent += AWSServiceClient_BeforeServiceRequest;
                }
                return new BedrockChatCompletionService(modelId, runtime, logger);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the {nameof(BedrockChatCompletionService)}: {ex.Message}", ex);
            }
        });

        return builder;
    }

    /// <summary>
    /// Add Amazon Bedrock Text Generation service to the kernel builder using IAmazonBedrockRuntime object.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bedrockRuntime">The IAmazonBedrockRuntime to run inference using the respective model.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns></returns>
    public static IKernelBuilder AddBedrockTextGenerationService(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null)
    {
        if (bedrockRuntime == null)
        {
            // Add IAmazonBedrockRuntime service client to the DI container
            builder.Services.TryAddAWSService<IAmazonBedrockRuntime>();
        }
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
        {
            try
            {
                IAmazonBedrockRuntime runtime = bedrockRuntime ?? serviceProvider.GetRequiredService<IAmazonBedrockRuntime>();
                var logger = serviceProvider.GetService<ILoggerFactory>();
                // Check if the runtime instance is a proxy object
                if (runtime.GetType().BaseType == typeof(AmazonServiceClient))
                {
                    // Cast to AmazonServiceClient and subscribe to the event
                    ((AmazonServiceClient)runtime).BeforeRequestEvent += AWSServiceClient_BeforeServiceRequest;
                }
                return new BedrockTextGenerationService(modelId, runtime, logger);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the {nameof(BedrockTextGenerationService)}: {ex.Message}", ex);
            }
        });

        return builder;
    }

    private const string UserAgentHeader = "User-Agent";
    private static readonly string s_userAgentString = $"lib/semantic-kernel#{Assembly.GetExecutingAssembly().GetName().Version?.ToString() ?? string.Empty}";

    internal static void AWSServiceClient_BeforeServiceRequest(object sender, RequestEventArgs e)
    {
        if (e is not WebServiceRequestEventArgs args || !args.Headers.TryGetValue(UserAgentHeader, out string? value) || value.Contains(s_userAgentString))
        {
            return;
        }
        args.Headers[UserAgentHeader] = $"{value} {s_userAgentString}";
    }
}
