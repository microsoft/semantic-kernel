// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using RepoUtils;

internal sealed class Example41_OpenAIAutoconfigure
{
    public static void Run()
    {
        Console.WriteLine("======== Azure Open AI Auto-Configure ========");

        try
        {
            IKernel azureKernel = Kernel.Builder
                .WithLogger(ConsoleLogger.Log)
                .WithAzureOpenAI(
                    endpoint: Env.Var("AZURE_OPENAI_ENDPOINT"),
                    apiKey: Env.Var("AZURE_OPENAI_KEY"))
                .Build();
        }
        catch (YourAppException)
        {
            ConsoleLogger.Log.LogInformation("Azure OpenAI keys not set. Skipping Azure OpenAI example.");
        }

        Console.WriteLine("======== Open AI Auto-Configure ========");

        try
        {
            IKernel openAIKernel = Kernel.Builder
                .WithLogger(ConsoleLogger.Log)
                .WithOpenAI(Env.Var("OPENAI_API_KEY"))
                .Build();
        }
        catch (YourAppException)
        {
            ConsoleLogger.Log.LogInformation("OpenAI API key not set. Skipping OpenAI example.");
        }
    }
}
