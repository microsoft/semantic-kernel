// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable SKEXP0070

using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Onnx;

namespace SemanticKernel.AotCompatibility;

/// <summary>
/// This class contains samples of how to use ONNX chat completion service in AOT applications.
/// </summary>
internal static class OnnxChatCompletionSamples
{
    /// <summary>
    /// Sends a prompt to the ONNX model and gets the chat message content.
    /// </summary>
    public static async Task GetChatMessageContent(IConfigurationRoot config)
    {
        string chatModelPath = config["Onnx:ModelPath"]!;
        string chatModelId = config["Onnx:ModelId"] ?? "phi-3";

        // Create kernel builder and add OnnxRuntimeGenAIChatCompletion service.
        // If you plan to use the service with Non-ONNX prompt execution settings,  
        // supply JSON serializer options with a JSON serializer context for this setup.
        IKernelBuilder builder = Kernel.CreateBuilder()
            .AddOnnxRuntimeGenAIChatCompletion(chatModelId, chatModelPath);

        // Build kernel and get the service instance
        Kernel kernel = builder.Build();
        IChatCompletionService chatService = kernel.GetRequiredService<IChatCompletionService>();

        string prompt = "Hello, what is the weather in Boston, USA now?";

        OnnxRuntimeGenAIPromptExecutionSettings executionSettings = new()
        {
            Temperature = 0.7f, // Adjusts creativity level  
            TopP = 0.9f // Limits token choice diversity
        };

        // Prompt the ONNX model
        ChatMessageContent messageContent = await chatService.GetChatMessageContentAsync(prompt, executionSettings);

        // Display the result
        Console.WriteLine(messageContent);
    }

    /// <summary>
    /// Sends a prompt to the ONNX model and gets the chat message content in a streaming fashion.
    /// </summary>
    public static async Task GetStreamingChatMessageContents(IConfigurationRoot config)
    {
        string chatModelPath = config["Onnx:ModelPath"]!;
        string chatModelId = config["Onnx:ModelId"] ?? "phi-3";

        // Create kernel builder and add OnnxRuntimeGenAIChatCompletion service.
        // If you plan to use the service with Non-ONNX prompt execution settings,  
        // supply JSON serializer options with a JSON serializer context for this setup.
        IKernelBuilder builder = Kernel.CreateBuilder()
            .AddOnnxRuntimeGenAIChatCompletion(chatModelId, chatModelPath);

        // Build kernel and get the service instance
        Kernel kernel = builder.Build();
        IChatCompletionService chatService = kernel.GetRequiredService<IChatCompletionService>();

        string prompt = "Hello, what is the weather in Boston, USA now?";

        OnnxRuntimeGenAIPromptExecutionSettings executionSettings = new()
        {
            Temperature = 0.7f, // Adjusts creativity level  
            TopP = 0.9f // Limits token choice diversity
        };

        // Prompt the ONNX model
        await foreach (StreamingChatMessageContent messageContent in chatService.GetStreamingChatMessageContentsAsync(prompt, executionSettings))
        {
            // Display the result
            Console.WriteLine(messageContent);
        }
    }
}
