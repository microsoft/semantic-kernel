// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Step00.Steps;

public sealed class DoMoreWorkStep : KernelProcessStep
{
    [KernelFunction]
    public async ValueTask ExecuteAsync(KernelProcessStepContext context)
    {
        Console.WriteLine("Step 3 - Doing Yet More Work...\n");
    }
}
