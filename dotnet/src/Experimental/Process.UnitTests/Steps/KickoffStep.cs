// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Process.UnitTests.Steps;

/// <summary>
/// Kick off step for the process.
/// </summary>
public sealed class KickoffStep : KernelProcessStep
{
    public static class ProcessFunctions
    {
        public const string KickOff = nameof(KickOff);
    }

    [KernelFunction(ProcessFunctions.KickOff)]
    public async ValueTask PrintWelcomeMessageAsync(KernelProcessStepContext context)
    {
        Console.WriteLine("##### Kickoff ran.");
        await context.EmitEventAsync(new() { Id = CommonEvents.StartARequested, Data = "Get Going" });
    }
}
