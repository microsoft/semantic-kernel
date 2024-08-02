// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

#pragma warning disable SKEXP0001
#pragma warning disable SKEXP0010
#pragma warning disable CA2249 // Consider using 'string.Contains' instead of 'string.IndexOf'

namespace AIModelRouter;

internal sealed partial class Program
{
    private static async Task Main(string[] args)
    {
        Console.ForegroundColor = ConsoleColor.White;

        var config = new ConfigurationBuilder().AddUserSecrets<Program>().Build();

        ServiceCollection services = new();

        // Adding multiple connectors targeting different providers / models.
        services.AddKernel()                /* LMStudio model is selected in server side. */
            .AddOpenAIChatCompletion(serviceId: "lmstudio", modelId: "N/A", endpoint: new Uri("http://localhost:1234"), apiKey: null)
            .AddOpenAIChatCompletion(serviceId: "ollama", modelId: "phi3", endpoint: new Uri("http://localhost:11434"), apiKey: null)
            .AddOpenAIChatCompletion(serviceId: "openai", modelId: "gpt-4o", apiKey: config["OpenAI:ApiKey"]!)

            // Adding a custom filter to capture router selected service id
            .Services.AddSingleton<IPromptRenderFilter>(new SelectedServiceFilter());

        var kernel = services.BuildServiceProvider().GetRequiredService<Kernel>();
        var router = new CustomRouter();

        while (true)
        {
            Console.Write("\n\nUser > ");
            var userMessage = Console.ReadLine();

            // Exit application if the user enters an empty message
            if (string.IsNullOrWhiteSpace(userMessage)) { return; }

            // Find the best service to use based on the user's input
            KernelArguments arguments = new(new PromptExecutionSettings()
            {
                ServiceId = router.FindService(userMessage, ["lmstudio", "ollama", "openai"])
            });

            // Invoke the prompt and print the response
            await foreach (var chatChunk in kernel.InvokePromptStreamingAsync(userMessage, arguments).ConfigureAwait(false))
            {
                Console.Write(chatChunk);
            }
        }
    }
}
