using System.ComponentModel;
using System.Text;
using System.Text.Json;
using Amazon.BedrockAgent;
using Amazon.BedrockAgentRuntime;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

var builder = Kernel.CreateBuilder();
builder.AddBedrockChatClient(modelId: "us.anthropic.claude-sonnet-4-5-20250929-v1:0");
builder
    .Services.AddSingleton<AmazonBedrockAgentClient>()
    .AddSingleton<AmazonBedrockAgentRuntimeClient>()
    .AddTransient(s => s.GetRequiredService<IChatClient>().AsChatCompletionService());

builder.Plugins.AddFromType<GreetingsPlugin>();
builder.Plugins.AddFromType<RandomNamePlugin>();

var kernel = builder.Build();

var executionSettings = new PromptExecutionSettings
{
    FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(
        autoInvoke: true,
        options: new FunctionChoiceBehaviorOptions
        {
            AllowParallelCalls = false,
            AllowConcurrentInvocation = false,
        }
    )
};

var chatService = kernel.GetRequiredService<IChatCompletionService>();
var history = new ChatHistory();
history.AddUserMessage("Greet 5 random persons");

try
{
    while (true)
    {
        var responses = chatService.GetStreamingChatMessageContentsAsync(
            history,
            executionSettings,
            kernel,
            CancellationToken.None
        );

        var assistantMessage = new StringBuilder();
        await foreach (var response in responses.ConfigureAwait(false))
        {
            if (response.Content != null)
            {
                Console.Write(response.Content);
                assistantMessage.Append(response.Content);
            }
        }

        var assistantMessageStr = assistantMessage.ToString();
        if (string.IsNullOrEmpty(assistantMessageStr))
        {
            history.AddUserMessage(assistantMessageStr);
        }

        history.AddUserMessage("Greet 5 more");
    }
}
catch (Exception)
{
    foreach (var historyMessage in history)
    {
        // Serialize the message to JSON format
        var jsonMessage = JsonSerializer.Serialize(historyMessage);
        Console.WriteLine(jsonMessage);
    }
}

public class GreetingsPlugin
{
    [KernelFunction, Description("Greet a person by name")]
    public string Greet(string name)
    {
        return $"Hello, {name}!";
    }
}

public class RandomNamePlugin
{
    private static readonly string[] s_names =
    {
        "Alice",
        "Bob",
        "Charlie",
        "Diana",
        "Ethan",
        "Fiona",
        "George",
        "Hannah",
        "Ian",
        "Julia",
    };

    [KernelFunction, Description("Get a random name")]
    public string GetRandomName()
    {
        var random = new Random();
        var name = s_names[random.Next(s_names.Length)];
        Console.WriteLine($"Tool called: GetRandomName() -> {name}");
        return name;
    }
}
