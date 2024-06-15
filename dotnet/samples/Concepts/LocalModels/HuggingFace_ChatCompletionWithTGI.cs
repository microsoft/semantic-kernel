// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

#pragma warning disable format // Format item can be simplified
#pragma warning disable CA1861 // Avoid constant arrays as arguments

namespace LocalModels;

// The following example shows how to use Semantic Kernel with HuggingFace API.
public class HuggingFace_ChatCompletionWithTGI(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Follow steps in <see href="https://huggingface.co/docs/text-generation-inference/main/en/quicktour"/> to setup HuggingFace local Text Generation Inference HTTP server.
    /// </summary>
    [Fact(Skip = "Requires TGI (text generation inference) deployment")]
    public async Task RunTGI_ChatCompletionAsync()
    {
        Console.WriteLine("\n======== HuggingFace - TGI Chat Completion ========\n");

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

        Console.WriteLine(result.Role);
        Console.WriteLine(result.Content);
    }

    /// <summary>
    /// Follow steps in <see href="https://huggingface.co/docs/text-generation-inference/main/en/quicktour"/> to setup HuggingFace local Text Generation Inference HTTP server.
    /// </summary>
    [Fact(Skip = "Requires TGI (text generation inference) deployment")]
    public async Task RunTGI_StreamingChatCompletionAsync()
    {
        Console.WriteLine("\n======== HuggingFace - TGI Chat Completion Streaming ========\n");

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
            if (role is null)
            {
                role = chatMessageChunk.Role;
                Console.Write(role);
            }
            Console.Write(chatMessageChunk.Content);
        }
    }
}
