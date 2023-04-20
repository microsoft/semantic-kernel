// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Reliability;

namespace SemanticKernel.Service.Config;

internal static class ConfigExtensions
{
    public static IHostBuilder ConfigureAppSettings(this IHostBuilder host)
    {
        string? environment = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT");

        host.ConfigureAppConfiguration((ctx, builder) =>
        {
            builder.AddJsonFile("appsettings.json", false, true);
            builder.AddJsonFile($"appsettings.{environment}.json", true, true);
            builder.AddEnvironmentVariables();
            builder.AddUserSecrets(Assembly.GetExecutingAssembly(), optional: true, reloadOnChange: true);
            // For settings from Key Vault, see https://learn.microsoft.com/en-us/aspnet/core/security/key-vault-configuration?view=aspnetcore-8.0
            string? keyVaultUri = ctx.Configuration["KeyVaultUri"];
            if (!string.IsNullOrWhiteSpace(keyVaultUri))
            {
                builder.AddAzureKeyVault(
                    new Uri(keyVaultUri),
                    new DefaultAzureCredential());

                /* See https://learn.microsoft.com/en-us/dotnet/api/azure.identity.defaultazurecredential?view=azure-dotnet
                   for more information on how to use DefaultAzureCredential */
            }
        });

        return host;
    }

    public static void AddCompletionBackend(this KernelConfig kernelConfig, AIServiceConfig serviceConfig)
    {
        if (!serviceConfig.IsValid())
        {
            throw new ArgumentException("The provided completion backend settings are not valid");
        }

        switch (serviceConfig.AIService.ToUpperInvariant())
        {
            case AIServiceConfig.AzureOpenAI:
                kernelConfig.AddAzureChatCompletionService(
                    serviceId: serviceConfig.Label,
                    deploymentName: serviceConfig.DeploymentOrModelId,
                    endpoint: serviceConfig.Endpoint,
                    apiKey: serviceConfig.Key,
                    alsoAsTextCompletion: true);
                break;

            case AIServiceConfig.OpenAI:
                kernelConfig.AddOpenAIChatCompletionService(
                    serviceId: serviceConfig.Label,
                    modelId: serviceConfig.DeploymentOrModelId,
                    apiKey: serviceConfig.Key,
                    alsoAsTextCompletion: true);
                break;

            default:
                throw new ArgumentException("Invalid AIService value in completion backend settings");
        }
    }

    public static void AddEmbeddingBackend(this KernelConfig kernelConfig, AIServiceConfig serviceConfig)
    {
        if (!serviceConfig.IsValid())
        {
            throw new ArgumentException("The provided embeddings backend settings are not valid");
        }

        switch (serviceConfig.AIService.ToUpperInvariant())
        {
            case AIServiceConfig.AzureOpenAI:
                kernelConfig.AddAzureTextEmbeddingGenerationService(serviceConfig.Label, serviceConfig.DeploymentOrModelId,
                    serviceConfig.Endpoint, serviceConfig.Key);
                break;

            case AIServiceConfig.OpenAI:
                kernelConfig.AddOpenAITextEmbeddingGenerationService(serviceConfig.Label, serviceConfig.DeploymentOrModelId,
                    serviceConfig.Key);
                break;

            default:
                throw new ArgumentException("Invalid AIService value in embedding backend settings");
        }
    }

    public static IEmbeddingGeneration<string, float> ToTextEmbeddingsService(this AIServiceConfig serviceConfig,
        ILogger? logger = null,
        IDelegatingHandlerFactory? handlerFactory = null)
    {
        if (!serviceConfig.IsValid())
        {
            throw new ArgumentException("The provided embeddings backend settings are not valid");
        }

        return serviceConfig.AIService.ToUpperInvariant() switch
        {
            AIServiceConfig.AzureOpenAI => new AzureTextEmbeddingGeneration(
                serviceConfig.DeploymentOrModelId,
                serviceConfig.Endpoint,
                serviceConfig.Key,
                handlerFactory: handlerFactory,
                log: logger),

            AIServiceConfig.OpenAI => new OpenAITextEmbeddingGeneration(
                serviceConfig.DeploymentOrModelId, serviceConfig.Key, handlerFactory: handlerFactory, log: logger),

            _ => throw new ArgumentException("Invalid AIService value in embeddings backend settings"),
        };
    }
}
