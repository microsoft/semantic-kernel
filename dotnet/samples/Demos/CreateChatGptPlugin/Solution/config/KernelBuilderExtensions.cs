// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

internal static class KernelBuilderExtensions
{
    /// <summary>
    /// Adds a text completion service to the list. It can be either an OpenAI or Azure OpenAI backend service.
    /// </summary>
    /// <param name="kernelBuilder"></param>
    /// <exception cref="ArgumentException"></exception>
    internal static IKernelBuilder WithCompletionService(this IKernelBuilder kernelBuilder)
    {
        switch (Env.Var("Global:LlmService")!)
        {
            case "AzureOpenAI":
                kernelBuilder.Services.AddAzureOpenAIChatCompletion(
                    deploymentName: Env.Var("AzureOpenAI:ChatCompletionDeploymentName")!,
                    modelId: Env.Var("AzureOpenAI:ChatCompletionModelId"),
                    endpoint: Env.Var("AzureOpenAI:Endpoint")!,
                    apiKey: Env.Var("AzureOpenAI:ApiKey")!
                );
                break;

            case "OpenAI":
                kernelBuilder.Services.AddOpenAIChatCompletion(
                    modelId: Env.Var("OpenAI:ChatCompletionModelId")!,
                    apiKey: Env.Var("OpenAI:ApiKey")!,
                    orgId: Env.Var("OpenAI:OrgId")
                );
                break;

            default:
                throw new ArgumentException($"Invalid service type value: {Env.Var("Global:LlmService")}");
        }

        return kernelBuilder;
    }
}
