using System;
using System.Collections.Generic;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Onnx;

// Path to the folder of your downloaded ONNX CUDA model
// i.e: D:\repo\huggingface\Phi-3-mini-4k-instruct-onnx\cuda\cuda-int4-rtn-block-32
string modelPath = "MODEL_PATH";

IKernelBuilder builder = Kernel.CreateBuilder();
builder.AddOnnxRuntimeGenAIChatClient(
    modelPath: modelPath,

    // Specify the provider you want to use, e.g., "cuda" for GPU support
    // For other execution providers, check: https://onnxruntime.ai/docs/genai/reference/config#provideroptions
    providers: [new Provider("cuda")] // 
);

Kernel kernel = builder.Build();

using IChatClient chatClient = kernel.GetRequiredService<IChatClient>();

List<ChatMessage> chatHistory = [];

while (true)
{
    Console.Write("User > ");
    string userMessage = Console.ReadLine()!;
    if (string.IsNullOrEmpty(userMessage))
    {
        break;
    }

    chatHistory.Add(new ChatMessage(ChatRole.User, userMessage));

    try
    {
        ChatResponse result = await chatClient.GetResponseAsync(chatHistory, new() { MaxOutputTokens = 1024 });
        Console.WriteLine($"Assistant > {result.Text}");

        chatHistory.AddRange(result.Messages);
    }
    catch (Exception e)
    {
        Console.WriteLine(e.Message);
    }
}
