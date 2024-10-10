// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

#pragma warning disable SKEXP0001
#pragma warning disable SKEXP0010
#pragma warning disable SKEXP0070

namespace AIModelRouter;

internal sealed class Program
{
    private static async Task Main(string[] args)
    {
        Console.ForegroundColor = ConsoleColor.White;

        var config = new ConfigurationBuilder().AddUserSecrets<Program>().Build();

        ServiceCollection services = new();

        // Adding multiple connectors targeting different providers / models.
        services
            .AddKernel()
            .AddOpenAIChatCompletion(
                serviceId: "lmstudio",
                modelId: "N/A", // LMStudio model is pre defined in the UI List box.
                endpoint: new Uri(config["LMStudio:Endpoint"] ?? "http://localhost:1234"),
                apiKey: null);

        Console.ForegroundColor = ConsoleColor.DarkCyan;
        Console.WriteLine("======== AI Services Added ========");
        Console.ForegroundColor = ConsoleColor.Cyan;
        Console.WriteLine("• LMStudio - Use \"lmstudio\" in the prompt.");

        if (config["Ollama:ModelId"] is not null)
        {
            services.AddOllamaChatCompletion(
                serviceId: "ollama",
                modelId: config["Ollama:ModelId"]!,
                endpoint: new Uri(config["Ollama:Endpoint"] ?? "http://localhost:11434"));

            Console.WriteLine("• Ollama - Use \"ollama\" in the prompt.");
        }

        if (config["OpenAI:ApiKey"] is not null)
        {
            services.AddOpenAIChatCompletion(
                serviceId: "openai",
                modelId: config["OpenAI:ModelId"] ?? "gpt-4o",
                apiKey: config["OpenAI:ApiKey"]!);

            Console.WriteLine("• OpenAI Added - Use \"openai\" in the prompt.");
        }

        if (config["Onnx:ModelPath"] is not null)
        {
            services.AddOnnxRuntimeGenAIChatCompletion(
                serviceId: "onnx",
                modelId: "phi-3",
                modelPath: config["Onnx:ModelPath"]!);

            Console.WriteLine("• ONNX Added - Use \"onnx\" in the prompt.");
        }

        if (config["AzureAIInference:Endpoint"] is not null)
        {
            services.AddAzureAIInferenceChatCompletion(
                serviceId: "azureai",
                endpoint: new Uri(config["AzureAIInference:Endpoint"]!),
                apiKey: config["AzureAIInference:ApiKey"]);

            Console.WriteLine("• Azure AI Inference Added - Use \"azureai\" in the prompt.");
        }

        if (config["Anthropic:ApiKey"] is not null)
        {
            services.AddAnthropicChatCompletion(
                serviceId: "anthropic",
                modelId: config["Anthropic:ModelId"] ?? "claude-3-5-sonnet-20240620",
                apiKey: config["Anthropic:ApiKey"]!);

            Console.WriteLine("• Anthropic Added - Use \"anthropic\" in the prompt.");
        }

        // Adding a custom filter to capture router selected service id
        services.AddSingleton<IPromptRenderFilter>(new SelectedServiceFilter());

        var kernel = services.BuildServiceProvider().GetRequiredService<Kernel>();
        var router = new CustomRouter();

        Console.ForegroundColor = ConsoleColor.White;
        while (true)
        {
            Console.Write("\nUser > ");
            var userMessage = Console.ReadLine();

            // Exit application if the user enters an empty message
            if (string.IsNullOrWhiteSpace(userMessage)) { return; }

            // Find the best service to use based on the user's input
            KernelArguments arguments = new(new PromptExecutionSettings()
            {
                ServiceId = router.FindService(userMessage, ["lmstudio", "ollama", "openai", "onnx", "azureai", "anthropic"])
            });

            // Invoke the prompt and print the response
            await foreach (var chatChunk in kernel.InvokePromptStreamingAsync(userMessage, arguments).ConfigureAwait(false))
            {
                Console.Write(chatChunk);
            }
            Console.WriteLine();
        }
    }
}
