// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

#pragma warning disable SKEXP0001
#pragma warning disable SKEXP0010

namespace AIModelRouter;

internal sealed class Program
{
    private static async Task Main(string[] args)
    {
        Console.ForegroundColor = ConsoleColor.White;
        List<string> serviceIds = [];
        var config = new ConfigurationBuilder().AddUserSecrets<Program>().Build();

        ServiceCollection services = new();

        Console.ForegroundColor = ConsoleColor.DarkCyan;
        Console.WriteLine("======== AI Services Added ========");

        services.AddKernel();

        // Adding multiple connectors targeting different providers / models.
        if (config["LMStudio:Endpoint"] is not null)
        {
            services.AddOpenAIChatCompletion(
                    serviceId: "lmstudio",
                    modelId: "N/A", // LMStudio model is pre defined in the UI List box.
                    endpoint: new Uri(config["LMStudio:Endpoint"]!),
                    apiKey: null);

            serviceIds.Add("lmstudio");
            Console.WriteLine("• LMStudio - Use \"lmstudio\" in the prompt.");
        }

        Console.ForegroundColor = ConsoleColor.Cyan;

        if (config["Ollama:ModelId"] is not null)
        {
            services.AddOllamaChatCompletion(
                serviceId: "ollama",
                modelId: config["Ollama:ModelId"]!,
                endpoint: new Uri(config["Ollama:Endpoint"] ?? "http://localhost:11434"));

            serviceIds.Add("ollama");
            Console.WriteLine("• Ollama - Use \"ollama\" in the prompt.");
        }

        if (config["AzureOpenAI:Endpoint"] is not null)
        {
            if (config["AzureOpenAI:ApiKey"] is not null)
            {
                services.AddAzureOpenAIChatCompletion(
                    serviceId: "azureopenai",
                    endpoint: config["AzureOpenAI:Endpoint"]!,
                    deploymentName: config["AzureOpenAI:ChatDeploymentName"]!,
                    apiKey: config["AzureOpenAI:ApiKey"]!);
            }
            else
            {
                services.AddAzureOpenAIChatCompletion(
                    serviceId: "azureopenai",
                    endpoint: config["AzureOpenAI:Endpoint"]!,
                    deploymentName: config["AzureOpenAI:ChatDeploymentName"]!,
                    credentials: new AzureCliCredential());
            }

            serviceIds.Add("azureopenai");
            Console.WriteLine("• Azure OpenAI Added - Use \"azureopenai\" in the prompt.");
        }

        if (config["OpenAI:ApiKey"] is not null)
        {
            services.AddOpenAIChatCompletion(
                serviceId: "openai",
                modelId: config["OpenAI:ChatModelId"] ?? "gpt-4o",
                apiKey: config["OpenAI:ApiKey"]!);

            serviceIds.Add("openai");
            Console.WriteLine("• OpenAI Added - Use \"openai\" in the prompt.");
        }

        if (config["Onnx:ModelPath"] is not null)
        {
            services.AddOnnxRuntimeGenAIChatCompletion(
                serviceId: "onnx",
                modelId: "phi-3",
                modelPath: config["Onnx:ModelPath"]!);

            serviceIds.Add("onnx");
            Console.WriteLine("• ONNX Added - Use \"onnx\" in the prompt.");
        }

        if (config["AzureAIInference:Endpoint"] is not null)
        {
            services.AddAzureAIInferenceChatCompletion(
                serviceId: "azureai",
                modelId: config["AzureAIInference:ChatModelId"]!,
                endpoint: new Uri(config["AzureAIInference:Endpoint"]!),
                apiKey: config["AzureAIInference:ApiKey"]);

            serviceIds.Add("azureai");
            Console.WriteLine("• Azure AI Inference Added - Use \"azureai\" in the prompt.");
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
                ServiceId = router.GetService(userMessage, serviceIds)
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
