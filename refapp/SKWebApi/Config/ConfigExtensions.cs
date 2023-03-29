// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.OpenAI.Services;
using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Reliability;

namespace SemanticKernel.Service.Config;

internal static class ConfigExtensions
{
    public static IHostBuilder ConfigureAppSettings(this IHostBuilder host)
    {
        string? enviroment = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT");

        host.ConfigureAppConfiguration((ctx, builder) =>
        {
            builder.AddJsonFile("appsettings.json", false, true);
            builder.AddJsonFile($"appsettings.{enviroment}.json", true, true);
            builder.AddEnvironmentVariables();
            // For settings from Key Vault, see https://learn.microsoft.com/en-us/aspnet/core/security/key-vault-configuration?view=aspnetcore-7.0
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
                kernelConfig.AddAzureOpenAICompletionBackend(serviceConfig.Label, serviceConfig.DeploymentOrModelId,
                                                             serviceConfig.Endpoint, serviceConfig.Key);
                break;

            case AIServiceConfig.OpenAI:
                kernelConfig.AddOpenAICompletionBackend(serviceConfig.Label, serviceConfig.DeploymentOrModelId,
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
                kernelConfig.AddAzureOpenAIEmbeddingsBackend(serviceConfig.Label, serviceConfig.DeploymentOrModelId,
                                                             serviceConfig.Endpoint, serviceConfig.Key);
                break;

            case AIServiceConfig.OpenAI:
                kernelConfig.AddOpenAIEmbeddingsBackend(serviceConfig.Label, serviceConfig.DeploymentOrModelId,
                                                        serviceConfig.Key);
                break;

            default:
                throw new ArgumentException("Invalid AIService value in embedding backend settings");
        }
    }

    public static IEmbeddingGenerator<string, float> ToTextEmbeddingsService(this AIServiceConfig serviceConfig,
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
                return new AzureTextEmbeddings(serviceConfig.DeploymentOrModelId, serviceConfig.Endpoint,
                                               serviceConfig.Key, "2022-12-01", logger, handlerFactory);

            case AIServiceConfig.OpenAI:
                return new OpenAITextEmbeddings(serviceConfig.DeploymentOrModelId, serviceConfig.Key,
                                                log: logger, handlerFactory: handlerFactory);

            default:
                throw new ArgumentException("Invalid AIService value in embeddings backend settings");
        }
    }
}
