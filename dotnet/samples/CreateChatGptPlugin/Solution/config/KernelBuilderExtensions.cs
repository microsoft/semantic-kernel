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
                if (Env.Var("AzureOpenAI:DeploymentType") == "text-completion")
                {
                    kernelBuilder.Services.AddAzureOpenAITextGeneration(
                        deploymentName: Env.Var("AzureOpenAI:TextCompletionDeploymentName")!,
                        modelId: Env.Var("AzureOpenAI:TextCompletionModelId")!,
                        endpoint: Env.Var("AzureOpenAI:Endpoint")!,
                        apiKey: Env.Var("AzureOpenAI:ApiKey")!
                    );
                }
                else if (Env.Var("AzureOpenAI:DeploymentType") == "chat-completion")
                {
                    kernelBuilder.Services.AddAzureOpenAIChatCompletion(
                        deploymentName: Env.Var("AzureOpenAI:ChatCompletionDeploymentName")!,
                        modelId: Env.Var("AzureOpenAI:ChatCompletionModelId")!,
                        endpoint: Env.Var("AzureOpenAI:Endpoint")!,
                        apiKey: Env.Var("AzureOpenAI:ApiKey")!
                    );
                }
                break;

            case "OpenAI":
                if (Env.Var("OpenAI:ModelType") == "text-completion")
                {
                    kernelBuilder.Services.AddOpenAITextGeneration(
                        modelId: Env.Var("OpenAI:TextCompletionModelId")!,
                        apiKey: Env.Var("OpenAI:ApiKey")!,
                        orgId: Env.Var("OpenAI:OrgId")
                    );
                }
                else if (Env.Var("OpenAI:ModelType") == "chat-completion")
                {
                    kernelBuilder.Services.AddOpenAIChatCompletion(
                        modelId: Env.Var("OpenAI:ChatCompletionModelId")!,
                        apiKey: Env.Var("OpenAI:ApiKey")!,
                        orgId: Env.Var("OpenAI:OrgId")
                    );
                }
                break;

            default:
                throw new ArgumentException($"Invalid service type value: {Env.Var("OpenAI:ModelType")}");
        }

        return kernelBuilder;
    }
}
