using System;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Onnx;
using OnnxFunctionCalling.Plugins;

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

async Task DoDemo(ChatHistory history, IChatCompletionService chatCompletionService, OnnxRuntimeGenAIPromptExecutionSettings settings, Kernel kernel)
{
    string userMessage = "change the alarm to 8";
    Console.WriteLine($"User > {userMessage}");
    history.AddUserMessage(userMessage);
    ChatMessageContent results = await chatCompletionService.GetChatMessageContentAsync(history, settings, kernel);
    Console.WriteLine($"Assistant > {results.Content}");
    history.AddAssistantMessage(results.Content!);
}

ILoggerFactory loggerFactory = LoggerFactory.Create(builder =>
{
    builder.AddConsole();
});

string modelId = "Phi_4_multimodal_instruct";
string modelPath = "D:\\VisionCATS_AI_Agent\\Development\\.cache\\models\\microsoft_Phi_4_multimodal_instruct_onnx-gpu_gpu_int4_rtn_block_32";

IKernelBuilder builder = Kernel.CreateBuilder();
builder.AddOnnxRuntimeGenAIChatCompletion(
    modelPath: modelPath,
    serviceId: "onnx",
    providers: [new Provider { Id = "cuda" }],
    loggerFactory: loggerFactory
);
builder.Plugins
    .AddFromType<MyTimePlugin>()
    .AddFromObject(new MyLightPlugin(turnedOn: true))
    .AddFromObject(new MyAlarmPlugin("11"));

Kernel kernel = builder.Build();

ChatHistory history = [];
history.AddSystemMessage("""
                         You are a helpful assistant.
                         You are not restricted to using the provided plugins,
                         and you can use information from your training.
                         Please explain your reasoning with the response.
                         """);

IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
OnnxRuntimeGenAIPromptExecutionSettings settings = new()
{
    FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
};

Console.WriteLine("""
                  Ask questions or give instructions to the copilot such as:
                  - change the alarm to 8
                  - what is the current alarm set?
                  - is the light on?
                  - turn the light off please
                  - set an alarm for 6:00 am
                  """);

await DoLoop(history, chatCompletionService, settings, kernel);

if (chatCompletionService is OnnxRuntimeGenAIChatCompletionService onnxService)
{
    onnxService.Dispose();
}
