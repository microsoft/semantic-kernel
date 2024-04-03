// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Embeddings;
using xRetry;
using Xunit;
using Xunit.Abstractions;

#pragma warning disable CA1861 // Avoid constant arrays as arguments

namespace Examples;

// The following example shows how to use Semantic Kernel with HuggingFace API.
public class Example20_HuggingFace : BaseTest
{
    /// <summary>
    /// This example uses HuggingFace Inference API to access hosted models.
    /// More information here: <see href="https://huggingface.co/inference-api"/>
    /// </summary>
    [Fact]
    public async Task RunInferenceApiExampleAsync()
    {
        WriteLine("\n======== HuggingFace Inference API example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceTextGeneration(
                model: TestConfiguration.HuggingFace.ModelId,
                apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var questionAnswerFunction = kernel.CreateFunctionFromPrompt("Question: {{$input}}; Answer:");

        var result = await kernel.InvokeAsync(questionAnswerFunction, new() { ["input"] = "What is New York?" });

        WriteLine(result.GetValue<string>());
    }

    [RetryFact(typeof(HttpOperationException))]
    public async Task RunInferenceApiEmbeddingAsync()
    {
        this.WriteLine("\n======= Hugging Face Inference API - Embedding Example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceTextEmbeddingGeneration(
                               model: TestConfiguration.HuggingFace.EmbeddingModelId,
                               apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var embeddingGenerator = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Generate embeddings for each chunk.
        var embeddings = await embeddingGenerator.GenerateEmbeddingsAsync(new[] { "John: Hello, how are you?\nRoger: Hey, I'm Roger!" });

        this.WriteLine($"Generated {embeddings.Count} embeddings for the provided text");
    }

    [RetryFact(typeof(HttpOperationException))]
    public async Task RunStreamingExampleAsync()
    {
        WriteLine("\n======== HuggingFace zephyr-7b-beta streaming example ========\n");

        const string Model = "HuggingFaceH4/zephyr-7b-beta";

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceTextGeneration(
                model: Model,
                //endpoint: Endpoint,
                apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var questionAnswerFunction = kernel.CreateFunctionFromPrompt("Question: {{$input}}; Answer:");

        await foreach (string text in kernel.InvokeStreamingAsync<string>(questionAnswerFunction, new() { ["input"] = "What is New York?" }))
        {
            this.Write(text);
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
        WriteLine("\n======== HuggingFace Llama 2 example ========\n");

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

        WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Follow steps in <see href="https://huggingface.co/docs/text-generation-inference/main/en/quicktour"/> to setup HuggingFace local Text Generation Inference HTTP server.
    /// </summary>
    [Fact]
    public async Task RunTextGenerationInferenceChatCompletionAsync()
    {
        WriteLine("\n======== HuggingFace - TGI Chat Completion ========\n");

        // This example was run against one of the chat completion (Message API) supported models from HuggingFace, listed in here: <see href="https://huggingface.co/docs/text-generation-inference/main/en/supported_models"/>
        // Starting a Local Docker i.e:
        // docker run --gpus all --shm-size 1g -p 8080:80 -v "F:\temp\huggingface:/data" ghcr.io/huggingface/text-generation-inference:1.4 --model-id teknium/OpenHermes-2.5-Mistral-7B

        // HuggingFace local HTTP server endpoint
        var endpoint = new Uri("http://localhost:8080");

        const string Model = "teknium/OpenHermes-2.5-Mistral-7B";

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceChatCompletion(
                model: Model,
                endpoint: endpoint)
            .Build();

        var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory("You are a helpful assistant.")
        {
            new ChatMessageContent(AuthorRole.User, "What is deep learning?")
        };

        var result = await chatCompletion.GetChatMessageContentAsync(chatHistory);

        WriteLine(result.Role);
        WriteLine(result.Content);
    }

    /// <summary>
    /// Follow steps in <see href="https://huggingface.co/docs/text-generation-inference/main/en/quicktour"/> to setup HuggingFace local Text Generation Inference HTTP server.
    /// </summary>
    [Fact]
    public async Task RunTextGenerationInferenceStreamingChatCompletionAsync()
    {
        WriteLine("\n======== HuggingFace - TGI Chat Completion ========\n");

        // This example was run against one of the chat completion (Message API) supported models from HuggingFace, listed in here: <see href="https://huggingface.co/docs/text-generation-inference/main/en/supported_models"/>
        // Starting a Local Docker i.e:
        // docker run --gpus all --shm-size 1g -p 8080:80 -v "F:\temp\huggingface:/data" ghcr.io/huggingface/text-generation-inference:1.4 --model-id teknium/OpenHermes-2.5-Mistral-7B

        // HuggingFace local HTTP server endpoint
        var endpoint = new Uri("http://localhost:8080");

        const string Model = "teknium/OpenHermes-2.5-Mistral-7B";

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceChatCompletion(
                model: Model,
                endpoint: endpoint)
            .Build();

        var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory("You are a helpful assistant.")
        {
            new ChatMessageContent(AuthorRole.User, "What is deep learning?")
        };

        AuthorRole? role = null;
        await foreach (var chatMessageChunk in chatCompletion.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            if (role == null)
            {
                Write(chatMessageChunk.Role);
            }
            Write(chatMessageChunk.Content);

            role ??= chatMessageChunk.Role;
        }
    }

    public Example20_HuggingFace(ITestOutputHelper output) : base(output)
    {
    }
}
