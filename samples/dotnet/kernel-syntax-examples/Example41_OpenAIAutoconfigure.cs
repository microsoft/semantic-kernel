// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using RepoUtils;

internal class Example41_OpenAIAutoconfigure
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Open AI Auto-Configure ========");

        IKernel openAIKernel = Kernel.Builder
            .WithLogger(ConsoleLogger.Log)
            .WithOpenAI(Env.Var("OPENAI_API_KEY"))
            .Build();

        Console.WriteLine("======== Azure Open AI Auto-Configure ========");

        KernelBuilder builder2 = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log);

        builder2 = await builder2.WithAzureOpenAIAsync(
            endpoint: Env.Var("AZURE_OPENAI_ENDPOINT"),
            apiKey: Env.Var("AZURE_OPENAI_KEY"));

        IKernel azureKernel = builder2.Build();
    }
}
