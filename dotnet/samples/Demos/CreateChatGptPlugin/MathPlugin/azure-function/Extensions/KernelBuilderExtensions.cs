// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Models;

internal static class KernelBuilderExtensions
{
    /// <summary>
    /// Adds a chat completion service to the list. It can be either an OpenAI or Azure OpenAI backend service.
    /// </summary>
    /// <param name="kernelBuilder"></param>
    /// <param name="serviceSettings"></param>
    /// <exception cref="ArgumentException"></exception>
    internal static IServiceCollection WithChatCompletionService(this IServiceCollection kernelBuilder, AIServiceSettings serviceSettings)
    {
        switch (serviceSettings.ServiceType.ToUpperInvariant())
        {
            case ServiceTypes.AzureOpenAI:
                kernelBuilder.AddAzureOpenAIChatCompletion(deploymentName: serviceSettings.DeploymentOrModelId, modelId: serviceSettings.DeploymentOrModelId, endpoint: serviceSettings.Endpoint, apiKey: serviceSettings.ApiKey, serviceId: serviceSettings.ServiceId);
                break;

            case ServiceTypes.OpenAI:
                kernelBuilder.AddOpenAIChatCompletion(modelId: serviceSettings.DeploymentOrModelId, apiKey: serviceSettings.ApiKey, orgId: serviceSettings.OrgId, serviceId: serviceSettings.ServiceId);
                break;

            default:
                throw new ArgumentException($"Invalid service type value: {serviceSettings.ServiceType}");
        }

        return kernelBuilder;
    }
}
