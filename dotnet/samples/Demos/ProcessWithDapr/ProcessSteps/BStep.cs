// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ProcessWithDapr.ProcessSteps;

/// <summary>
/// A step in the process.
/// </summary>
internal sealed class BStep : KernelProcessStep
{
    [KernelFunction]
    public async ValueTask DoItAsync(KernelProcessStepContext context)
    {
        Console.WriteLine("##### BStep ran.");
        await Task.Delay(TimeSpan.FromSeconds(2));
        await context.EmitEventAsync(new() { Id = CommonEvents.BStepDone, Data = "I did B" });
    }
}
