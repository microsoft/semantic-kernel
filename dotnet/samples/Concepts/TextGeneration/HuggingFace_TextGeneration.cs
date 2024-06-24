// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using xRetry;

#pragma warning disable format // Format item can be simplified
#pragma warning disable CA1861 // Avoid constant arrays as arguments

namespace TextGeneration;

// The following example shows how to use Semantic Kernel with HuggingFace API.
public class HuggingFace_TextGeneration(ITestOutputHelper helper) : BaseTest(helper)
{
    private const string DefaultModel = "HuggingFaceH4/zephyr-7b-beta";

    /// <summary>
    /// This example uses HuggingFace Inference API to access hosted models.
    /// More information here: <see href="https://huggingface.co/inference-api"/>
    /// </summary>
    [Fact]
    public async Task RunInferenceApiExampleAsync()
    {
        Console.WriteLine("\n======== HuggingFace Inference API example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceTextGeneration(
                model: TestConfiguration.HuggingFace.ModelId ?? DefaultModel,
                apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var questionAnswerFunction = kernel.CreateFunctionFromPrompt("Question: {{$input}}; Answer:");

        var result = await kernel.InvokeAsync(questionAnswerFunction, new() { ["input"] = "What is New York?" });

        Console.WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Some Hugging Face models support streaming responses, configure using the HuggingFace ModelId setting.
    /// </summary>
    /// <remarks>
    /// Tested with HuggingFaceH4/zephyr-7b-beta model.
    /// </remarks>
    [RetryFact(typeof(HttpOperationException))]
    public async Task RunStreamingExampleAsync()
    {
        string model = TestConfiguration.HuggingFace.ModelId ?? DefaultModel;

        Console.WriteLine($"\n======== HuggingFace {model} streaming example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceTextGeneration(
                model: model,
                apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var settings = new HuggingFacePromptExecutionSettings { UseCache = false };

        var questionAnswerFunction = kernel.CreateFunctionFromPrompt("Question: {{$input}}; Answer:", new HuggingFacePromptExecutionSettings
        {
            UseCache = false
        });

        await foreach (string text in kernel.InvokePromptStreamingAsync<string>("Question: {{$input}}; Answer:", new(settings) { ["input"] = "What is New York?" }))
        {
            Console.Write(text);
        }
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
    [Fact(Skip = "Requires local model or Huggingface Pro subscription")]
    public async Task RunLlamaExampleAsync()
    {
        Console.WriteLine("\n======== HuggingFace Llama 2 example ========\n");

        // HuggingFace Llama 2 model: https://huggingface.co/meta-llama/Llama-2-7b-hf
        const string Model = "meta-llama/Llama-2-7b-hf";

        // HuggingFace local HTTP server endpoint
        // const string Endpoint = "http://localhost:5000/completions";

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceTextGeneration(
                model: Model,
                //endpoint: Endpoint,
                apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var questionAnswerFunction = kernel.CreateFunctionFromPrompt("Question: {{$input}}; Answer:");

        var result = await kernel.InvokeAsync(questionAnswerFunction, new() { ["input"] = "What is New York?" });

        Console.WriteLine(result.GetValue<string>());
    }
}
