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
    /// <param name="kernelSettings"></param>
    /// <exception cref="ArgumentException"></exception>
    internal static IServiceCollection WithChatCompletionService(this IServiceCollection kernelBuilder, KernelSettings kernelSettings)
    {
        switch (kernelSettings.ServiceType.ToUpperInvariant())
        {
            case ServiceTypes.AzureOpenAI:
                kernelBuilder.AddAzureOpenAIChatCompletion(deploymentName: kernelSettings.DeploymentOrModelId, modelId: kernelSettings.DeploymentOrModelId, endpoint: kernelSettings.Endpoint, apiKey: kernelSettings.ApiKey, serviceId: kernelSettings.ServiceId);
                break;

            case ServiceTypes.OpenAI:
                kernelBuilder.AddOpenAIChatCompletion(modelId: kernelSettings.DeploymentOrModelId, apiKey: kernelSettings.ApiKey, orgId: kernelSettings.OrgId, serviceId: kernelSettings.ServiceId);
                break;

            default:
                throw new ArgumentException($"Invalid service type value: {kernelSettings.ServiceType}");
        }

        return kernelBuilder;
    }
}
