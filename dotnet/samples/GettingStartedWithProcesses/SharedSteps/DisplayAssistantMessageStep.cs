// Copyright (c) Microsoft. All rights reserved.

using Events;
using Microsoft.SemanticKernel;

namespace SharedSteps;

/// <summary>
/// Step used in the Processes Samples:
/// - Step_02_AccountOpening.cs
/// </summary>
public class DisplayAssistantMessageStep : KernelProcessStep
{
    public static class ProcessStepFunctions
    {
        public const string DisplayAssistantMessage = nameof(DisplayAssistantMessage);
    }

    [KernelFunction(ProcessStepFunctions.DisplayAssistantMessage)]
    public async ValueTask DisplayAssistantMessageAsync(KernelProcessStepContext context, string assistantMessage)
    {
        Console.ForegroundColor = ConsoleColor.Blue;
        Console.WriteLine($"ASSISTANT: {assistantMessage}\n");
        Console.ResetColor();

        // Emit the assistantMessageGenerated
        await context.EmitEventAsync(new() { Id = CommonEvents.AssistantResponseGenerated, Data = assistantMessage });
    }
}
