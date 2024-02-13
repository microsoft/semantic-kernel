// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel;

namespace HomeAutomation;

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
        // Get chat completion service
        var chatCompletionService = _kernel.GetRequiredService<IChatCompletionService>();

        // Enable auto function calling
        OpenAIPromptExecutionSettings openAIPromptExecutionSettings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        ChatMessageContent chatResult = await chatCompletionService.GetChatMessageContentAsync("What time is it?",
            openAIPromptExecutionSettings, _kernel, stoppingToken);
        Console.WriteLine($">>> Result: {chatResult}");

        chatResult = await chatCompletionService.GetChatMessageContentAsync(
            "If it's before 7:00 pm, turn on the office light.",
            openAIPromptExecutionSettings, _kernel, stoppingToken);
        Console.WriteLine($">>> Result: {chatResult}");

        chatResult = await chatCompletionService.GetChatMessageContentAsync(
            "Otherwise, turn on the porch light.",
            openAIPromptExecutionSettings, _kernel, stoppingToken);
        Console.WriteLine($">>> Result: {chatResult}");

        chatResult = await chatCompletionService.GetChatMessageContentAsync("Which light is currently on?",
            openAIPromptExecutionSettings, _kernel, stoppingToken);
        Console.WriteLine($">>> Result: {chatResult}");

        _hostApplicationLifetime.StopApplication();
    }
}
