// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace StructuredDataPlugin;

internal sealed class Program
{
    internal static async Task Main(string[] args)
    {
        var serviceCollection = new ServiceCollection()
            .AddSingleton<IConfiguration>((sp) => new ConfigurationBuilder()
                .AddJsonFile("appsettings.json", optional: true)
                .AddEnvironmentVariables()
                .AddUserSecrets<Program>()
                .Build())
            .AddTransient<ApplicationDbContext>()
            .AddTransient<StructuredDataService<ApplicationDbContext>>();

        var serviceProvider = serviceCollection.BuildServiceProvider();
        var config = serviceProvider.GetRequiredService<IConfiguration>();
        using var structuredDataService = serviceProvider.GetRequiredService<StructuredDataService<ApplicationDbContext>>();

        // Create kernel builder and add OpenAI
        var kernelBuilder = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o",
                apiKey: config["OpenAI:ApiKey"]!);

        // Add the database plugin using the factory with default operations
        var databasePlugin = StructuredDataPluginFactory.CreateStructuredDataPlugin<ApplicationDbContext, Product>(
            structuredDataService);

        kernelBuilder.Plugins.Add(databasePlugin);

        // Build the kernel and add the plugin
        var kernel = kernelBuilder.Build();

        // Create settings for function calling
        var settings = new OpenAIPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Example 1: Inserting new records
        Console.WriteLine("Creating a new record...");
        var insertPrompt = "Insert a new product with name 'Book' and price 29.99";
        var insertResult = await kernel.InvokePromptAsync(insertPrompt, new(settings));
        Console.WriteLine($"Insert Result: {insertResult}");

        // Example 2: Querying data
        Console.WriteLine("\nQuerying specific records...");
        var queryPrompt = "Find all products under $50";
        var queryResult = await kernel.InvokePromptAsync(queryPrompt, new(settings));
        Console.WriteLine($"Query Result: {queryResult}");

        // Example 3: Updating records
        Console.WriteLine("\nUpdating a record...");
        var updatePrompt = "Update the price of 'Book' to 39.99 and keep its name";
        var updateResult = await kernel.InvokePromptAsync(updatePrompt, new(settings));
        Console.WriteLine($"Update Result: {updateResult}");

        // Example 3: Updating records
        Console.WriteLine("\nDeleting a record...");
        var deletePrompt = "Delete the product 'Book'";
        var deleteResult = await kernel.InvokePromptAsync(deletePrompt, new(settings));
        Console.WriteLine($"Delete Result: {deleteResult}");

        // Example 4: Interactive chat-like interaction
        Console.WriteLine("\nStarting interactive mode (type 'exit' to quit)");
        Console.WriteLine("You can try queries like:");
        Console.WriteLine("- Find all products under $50");
        Console.WriteLine("- Insert a new product with name 'Table' and price 19.99");
        Console.WriteLine("- Update the price of 'Table' to 25.99");

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
}
