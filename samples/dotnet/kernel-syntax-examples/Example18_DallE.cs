// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.Configuration;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with OpenAI DallE to create images
 */

// ReSharper disable once InconsistentNaming
public static class Example18_DallE
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== DallE Image Generation ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Add your text completion backend
        kernel.Config.AddOpenAIImageGeneration("dallE", Env.Var("OPENAI_API_KEY"));

        IImageGeneration backend = kernel.GetService<IImageGeneration>();

        var imageDescription = "A cute baby sea otter";
        var image = await backend.GenerateImageAsync(imageDescription, 256, 256);

        Console.WriteLine(imageDescription);
        Console.WriteLine("Image URL: " + image);
    }
}
