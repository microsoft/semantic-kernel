/*
 Copyright (c) Microsoft. All rights reserved.

 Example application that uses Semantic Kernel.

 Loads app configuration from:
 - appsettings.json.
 - appsettings.{Environment}.json.
 - Secret Manager when the app runs in the "Development" environment (set through the DOTNET_ENVIRONMENT variable).
 - Environment variables.
 - Command-line arguments.
*/

using HomeAutomation.Plugins;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace HomeAutomation;

internal static class Program
{
    internal static async Task Main(string[] args)
    {
        HostApplicationBuilder builder = Host.CreateApplicationBuilder(args);
        builder.Services.AddHostedService<Worker>();
        builder.Services.AddSingleton<AppConfiguration>();
        builder.Services.AddSingleton<Kernel>(sp =>
        {
            AppConfiguration ac = sp.GetRequiredService<AppConfiguration>();
            var builder = Kernel.CreateBuilder()
                                // Add AI services here
                                // Note that you can provide your custom http client when adding specific AI services
                                .AddAzureOpenAIChatCompletion(ac.AzureOpenAiDeployment, ac.AzureOpenAiEndpoint, ac.AzureOpenAiApiKey);
            // Add plugins to include in kernel here
            builder.Plugins.AddFromType<MyTimePlugin>();
            Kernel kernel = builder.Build();

            return kernel;
        });

        using IHost host = builder.Build();

        await host.RunAsync();
    }
}

/// <summary>
/// Actual code to run.
/// </summary>
internal sealed class Worker : BackgroundService
{
    private readonly IHostApplicationLifetime _hostApplicationLifetime;
    private readonly Kernel _kernel;

    public Worker(IHostApplicationLifetime hostApplicationLifetime, Kernel kernel)
    {
        _hostApplicationLifetime = hostApplicationLifetime;
        _kernel = kernel;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        const string TimePrompt = "What time is it?";

        Console.WriteLine($"Worker running at: {DateTimeOffset.Now}");

        // Get chat completion service
        var chatCompletionService = _kernel.GetRequiredService<IChatCompletionService>();

        // Enable auto function calling
        OpenAIPromptExecutionSettings openAIPromptExecutionSettings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Get the response from the AI
        ChatMessageContent chatResult = await chatCompletionService.GetChatMessageContentAsync(TimePrompt, openAIPromptExecutionSettings, _kernel, stoppingToken);
        Console.WriteLine($"Result is: {chatResult}");

        MyLightPlugin kitchenLight = new();
        MyLightPlugin bedroomLight = new();
        _kernel.ImportPluginFromObject(kitchenLight, "Kitchen");
        _kernel.ImportPluginFromObject(bedroomLight, "Bedroom");

        chatResult = await chatCompletionService.GetChatMessageContentAsync("Turn on the kitchen light", openAIPromptExecutionSettings, _kernel, stoppingToken);
        Console.WriteLine($"Result to request to turn light on: {chatResult}");

        chatResult = await chatCompletionService.GetChatMessageContentAsync("Is the bedroom light on?", openAIPromptExecutionSettings, _kernel, stoppingToken);
        Console.WriteLine($"Result to request to light status: {chatResult}");

        _hostApplicationLifetime.StopApplication();
    }
}
