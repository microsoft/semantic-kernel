// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using xRetry;
using FunctionCallContent = Microsoft.SemanticKernel.FunctionCallContent;

namespace FunctionCalling;

/// <summary>
/// These examples demonstrate two ways functions called by the Gemini LLM can be invoked using the SK streaming and non-streaming AI API:
///
/// 1. Automatic Invocation by SK (with and without nullable properties):
///    Functions called by the LLM are invoked automatically by SK. The results of these function invocations
///    are automatically added to the chat history and returned to the LLM. The LLM reasons about the chat history
///    and generates the final response.
///    This approach is fully automated and requires no manual intervention from the caller.
///
/// 2. Manual Invocation by a Caller:
///    Functions called by the LLM are returned to the AI API caller. The caller controls the invocation phase where
///    they may decide which function to call, when to call them, how to handle exceptions, call them in parallel or sequentially, etc.
///    The caller then adds the function results or exceptions to the chat history and returns it to the LLM, which reasons about it
///    and generates the final response.
///    This approach is manual and provides more control over the function invocation phase to the caller.
/// </summary>
public sealed class Gemini_FunctionCalling(ITestOutputHelper output) : BaseTest(output)
{
    [RetryFact]
    public async Task GoogleAIChatCompletionWithFunctionCalling()
    {
        Console.WriteLine("============= Google AI - Gemini Chat Completion with function calling =============");

        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);
        Assert.NotNull(TestConfiguration.GoogleAI.Gemini.ModelId);

        using var googleClient = new Google.GenAI.Client(apiKey: TestConfiguration.GoogleAI.ApiKey);
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services
            .AddChatClient(googleClient.AsIChatClient(TestConfiguration.GoogleAI.Gemini.ModelId))
            .UseKernelFunctionInvocation();
        Kernel kernel = builder.Build();

        await this.RunSampleAsync(kernel);
    }

    [RetryFact]
    public async Task VertexAIChatCompletionWithFunctionCalling()
    {
        Console.WriteLine("============= Vertex AI - Gemini Chat Completion with function calling =============");

        Assert.NotNull(TestConfiguration.VertexAI.Location);
        Assert.NotNull(TestConfiguration.VertexAI.ProjectId);
        Assert.NotNull(TestConfiguration.VertexAI.Gemini.ModelId);

        // The Google SDK discovers application default credentials and refreshes tokens automatically.
        using var googleClient = new Google.GenAI.Client(
            vertexAI: true,
            project: TestConfiguration.VertexAI.ProjectId,
            location: TestConfiguration.VertexAI.Location);
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services
            .AddChatClient(googleClient.AsIChatClient(TestConfiguration.VertexAI.Gemini.ModelId))
            .UseKernelFunctionInvocation();
        Kernel kernel = builder.Build();

        await this.RunSampleAsync(kernel);
    }

    [RetryFact]
    public async Task GoogleAIFunctionCallingNullable()
    {
        Console.WriteLine("============= Google AI - Gemini Chat Completion with function calling (nullable properties) =============");

        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);

        using var googleClient = new Google.GenAI.Client(apiKey: TestConfiguration.GoogleAI.ApiKey);
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services
            .AddChatClient(googleClient.AsIChatClient(TestConfiguration.GoogleAI.Gemini.ModelId))
            .UseKernelFunctionInvocation();

        kernelBuilder.Plugins.AddFromType<MyWeatherPlugin>();

        var promptExecutionSettings = new PromptExecutionSettings()
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(),
        };

        var kernel = kernelBuilder.Build();

        var response = await kernel.InvokePromptAsync("Hi, what's the weather in New York?", new(promptExecutionSettings));

        Console.WriteLine(response.ToString());
    }

    private sealed class MyWeatherPlugin
    {
        [KernelFunction]
        [Description("Get the weather for a given location.")]
        private string GetWeather(WeatherRequest request)
        {
            return $"The weather in {request?.Location} is sunny.";
        }
    }

    [RetryFact]
    public async Task VertexAIFunctionCallingNullable()
    {
        Console.WriteLine("============= Vertex AI - Gemini Chat Completion with function calling (nullable properties) =============");

        Assert.NotNull(TestConfiguration.VertexAI.Location);
        Assert.NotNull(TestConfiguration.VertexAI.ProjectId);

        // The Google SDK discovers application default credentials and refreshes tokens automatically.
        using var googleClient = new Google.GenAI.Client(
            vertexAI: true,
            project: TestConfiguration.VertexAI.ProjectId,
            location: TestConfiguration.VertexAI.Location);
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services
            .AddChatClient(googleClient.AsIChatClient(TestConfiguration.VertexAI.Gemini.ModelId))
            .UseKernelFunctionInvocation();

        kernelBuilder.Plugins.AddFromType<MyWeatherPlugin>();

        var promptExecutionSettings = new PromptExecutionSettings()
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(),
        };
        var kernel = kernelBuilder.Build();
        var response = await kernel.InvokePromptAsync("Hi, what's the weather in New York?", new(promptExecutionSettings));
        Console.WriteLine(response.ToString());
    }

    private async Task RunSampleAsync(Kernel kernel)
    {
        // Add a plugin with some helper functions we want to allow the model to utilize.
        kernel.ImportPluginFromFunctions("HelperFunctions",
        [
            kernel.CreateFunctionFromMethod(() => DateTime.UtcNow.ToString("R"), "GetCurrentUtcTime", "Retrieves the current time in UTC."),
            kernel.CreateFunctionFromMethod((string cityName) =>
                cityName switch
                {
                    "Boston" => "61 and rainy",
                    "London" => "55 and cloudy",
                    "Miami" => "80 and sunny",
                    "Paris" => "60 and rainy",
                    "Tokyo" => "50 and sunny",
                    "Sydney" => "75 and sunny",
                    "Tel Aviv" => "80 and sunny",
                    _ => "31 and snowing",
                }, "Get_Weather_For_City", "Gets the current weather for the specified city"),
        ]);

        Console.WriteLine("======== Example 1: Use automated function calling with a non-streaming prompt ========");
        {
            PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
            Console.WriteLine(await kernel.InvokePromptAsync(
                "Check current UTC time, and return current weather in Paris city", new(settings)));
            Console.WriteLine();
        }

        Console.WriteLine("======== Example 2: Use automated function calling with a streaming prompt ========");
        {
            PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
            await foreach (var update in kernel.InvokePromptStreamingAsync(
                               "Check current UTC time, and return current weather in Boston city", new(settings)))
            {
                Console.Write(update);
            }

            Console.WriteLine();
        }

        Console.WriteLine("======== Example 3: Use manual function calling with a non-streaming prompt ========");
        {
            var chat = kernel.GetRequiredService<IChatClient>().AsChatCompletionService();
            var chatHistory = new ChatHistory();

            PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) };
            chatHistory.AddUserMessage("Check current UTC time, and return current weather in London city");
            while (true)
            {
                var result = await chat.GetChatMessageContentAsync(chatHistory, settings, kernel);

                if (result.Content is not null)
                {
                    Console.Write(result.Content);
                }

                var functionCalls = FunctionCallContent.GetFunctionCalls(result).ToArray();
                if (functionCalls.Length == 0)
                {
                    break;
                }

                chatHistory.Add(result);
                foreach (var functionCall in functionCalls)
                {
                    var functionResult = await functionCall.InvokeAsync(kernel);
                    chatHistory.Add(functionResult.ToChatMessage());
                }
            }

            Console.WriteLine();
        }

        /* Uncomment this to try in a console chat loop.
        Console.WriteLine("======== Example 4: Use automated function calling with a streaming chat ========");
        {
            PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
            var chat = kernel.GetRequiredService<IChatClient>().AsChatCompletionService();
            var chatHistory = new ChatHistory();

            while (true)
            {
                Console.Write("Question (Type \"quit\" to leave): ");
                string question = Console.ReadLine() ?? string.Empty;
                if (question == "quit")
                {
                    break;
                }

                chatHistory.AddUserMessage(question);
                System.Text.StringBuilder sb = new();
                await foreach (var update in chat.GetStreamingChatMessageContentsAsync(chatHistory, settings, kernel))
                {
                    if (update.Content is not null)
                    {
                        Console.Write(update.Content);
                        sb.Append(update.Content);
                    }
                }

                chatHistory.AddAssistantMessage(sb.ToString());
                Console.WriteLine();
            }
        }
        */
    }

    private sealed class WeatherRequest
    {
        public string? Location { get; set; }
    }
}
