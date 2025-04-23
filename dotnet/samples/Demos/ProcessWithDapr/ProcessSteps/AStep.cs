// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ProcessWithDapr.ProcessSteps;

/// <summary>
/// A step in the process.
/// </summary>
internal sealed class AStep : KernelProcessStep
{
    [KernelFunction]
    public async ValueTask DoItAsync(KernelProcessStepContext context)
    {
        Console.WriteLine("##### AStep ran.");
        await Task.Delay(TimeSpan.FromSeconds(1));
        await context.EmitEventAsync(CommonEvents.AStepDone, "I did A");
    }
}
