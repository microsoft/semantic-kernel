// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Process.UnitTests.Steps;

/// <summary>
/// A step in the process.
/// </summary>
public sealed class BStep : KernelProcessStep
{
    [KernelFunction]
    public async ValueTask DoItAsync(KernelProcessStepContext context)
    {
        Console.WriteLine("##### BStep ran.");
        await Task.Delay(TimeSpan.FromSeconds(2));
        await context.EmitEventAsync(new() { Id = CommonEvents.BStepDone, Data = "I did B" });
    }
}
