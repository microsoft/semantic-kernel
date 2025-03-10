// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using System.Text.Json;

#pragma warning disable SKEXP0070, SKEXP0050 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
#pragma warning disable CA2007, VSTHRD111 // .ConfigureAwait(false)

namespace StructuredDataPlugin;

internal sealed class Program
{
    internal static async Task Main(string[] args)
    {
        var serviceCollection = new ServiceCollection()
            .AddSingleton<IConfiguration>((sp) => new ConfigurationBuilder().AddUserSecrets<Program>().Build())
            .AddTransient<MyDbContext>()
            .AddTransient<StructuredDataService<MyDbContext>>();

        var serviceProvider = serviceCollection.BuildServiceProvider();
        var config = serviceProvider.GetRequiredService<IConfiguration>();
        using var structuredDataService = serviceProvider.GetRequiredService<StructuredDataService<MyDbContext>>();
        using var myHandler = new MyHandler();
        using var httpClient = new HttpClient(myHandler);

        // Create kernel builder and add OpenAI
        var kernelBuilder = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o",
                apiKey: config["OpenAI:ApiKey"]!,
                httpClient: httpClient);

        // Add the database plugin using the factory with default operations
        var databasePlugin = StructuredDataPluginFactory.CreateStructuredDataPlugin<MyDbContext, Product>(
            structuredDataService);

        kernelBuilder.Plugins.Add(databasePlugin);

        // Build the kernel and add the plugin
        var kernel = kernelBuilder.Build();

        // Create settings for function calling
        var settings = new OpenAIPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Example 1: Insert a new record
        Console.WriteLine("Creating a new record...");
        var insertPrompt = $"Create a new record with description 'Test from OpenAI' and current date {DateTime.Now.Date:yyyy-MM-dd}";
        var insertResult = await kernel.InvokePromptAsync(insertPrompt, new(settings));
        Console.WriteLine($"Insert Result: {insertResult}");

        // Example 2: Query records
        Console.WriteLine("\nQuerying all records...");
        var queryPrompt = "Show me all the records in the database";
        var queryResult = await kernel.InvokePromptAsync(queryPrompt, new(settings));
        Console.WriteLine($"Query Result: {queryResult}");

        // Example 3: Complex query with specific criteria
        Console.WriteLine("\nQuerying records with specific criteria...");
        var complexPrompt = $"Find records that were created today: {DateTime.Now.Date:yyyy-MM-dd} and show their descriptions";
        var complexResult = await kernel.InvokePromptAsync(complexPrompt, new(settings));
        Console.WriteLine($"Complex Query Result: {complexResult}");

        // Example 4: Interactive chat-like interaction
        Console.WriteLine("\nStarting interactive mode (type 'exit' to quit)");
        while (true)
        {
            Console.Write("\nEnter your database query: ");
            var userInput = Console.ReadLine();

            if (string.IsNullOrEmpty(userInput) || userInput.Equals("exit", StringComparison.OrdinalIgnoreCase))
            {
                break;
            }

            var result = await kernel.InvokePromptAsync(userInput, new(settings));
            Console.WriteLine($"\nResult: {result}");
        }
    }

    private sealed class MyHandler : HttpClientHandler
    {
        private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
        {
            WriteIndented = true,
        };
        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var requestBody = await request.Content!.ReadAsStringAsync(cancellationToken);
            // Console.WriteLine($"Request: {request.Method} {request.RequestUri}");
            Console.WriteLine($"Request Body: {JsonSerializer.Serialize(JsonSerializer.Deserialize<JsonElement>(requestBody), s_jsonSerializerOptions)}");
            // Custom logic for handling HTTP requests
            return await base.SendAsync(request, cancellationToken);
        }
    }
}
