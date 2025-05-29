// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Process.UnitTests.Steps;

/// <summary>
/// A step in the process.
/// </summary>
public sealed class AStep : KernelProcessStep
{
    [KernelFunction]
    public async ValueTask DoItAsync(KernelProcessStepContext context)
    {
        Console.WriteLine("##### AStep ran.");
        await Task.Delay(TimeSpan.FromSeconds(1));
        await context.EmitEventAsync(CommonEvents.AStepDone, "I did A");
    }
}
