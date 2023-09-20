// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with HuggingFace API.
 */
// ReSharper disable once InconsistentNaming
public static class Example20_HuggingFace
{
    public static async Task RunAsync()
    {
        await RunInferenceApiExampleAsync();
        await RunLlamaExampleAsync();
    }

    /// <summary>
    /// This example uses HuggingFace Inference API to access hosted models.
    /// More information here: <see href="https://huggingface.co/inference-api"/>
    /// </summary>
    private static async Task RunInferenceApiExampleAsync()
    {
        Console.WriteLine("\n======== HuggingFace Inference API example ========\n");

        IKernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithHuggingFaceTextCompletionService(
                model: TestConfiguration.HuggingFace.ModelId,
                apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var questionAnswerFunction = kernel.CreateSemanticFunction("Question: {{$input}}; Answer:");

        var result = await kernel.RunAsync("What is New York?", questionAnswerFunction);

        Console.WriteLine(result);
    }

    /// <summary>
    /// This example uses HuggingFace Llama 2 model and local HTTP server from Semantic Kernel repository.
    /// How to setup local HTTP server: <see href="https://github.com/microsoft/semantic-kernel/blob/main/samples/apps/hugging-face-http-server/README.md"/>.
    /// <remarks>
    /// Additional access is required to download Llama 2 model and run it locally.
    /// How to get access:
    /// 1. Visit <see href="https://ai.meta.com/resources/models-and-libraries/llama-downloads/"/> and complete request access form.
    /// 2. Visit <see href="https://huggingface.co/meta-llama/Llama-2-7b-hf"/> and complete form "Access Llama 2 on Hugging Face".
    /// Note: Your Hugging Face account email address MUST match the email you provide on the Meta website, or your request will not be approved.
    /// </remarks>
    /// </summary>
    private static async Task RunLlamaExampleAsync()
    {
        Console.WriteLine("\n======== HuggingFace Llama 2 example ========\n");

        // HuggingFace Llama 2 model: https://huggingface.co/meta-llama/Llama-2-7b-hf
        const string Model = "meta-llama/Llama-2-7b-hf";

        // HuggingFace local HTTP server endpoint
        const string Endpoint = "http://localhost:5000/completions";

        IKernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithHuggingFaceTextCompletionService(
                model: Model,
                endpoint: Endpoint,
                apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var questionAnswerFunction = kernel.CreateSemanticFunction("Question: {{$input}}; Answer:");

        var result = await kernel.RunAsync("What is New York?", questionAnswerFunction);

        Console.WriteLine(result);
    }
}
