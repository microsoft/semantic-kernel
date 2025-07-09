// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Step03.Steps;

/// <summary>
/// Step used in the Processes Samples:
/// - Step_03_FoodPreparation.cs
/// </summary>
public class ExternalStep(string externalEventName) : KernelProcessStep
{
    private readonly string _externalEventName = externalEventName;

    [KernelFunction]
    public async Task EmitExternalEventAsync(KernelProcessStepContext context, object data)
    {
        await context.EmitEventAsync(this._externalEventName, data);
    }
}
