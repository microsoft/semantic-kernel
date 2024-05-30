// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace HomeAutomation;

/// <summary>
/// Actual code to run.
/// </summary>
internal sealed class Worker(
    IHostApplicationLifetime hostApplicationLifetime,
    [FromKeyedServices("HomeAutomationKernel")] Kernel kernel) : BackgroundService
{
    private readonly IHostApplicationLifetime _hostApplicationLifetime = hostApplicationLifetime;
    private readonly Kernel _kernel = kernel;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        // Get chat completion service
        var chatCompletionService = _kernel.GetRequiredService<IChatCompletionService>();

        // Enable auto function calling
        OpenAIPromptExecutionSettings openAIPromptExecutionSettings = new()
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        };

        Console.WriteLine("Ask questions or give instructions to the copilot such as:\n" +
                          "- What time is it?\n" +
                          "- Turn on the porch light.\n" +
                          "- If it's before 7:00 pm, turn on the office light.\n" +
                          "- Which light is currently on?\n" +
                          "- Set an alarm for 6:00 am.\n");

        Console.Write("> ");

        string? input = null;
        while ((input = Console.ReadLine()) is not null)
        {
            Console.WriteLine();

            ChatMessageContent chatResult = await chatCompletionService.GetChatMessageContentAsync(input,
                    openAIPromptExecutionSettings, _kernel, stoppingToken);

            Console.Write($"\n>>> Result: {chatResult}\n\n> ");
        }

        _hostApplicationLifetime.StopApplication();
    }
}
