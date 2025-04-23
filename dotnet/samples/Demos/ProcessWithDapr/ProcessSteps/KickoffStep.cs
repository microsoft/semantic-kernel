// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ProcessWithDapr.ProcessSteps;

/// <summary>
/// Kick off step for the process.
/// </summary>
internal sealed class KickoffStep : KernelProcessStep
{
    public static class Functions
    {
        public const string KickOff = nameof(KickOff);
    }

    [KernelFunction(Functions.KickOff)]
    public async ValueTask PrintWelcomeMessageAsync(KernelProcessStepContext context)
    {
        Console.WriteLine("##### Kickoff ran.");
        await context.EmitEventAsync(new() { Id = CommonEvents.StartARequested, Data = "Get Going" });
    }
}
