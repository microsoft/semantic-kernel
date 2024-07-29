// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Amazon.Extensions.NETCore.Setup;
using Amazon.Runtime;
using Connectors.Amazon.Services;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Services;
using Microsoft.SemanticKernel.TextGeneration;

namespace Connectors.Amazon.Extensions;

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
    /// <param name="bedrockApi">The IAmazonBedrockRuntime to run inference using the respective model.</param>
    /// <returns></returns>
    public static IKernelBuilder AddBedrockChatCompletionService(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime bedrockApi)
    {
        builder.Services.AddSingleton<IChatCompletionService>(_ =>
        {
            try
            {
                return new BedrockChatCompletionService(modelId, bedrockApi);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the BedrockChatCompletionService: {ex.Message}", ex);
            }
        });

        return builder;
    }

    /// <summary>
    /// Add Amazon Bedrock Chat Completion service to the kernel builder using new AmazonBedrockRuntimeClient().
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <returns></returns>
    public static IKernelBuilder AddBedrockChatCompletionService(
        this IKernelBuilder builder,
        string modelId)
    {
        // Add IAmazonBedrockRuntime service client to the DI container
        builder.Services.AddAWSService<IAmazonBedrockRuntime>();
        builder.Services.AddSingleton<IChatCompletionService>(services =>
        {
            try
            {
                var bedrockRuntime = services.GetRequiredService<IAmazonBedrockRuntime>();
                return new BedrockChatCompletionService(modelId, bedrockRuntime);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the BedrockChatCompletionService: {ex.Message}", ex);
            }
        });

        return builder;
    }
    /// <summary>
    /// Chat completion service that uses AWS credentials to authenticate.
    /// </summary>
    /// <param name="builder"></param>
    /// <param name="modelId"></param>
    /// <param name="awsCredentials"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public static IKernelBuilder AddBedrockChatCompletionService(
        this IKernelBuilder builder,
        string modelId,
        AWSCredentials awsCredentials)
    {
        // Create AWSOptions with the provided credentials
        var awsOptions = new AWSOptions
        {
            Credentials = awsCredentials
        };
        // Add IAmazonBedrockRuntime service client to the DI container
        builder.Services.AddAWSService<IAmazonBedrockRuntime>(awsOptions);

        builder.Services.AddSingleton<IChatCompletionService>(services =>
        {
            try
            {
                var bedrockRuntime = services.GetRequiredService<IAmazonBedrockRuntime>();
                return new BedrockChatCompletionService(modelId, bedrockRuntime);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the BedrockChatCompletionService: {ex.Message}", ex);
            }
        });

        return builder;
    }
    /// <summary>
    /// Chat completion service that uses access keys and token.
    /// </summary>
    /// <param name="builder"></param>
    /// <param name="modelId"></param>
    /// <param name="awsAccessKeyId"></param>
    /// <param name="awsSecretAccessKey"></param>
    /// <param name="token"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public static IKernelBuilder AddBedrockChatCompletionService(
        this IKernelBuilder builder,
        string modelId,
        string awsAccessKeyId,
        string awsSecretAccessKey,
        string token)
    {
        // Create AWSOptions with the provided credentials
        var awsOptions = new AWSOptions
        {
            Credentials = new SessionAWSCredentials(awsAccessKeyId, awsSecretAccessKey, token)
        };
        // Add IAmazonBedrockRuntime service client to the DI container
        builder.Services.AddAWSService<IAmazonBedrockRuntime>(awsOptions);

        builder.Services.AddSingleton<IChatCompletionService>(services =>
        {
            try
            {
                var bedrockRuntime = services.GetRequiredService<IAmazonBedrockRuntime>();
                return new BedrockChatCompletionService(modelId, bedrockRuntime);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the BedrockChatCompletionService: {ex.Message}", ex);
            }
        });

        return builder;
    }
    /// <summary>
    /// Add Amazon Bedrock Text Generation service to the kernel builder using IAmazonBedrockRuntime object.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bedrockApi">The IAmazonBedrockRuntime to run inference using the respective model.</param>
    /// <returns></returns>
    public static IKernelBuilder AddBedrockTextGenerationService(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime bedrockApi)
    {
        builder.Services.AddSingleton<ITextGenerationService>(_ =>
        {
            try
            {
                return new BedrockTextGenerationService(modelId, bedrockApi);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the BedrockTextGenerationService: {ex.Message}", ex);
            }
        });

        return builder;
    }
    /// <summary>
    /// Add Amazon Bedrock Text Generation service to the kernel builder using new AmazonBedrockRuntimeClient().
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <returns></returns>
    public static IKernelBuilder AddBedrockTextGenerationService(
        this IKernelBuilder builder,
        string modelId)
    {
        // Add IAmazonBedrockRuntime service client to the DI container
        builder.Services.AddAWSService<IAmazonBedrockRuntime>();
        builder.Services.AddSingleton<ITextGenerationService>(services =>
        {
            try
            {
                var bedrockRuntime = services.GetRequiredService<IAmazonBedrockRuntime>();
                return new BedrockTextGenerationService(modelId, bedrockRuntime);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the BedrockTextGenerationService: {ex.Message}", ex);
            }
        });

        return builder;
    }
    /// <summary>
    /// Add Amazon Bedrock Chat Completion service to the kernel builder using awsCredentials.
    /// </summary>
    /// <param name="builder"></param>
    /// <param name="modelId"></param>
    /// <param name="awsCredentials"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public static IKernelBuilder AddBedrockTextGenerationService(
        this IKernelBuilder builder,
        string modelId,
        AWSCredentials awsCredentials)
    {
        // Create AWSOptions with the provided credentials
        var awsOptions = new AWSOptions
        {
            Credentials = awsCredentials
        };
        // Add IAmazonBedrockRuntime service client to the DI container
        builder.Services.AddAWSService<IAmazonBedrockRuntime>(awsOptions);

        builder.Services.AddSingleton<ITextGenerationService>(services =>
        {
            try
            {
                var bedrockRuntime = services.GetRequiredService<IAmazonBedrockRuntime>();
                return new BedrockTextGenerationService(modelId, bedrockRuntime);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the BedrockTextGenerationService: {ex.Message}", ex);
            }
        });

        return builder;
    }
    /// <summary>
    /// Add Amazon Bedrock Chat Completion service to the kernel builder using secret keys and tokens.
    /// </summary>
    /// <param name="builder"></param>
    /// <param name="modelId"></param>
    /// <param name="awsAccessKeyId"></param>
    /// <param name="awsSecretAccessKey"></param>
    /// <param name="token"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public static IKernelBuilder AddBedrockTextGenerationService(
        this IKernelBuilder builder,
        string modelId,
        string awsAccessKeyId,
        string awsSecretAccessKey,
        string token)
    {
        // Create AWSOptions with the provided credentials
        var awsOptions = new AWSOptions
        {
            Credentials = new SessionAWSCredentials(awsAccessKeyId, awsSecretAccessKey, token)
        };
        // Add IAmazonBedrockRuntime service client to the DI container
        builder.Services.AddAWSService<IAmazonBedrockRuntime>(awsOptions);

        builder.Services.AddSingleton<ITextGenerationService>(services =>
        {
            try
            {
                var bedrockRuntime = services.GetRequiredService<IAmazonBedrockRuntime>();
                return new BedrockTextGenerationService(modelId, bedrockRuntime);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the BedrockTextGenerationService: {ex.Message}", ex);
            }
        });

        return builder;
    }
}
