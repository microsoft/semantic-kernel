// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Azure.Identity;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Reliability;

namespace SemanticKernel.Service.Config;

internal static class ConfigExtensions
{
    public static IHostBuilder AddConfiguration(this IHostBuilder host)
    {
        string? environment = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT");

        host.ConfigureAppConfiguration((builderContext, configBuilder) =>
        {
            configBuilder.AddJsonFile(
                path: "appsettings.json",
                optional: false,
                reloadOnChange: true);

            configBuilder.AddJsonFile(
                path: $"appsettings.{environment}.json",
                optional: true,
                reloadOnChange: true);

            configBuilder.AddEnvironmentVariables();

            configBuilder.AddUserSecrets(
                assembly: Assembly.GetExecutingAssembly(),
                optional: true,
                reloadOnChange: true);

            // For settings from Key Vault, see https://learn.microsoft.com/en-us/aspnet/core/security/key-vault-configuration?view=aspnetcore-8.0
            string? keyVaultUri = builderContext.Configuration["KeyVaultUri"];
            if (!string.IsNullOrWhiteSpace(keyVaultUri))
            {
                configBuilder.AddAzureKeyVault(
                    new Uri(keyVaultUri),
                    new DefaultAzureCredential());

                // for more information on how to use DefaultAzureCredential, see https://learn.microsoft.com/en-us/dotnet/api/azure.identity.defaultazurecredential?view=azure-dotnet
            }
        });

        return host;
    }

    public static KernelConfig AddCompletionBackend(this KernelConfig kernelConfig, IOptionsSnapshot<AIServiceOptions> aiServiceOptions)
    {
        AIServiceOptions config = aiServiceOptions.Get(AIServiceOptions.CompletionPropertyName);

        switch (config.AIService)
        {
            case AIServiceOptions.AIServiceType.AzureOpenAI:
                kernelConfig.AddAzureChatCompletionService(
                    serviceId: config.Label,
                    deploymentName: config.DeploymentOrModelId,
                    endpoint: config.Endpoint,
                    apiKey: config.Key,
                    alsoAsTextCompletion: true);
                break;

            case AIServiceOptions.AIServiceType.OpenAI:
                kernelConfig.AddOpenAIChatCompletionService(
                    serviceId: config.Label,
                    modelId: config.DeploymentOrModelId,
                    apiKey: config.Key,
                    alsoAsTextCompletion: true);
                break;

            default:
                throw new ArgumentException($"Invalid {nameof(config.AIService)} value in '{AIServiceOptions.CompletionPropertyName}' settings.");
        }

        return kernelConfig;
    }

    public static KernelConfig AddEmbeddingBackend(this KernelConfig kernelConfig, IOptionsSnapshot<AIServiceOptions> aiServiceOptions)
    {
        AIServiceOptions config = aiServiceOptions.Get(AIServiceOptions.EmbeddingPropertyName);

        switch (config.AIService)
        {
            case AIServiceOptions.AIServiceType.AzureOpenAI:
                kernelConfig.AddAzureTextEmbeddingGenerationService(
                    serviceId: config.Label,
                    deploymentName: config.DeploymentOrModelId,
                    endpoint: config.Endpoint,
                    apiKey: config.Key);
                break;

            case AIServiceOptions.AIServiceType.OpenAI:
                kernelConfig.AddOpenAITextEmbeddingGenerationService(
                    serviceId: config.Label,
                    modelId: config.DeploymentOrModelId,
                    apiKey: config.Key);
                break;

            default:
                throw new ArgumentException($"Invalid {nameof(config.AIService)} value in '{AIServiceOptions.EmbeddingPropertyName}' settings.");
        }

        return kernelConfig;
    }

    public static IEmbeddingGeneration<string, float> ToTextEmbeddingsService(this AIServiceOptions serviceConfig,
        ILogger? logger = null,
        IDelegatingHandlerFactory? handlerFactory = null)
    {
        return serviceConfig.AIService switch
        {
            AIServiceOptions.AIServiceType.AzureOpenAI => new AzureTextEmbeddingGeneration(
                serviceConfig.DeploymentOrModelId,
                serviceConfig.Endpoint,
                serviceConfig.Key,
                handlerFactory: handlerFactory,
                log: logger),

            AIServiceOptions.AIServiceType.OpenAI => new OpenAITextEmbeddingGeneration(
                serviceConfig.DeploymentOrModelId, serviceConfig.Key, handlerFactory: handlerFactory, log: logger),

            _ => throw new ArgumentException("Invalid AIService value in embeddings backend settings"),
        };
    }
}
