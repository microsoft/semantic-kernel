using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Onnx;

async Task DoLoop(ChatHistory history, IChatCompletionService chatCompletionService, OnnxRuntimeGenAIPromptExecutionSettings settings, Kernel kernel)
{
    while (true)
    {
        Console.Write("User > ");
        string userMessage = Console.ReadLine()!;
        if (userMessage == "exit" || userMessage == "quit")
        {
            break;
        }

        if (string.IsNullOrEmpty(userMessage))
        {
            continue;
        }

        history.AddUserMessage(userMessage);

        try
        {
            ChatMessageContent results = await chatCompletionService.GetChatMessageContentAsync(history, settings, kernel);
            Console.WriteLine($"Assistant > {results.Content}");
            history.AddAssistantMessage(results.Content!);
        }
        catch (Exception e)
        {
            Console.WriteLine(e.Message);
        }
    }
}

string modelPath = "MODEL_PATH";

IKernelBuilder builder = Kernel.CreateBuilder();
builder.AddOnnxRuntimeGenAIChatCompletion(
    modelId: "onnx",
    modelPath: modelPath,
    providers: [new Provider { Id = "cuda" }]
);

Kernel kernel = builder.Build();

ChatHistory history = [];

IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
OnnxRuntimeGenAIPromptExecutionSettings settings = new()
{
    MaxTokens = 5120
};

await DoLoop(history, chatCompletionService, settings, kernel);

if (chatCompletionService is OnnxRuntimeGenAIChatCompletionService onnxService)
{
    onnxService.Dispose();
}
