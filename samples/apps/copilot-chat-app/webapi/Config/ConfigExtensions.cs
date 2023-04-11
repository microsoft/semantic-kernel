// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.OpenAI.TextEmbedding;
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
                kernelConfig.AddAzureOpenAITextCompletionService(serviceConfig.Label, serviceConfig.DeploymentOrModelId,
                    serviceConfig.Endpoint, serviceConfig.Key);
                break;

            case AIServiceConfig.OpenAI:
                kernelConfig.AddOpenAITextCompletionService(serviceConfig.Label, serviceConfig.DeploymentOrModelId,
                    serviceConfig.Key);
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
                kernelConfig.AddAzureOpenAIEmbeddingGenerationService(serviceConfig.Label, serviceConfig.DeploymentOrModelId,
                    serviceConfig.Endpoint, serviceConfig.Key);
                break;

            case AIServiceConfig.OpenAI:
                kernelConfig.AddOpenAIEmbeddingGenerationService(serviceConfig.Label, serviceConfig.DeploymentOrModelId,
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

        switch (serviceConfig.AIService.ToUpperInvariant())
        {
            case AIServiceConfig.AzureOpenAI:
                return new AzureTextEmbeddingGeneration(serviceConfig.DeploymentOrModelId, serviceConfig.Endpoint,
                    serviceConfig.Key, "2022-12-01", logger, handlerFactory);

            case AIServiceConfig.OpenAI:
                return new OpenAITextEmbeddingGeneration(serviceConfig.DeploymentOrModelId, serviceConfig.Key,
                    log: logger, handlerFactory: handlerFactory);

            default:
                throw new ArgumentException("Invalid AIService value in embeddings backend settings");
        }
    }
}
